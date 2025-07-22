import ROOT
import fastjet
import math
import ljpHelpers
import os
import uproot

'''
file = uproot.open("rootFiles/transformerJets.root")
tree = file["tree"]

pt = tree["constit_pt"].array(library="np")
eta = tree["constit_eta"].array(library="np")
phi = tree["constit_phi"].array(library="np")
e = tree["constit_e"].array(library="np")

# 每个 pt 是一个 object array，自己检查 shape 是否是 (events, constituents)
print(pt.shape)
'''



def loopFile(m_filename, tree, outdir = "histfiles", nImages = 30, minDr = 0.0, maxDr = 10.0, minKt = -1, maxKt = 8, minZ = 0.5, maxZ = 6.5, nBinsKt = 25, nBinsDr = 25, nBinsZ = 40):
   # Set branch addresses and branch pointers
   if (not tree):
     return;

   # The output file with the histograms
   newfile = ROOT.TFile.Open(("%s/%s"%(outdir, m_filename)), "RECREATE");
   """
   # A variety of output histograms (defined here, filled later)
   h_lundPlane = ROOT.TH2F("lundPlane", ";ln(R/#Delta R); ln(1/z)", nBinsDr, minDr, maxDr, nBinsZ, minZ, maxZ);
   h_lundPlaneKt = ROOT.TH2F("lundPlaneKt", ";ln(R/#Delta R); ln(#it{k_{t}}/GeV)", nBinsDr, minDr, maxDr, nBinsKt, minKt, maxKt);
   h_jetPt = ROOT.TH1F("jetPt", ";p_{T} [GeV]", 500, 0, 5000);
   """
   # A variety of output histograms (defined here, filled later)
   h_lundPlane = ROOT.TH2F("lundPlane", ";ln(R/#Delta R); ln(1/z)", nBinsDr, minDr, maxDr, nBinsZ, minZ, maxZ);
   h_lundPlaneKt = ROOT.TH2F("lundPlaneKt", ";ln(R/#Delta R); ln(#it{k_{t}}/GeV)", nBinsDr, minDr, maxDr, nBinsKt, minKt, maxKt);
   h_jetPt = ROOT.TH1F("jetPt", ";p_{T} [GeV]", 500, 0, 1000);
   h_jetM = ROOT.TH1F("jetM", ";p_{T} [GeV]", 300, 0, 300);
   h_jetEta = ROOT.TH1F("jetEta", ";p_{T} [GeV]", 500, -5, 5);
   h_jetPhi = ROOT.TH1F("jetPhi", ";p_{T} [GeV]", 500, -3.14, 3.14);
   h_constitPt = ROOT.TH1F("constitPt", ";p_{T} [GeV]", 500, 0, 5000);
   h_constitEta = ROOT.TH1F("constitEta", ";p_{T} [GeV]", 500, -5, 5);
   h_constitPhi = ROOT.TH1F("constitPhi", ";p_{T} [GeV]", 500, -3.14, 3.14);


   # LJP images for a single event (to be filled later)
   lundPlaneImages = [];
   for i in range(nImages):
     h_lundPlaneImage = ROOT.TH2F("lundPlaneImage_%d"%i, ";ln(R/#Delta R); ln(1/z)", nBinsDr, minDr, maxDr, nBinsZ, minZ, maxZ);
     lundPlaneImages.append(h_lundPlaneImage);
     h_lundPlaneImageKt = ROOT.TH2F(("lundPlaneImageKt_%d"%i), ";ln(R/#Delta R); ln(kt)",nBinsDr, minDr, maxDr, nBinsKt, minKt, maxKt);

   # Index for how many jets have been analyzed
   njet = 0;
   # Index for the event number
   jentry=0;

   # Loop through all events in the input file to read information about the jets and constituents,
   # and use this to fill histograms with this data
   for event in tree:
     jentry+=1

     # Read the kinematic information about the jets from the tree
     '''
     jet_pt = event.jet_pt;
     jet_eta = event.jet_eta;
     jet_phi = event.jet_phi;
     jet_e = event.jet_e
     '''

     # Read the kinematic information about the jet constituents from the tree
     constit_pt = event.constit_pt
     constit_eta = event.constit_eta
     constit_phi = event.constit_phi
     constit_e = event.constit_e
     '''
     constit_pt = pt
     constit_eta = eta
     constit_phi = phi
     constit_e = e
     '''





     jetR10 = 1.0;
     jetDef10 = fastjet.JetDefinition(fastjet.antikt_algorithm, jetR10, fastjet.E_scheme);

     for cjet in range(len(constit_pt)):
       njet+=1;
       constituents = [];
      
       """
       # Convert the constituent information into a format that we can use for fastjet (i.e. Pseudojets)
       for j in range(len((constit_pt)[cjet])):
         constitTLV = ROOT.TLorentzVector(0,0,0,0);
         constitTLV.SetPtEtaPhiE((constit_pt)[cjet][j], (constit_eta)[cjet][j], (constit_phi)[cjet][j],(constit_e)[cjet][j]);
         constitPJ = fastjet.PseudoJet(constitTLV.Px(), constitTLV.Py(), constitTLV.Pz(), constitTLV.E());
         constituents.append(constitPJ);
       """
       # Convert the constituent information into a format that we can use for fastjet (i.e. Pseudojets)
       for j in range(len((constit_pt))):
         h_constitPt.Fill(constit_pt[j]);
         h_constitEta.Fill(constit_eta[j]);
         h_constitPhi.Fill(constit_phi[j]);
         constitTLV = ROOT.TLorentzVector(0,0,0,0);
         constitTLV.SetPtEtaPhiM((constit_pt)[j], (constit_eta)[j], (constit_phi)[j],0);
         constitPJ = fastjet.PseudoJet(constitTLV.Px(), constitTLV.Py(), constitTLV.Pz(), constitTLV.E());
         constituents.append(constitPJ);



       # Run the jet clustering on the jet constituents, using the antikt algorithm
       clustSeq4 = fastjet.ClusterSequence(constituents, jetDef10);
       inclusiveJets10 = fastjet.sorted_by_pt(clustSeq4.inclusive_jets(25.));

       # Save a histogram with the jet pT. This is useful for debugging our input files.
       ''' adding if statement here'''
       if not inclusiveJets10:
           continue
           
       h_jetPt.Fill(inclusiveJets10[0].pt());

       # Recluster the jets using the Cambridge-Aachen algorithm
       '''
       cs_ca = fastjet.ClusterSequence(inclusiveJets10[0].constituents(), fastjet.JetDefinition1Param(fastjet.cambridge_algorithm, 10.0));
       '''
       constituents_list = [inclusiveJets10[0].constituents()[i] for i in range(len(inclusiveJets10[0].constituents()))]


       cs_ca = fastjet.ClusterSequence(constituents_list, fastjet.JetDefinition(fastjet.cambridge_algorithm, 10.0))

       myJet_ca = fastjet.sorted_by_pt(cs_ca.inclusive_jets(1.0));

       lundPlane = ljpHelpers.jet_declusterings(inclusiveJets10[0]);
       
       for k in range(len(lundPlane)):
         # Fill the LJP with the declustered information
         '''
         if(lundPlane[k].delta_R >= 0 and lundPlane[k].z >= 0):
         '''
         if(lundPlane[k].delta_R > 0 and lundPlane[k].z > 0):
           h_lundPlane.Fill(math.log(1./lundPlane[k].delta_R), math.log(1./lundPlane[k].z));         
           h_lundPlaneKt.Fill(math.log(1./lundPlane[k].delta_R), math.log(lundPlane[k].kt));         
         
         # Draw LJP for individual events
         # These take up a lot of space, so we are only writing a fixed number of them 
         if(jentry < nImages and cjet ==0):
           lundPlaneImages[jentry].Fill(math.log(1./lundPlane[k].delta_R), math.log(1./lundPlane[k].z));
     break

   # Normalize by the number of jets that have been used
   if njet > 0:
     h_lundPlane.Scale(1./njet);
     h_lundPlaneKt.Scale(1./njet);
     '''New Adding'''
     h_jetPt.Scale(1. / h_jetPt.Integral())  # ← 加上这句归一化 jetPt

   # Write the histograms to the output file
   newfile.cd()
   h_lundPlane.Write();
   h_lundPlaneKt.Write();
   h_jetPt.Write();

   for i in range(nImages):
     lundPlaneImages[i].Write();
   newfile.Close();


import argparse
parser = argparse.ArgumentParser(description='Process benchmarks.')
parser.add_argument("--filename", help="", default="fileList.txt")
parser.add_argument("--treename", help="", default="tree")

opt = parser.parse_args()


if not os.path.exists("rootFiles"):
    os.makedirs("rootFiles")

with open(opt.filename) as infile:
  for line in infile:

    # Parsing the information from the files
    if( line[0] == '#'):
      continue;
    line = line.rstrip('\n')

    tree = ROOT.TTree();

    try:
      file = ROOT.TFile(line);
      tree = file.Get(opt.treename);
    except:
      file = None
      print("Did not find either file or tree, continuing to the next")
      continue

    if(not tree):
      continue;

    m_filename = "hists" + line;
    # Remove directory name from the new file name
    while(m_filename.find("/") >=0):
      m_filename = m_filename[m_filename.find("/")+1:];
      print(m_filename)

    loopFile(m_filename, tree);
    file.Close();