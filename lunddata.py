import ROOT
import os
import fastjet
import awkward as ak
import math
import ljpHelpers
import argparse

# -----------------------------
# New helpers (minimal additions)
# -----------------------------
def list_all_ttrees(rfile):
    """Return a list of (path, TTree) for ALL TTrees in the file (recursively)."""
    out = []
    def _walk(dir_or_file, prefix=""):
        keys = dir_or_file.GetListOfKeys()
        if not keys: return
        for k in keys:
            obj = k.ReadObj()
            name = obj.GetName()
            if isinstance(obj, ROOT.TTree):
                out.append((prefix + name, obj))
            elif isinstance(obj, ROOT.TDirectory):
                _walk(obj, prefix + name + "/")
    _walk(rfile, "")
    return out

def autodetect_constit_names(tree):
    """
    Auto-detect three array-like branches for constituents.
    Default mapping by order: [0] -> pt, [1] -> eta, [2] -> phi.
    Strategy (kept minimal):
      1) Prefer names starting with 'constit_' (e.g. constit_pt/eta/phi).
      2) Else prefer names like var1/var2/var3.
      3) Else take the first three branches that look like per-event sequences.
    """
    # Collect all branch names
    blist = tree.GetListOfBranches()
    names = [blist.At(i).GetName() for i in range(blist.GetEntries())]

    # 1) constit_* first
    constit_like = [n for n in names if n.lower().startswith("constit_")]
    if len(constit_like) >= 3:
        return constit_like[0], constit_like[1], constit_like[2]

    # 2) var1/var2/var3
    var_like = [n for n in names if n.lower().startswith("var")]
    # stable order
    var_like = sorted(var_like, key=lambda s: s.lower())
    if len(var_like) >= 3:
        return var_like[0], var_like[1], var_like[2]

    # 3) first three sequence-like branches by peeking the first few events
    seq_candidates = []
    # peek up to ~200 events to find any event with non-empty sequences
    it = tree.__iter__()
    for _ in range(200):
        try:
            ev = next(it)
        except StopIteration:
            break
        tmp = []
        for n in names:
            if hasattr(ev, n):
                vals = getattr(ev, n)
                try:
                    # treat as sequence if len() works and length > 0
                    if len(vals) > 0:
                        tmp.append(n)
                except Exception:
                    pass
            if len(tmp) >= 3:
                seq_candidates = tmp[:3]
                break
        if len(seq_candidates) >= 3:
            break

    if len(seq_candidates) >= 3:
        return seq_candidates[0], seq_candidates[1], seq_candidates[2]

    # Fallback (won't be ideal, but keeps script running)
    return names[0], names[1], names[2]


def loopFile(m_filename, tree, outdir = "lundfiles", nImages = 30, minDr = 0.0, maxDr = 10.0, minKt = -1, maxKt = 8, minZ = 0.5, maxZ = 6.5, nBinsKt = 25, nBinsDr = 25, nBinsZ = 40):
   # Set branch addresses and branch pointers
   if (not tree):
     return;
     
   if not os.path.exists(outdir):
     os.makedirs(outdir)

   # Output TTree and variables
   newfile = ROOT.TFile.Open(("%s/%s"%(outdir, m_filename)), "RECREATE");
   lundTree = ROOT.TTree("lundTree", "Jet declustering kt and deltaR")
   kt_vec = ROOT.std.vector('float')()
   deltaR_vec = ROOT.std.vector('float')()
   lundTree.Branch("kt", kt_vec)
   lundTree.Branch("deltaR", deltaR_vec)

   # --- NEW: autodetect constituent branch names (pt, eta, phi by order) ---
   pt_name, eta_name, phi_name = autodetect_constit_names(tree)
   print(f"[info] branches detected: pt={pt_name}, eta={eta_name}, phi={phi_name}")

   njet = 0;
   jentry=0;

   for index, event in enumerate(tree):
     jentry+=1

     # --- CHANGED: read by detected names instead of hardcoded constit_* ---
     constit_pt  = getattr(event, pt_name,  None)
     constit_eta = getattr(event, eta_name, None)
     constit_phi = getattr(event, phi_name, None)
     if constit_pt is None or constit_eta is None or constit_phi is None:
         continue

     jetR10 = 1.0;
     jetDef10 = fastjet.JetDefinition(fastjet.antikt_algorithm, jetR10, fastjet.E_scheme);

     for cjet in range(len(constit_pt)):
       njet+=1;
       constituents = [];

       # Convert constituents to PseudoJets
       for j in range(len((constit_pt))):
         constitTLV = ROOT.TLorentzVector(0,0,0,0);
         constitTLV.SetPtEtaPhiM((constit_pt)[j], (constit_eta)[j], (constit_phi)[j],0);
         constitPJ = fastjet.PseudoJet(constitTLV.Px(), constitTLV.Py(), constitTLV.Pz(), constitTLV.E());
         constituents.append(constitPJ);
         
     # Anti-kT
     clustSeq4 = fastjet.ClusterSequence(constituents, jetDef10);
     inclusiveJets10 = fastjet.sorted_by_pt(clustSeq4.inclusive_jets(25.));
     if not inclusiveJets10:
       continue

     # C/A recluster (kept exactly as original)
     allConstits = list(inclusiveJets10[0].constituents())
     cs_ca = fastjet.ClusterSequence(allConstits, fastjet.JetDefinition1Param(fastjet.cambridge_algorithm, 10.0));
     myJet_ca = fastjet.sorted_by_pt(cs_ca.inclusive_jets(1.0));

     # Decluster using existing helper (unchanged)
     lundPlane = ljpHelpers.jet_declusterings(inclusiveJets10[0]);

     for k in range(len(lundPlane)):
       if(lundPlane[k].delta_R > 0 and lundPlane[k].z > 0):       
         deltaR_vec.push_back(lundPlane[k].delta_R)
         kt_vec.push_back(lundPlane[k].kt)

     if len(kt_vec) > 0:
        lundTree.Fill()
        kt_vec.clear()
        deltaR_vec.clear()

   newfile.cd()
   lundTree.Write()
   newfile.Close();


# -----------------------------
# CLI (minimal changes)
# -----------------------------
parser = argparse.ArgumentParser(description='Process benchmarks.')
parser.add_argument("--filename", help="", default="fileList.txt")
parser.add_argument("--treename", help="TTree name, or 'auto' to loop over all trees", default="tree")
opt = parser.parse_args()

if not os.path.exists("rootFiles"):
    os.makedirs("rootFiles")

with open(opt.filename) as infile:
  for line in infile:
    if( line.strip()=='' or line[0] == '#'):
      continue;
    line = line.rstrip('\n')

    try:
      rfile = ROOT.TFile(line);
      if not rfile or rfile.IsZombie():
          print("Did not find file or file is zombie, continue")
          continue
    except:
      print("Did not find either file or tree, continuing to the next")
      continue

    # --- NEW: auto loop over ALL TTrees if treename=='auto' ---
    trees = []
    if opt.treename.lower() == "auto":
        trees = list_all_ttrees(rfile)
        if not trees:
            print("[warn] no TTrees found, skip file")
            rfile.Close()
            continue
    else:
        t = rfile.Get(opt.treename)
        if isinstance(t, ROOT.TTree):
            trees = [(opt.treename, t)]
        else:
            print("Did not find tree, continuing to the next")
            rfile.Close()
            continue

    # Process every tree discovered
    for tpath, tree in trees:
        if not tree: 
            continue
        m_filename = "hists" + line
        # Remove directories from filename
        while(m_filename.find("/") >=0):
          m_filename = m_filename[m_filename.find("/")+1:];
        # Add tree path to make outputs unique if multiple trees
        safe_tpath = tpath.replace("/", "_")
        m_filename_with_tree = f"{safe_tpath}_{m_filename}"
        print(f"[info] processing tree: {tpath}")
        loopFile(m_filename_with_tree, tree);

    rfile.Close()
