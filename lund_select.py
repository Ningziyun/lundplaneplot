#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Read two jagged branches from a ROOT TTree, apply:
  - shuffle  : per-jet permutation with pair alignment
  - top10    : keep jets with >=10 emissions, then slice [:10]
  - both     : shuffle then top10

THEN write them back using **PyROOT** as EXACTLY TWO branches:
  - log_kt
  - log_1_over_deltaR

Usage examples -------------- 
python lund_select.py --in rootFiles/log_kt_deltaR.root --out shuffled.root --mode shuffle 
python lund_select.py --in rootFiles/log_kt_deltaR.root --out top10.root --mode top10 
python lund_select.py --in rootFiles/log_kt_deltaR.root --out both.root --mode both --seed 123

We explicitly create std::vector<float> branches via PyROOT,
so NO auxiliary count/offset branches will appear.
"""

import argparse
from typing import Optional

import numpy as np
import awkward as ak
import uproot

# Import PyROOT only for writing
import ROOT


# ---------------------------
# I/O helpers
# ---------------------------
def autodetect_tree_name(root_path: str) -> str:
    """Return the name of the first TTree in the ROOT file."""
    with uproot.open(root_path) as f:
        for key in f.keys():  # e.g. "myTree;1"
            try:
                obj = f[key]
                if getattr(obj, "classname", "") == "TTree":
                    return key.split(";")[0]
            except Exception:
                continue
    raise ValueError("No TTree found in the input ROOT file.")


def read_branches(root_path: str, tree_name: str, in_b1: str, in_b2: str):
    """
    Read two jagged branches as Awkward arrays and ensure per-entry length match.
    Return (a1, a2, resolved_tree_name).
    """
    with uproot.open(root_path) as f:
        if tree_name.lower() == "auto":
            tree_name = autodetect_tree_name(root_path)
        tree = f[tree_name]
        arrs = tree.arrays([in_b1, in_b2], library="ak")
    a1 = arrs[in_b1]
    a2 = arrs[in_b2]
    if ak.any(ak.num(a1) != ak.num(a2)):
        raise ValueError("Per-entry lengths of the two branches do not match.")
    return a1, a2, tree_name


# ---------------------------
# Core ops
# ---------------------------
def op_shuffle(a1: ak.Array, a2: ak.Array, seed: Optional[int] = None):
    """
    Randomly permute emissions WITHIN each jet using the SAME permutation
    for both arrays so that pairs (a1[i], a2[i]) remain aligned.

    Implementation:
      - Generate a random key per emission (flat)
      - Unflatten keys to jagged by counts
      - argsort(keys, axis=1) => per-jet permutation indices
      - Apply the same permutation to both arrays
    """
    rng = np.random.default_rng(seed)
    counts = ak.num(a1)
    keys_flat = rng.random(int(ak.sum(counts)))
    keys = ak.unflatten(keys_flat, counts)
    perm = ak.argsort(keys, axis=1)
    return a1[perm], a2[perm]


def op_top10(a1: ak.Array, a2: ak.Array):
    """
    Keep only jets with >=10 emissions and slice to the first 10 emissions.
    """
    n = ak.num(a1)
    mask = n >= 10
    return a1[mask][:, :10], a2[mask][:, :10]


# ---------------------------
# PyROOT writer (exact two branches)
# ---------------------------
def write_with_pyroot(
    out_path: str,
    tree_name: str,
    a1: ak.Array,
    a2: ak.Array,
    out_b1: str = "log_kt",
    out_b2: str = "log_1_over_deltaR",
):
    """
    Write EXACTLY TWO branches using PyROOT as std::vector<float>:
      - out_b1
      - out_b2

    Notes:
      * We loop over jets; for each jet, we fill vector<float> with emissions.
      * Awkward arrays are converted to Python lists per entry for simplicity.
    """
    # Ensure dtype float32 for compactness and consistency
    a1_32 = ak.values_astype(a1, np.float32)
    a2_32 = ak.values_astype(a2, np.float32)

    # Create output file and tree
    fout = ROOT.TFile(out_path, "RECREATE")
    t = ROOT.TTree(tree_name, tree_name)

    # Create std::vector<float> buffers
    v1 = ROOT.std.vector('float')()
    v2 = ROOT.std.vector('float')()

    # Bind branches (address must remain valid during Fill)
    t.Branch(out_b1, v1)
    t.Branch(out_b2, v2)

    # Iterate over entries (jets)
    # Convert to list-of-lists to avoid awkward-to-C++ overhead in the loop
    list1 = ak.to_list(a1_32)
    list2 = ak.to_list(a2_32)

    if len(list1) != len(list2):
        raise RuntimeError("Internal error: number of jets mismatch after processing.")

    for x1, x2 in zip(list1, list2):
        # Clear vectors
        v1.clear()
        v2.clear()
        # Fill vectors
        # (x1, x2) are Python lists of floats for this jet (variable length)
        for val in x1:
            v1.push_back(float(val))
        for val in x2:
            v2.push_back(float(val))
        # Fill one entry
        t.Fill()

    # Write and close
    fout.Write()
    fout.Close()


# ---------------------------
# CLI
# ---------------------------
def parse_args():
    p = argparse.ArgumentParser(
        description="Shuffle/truncate two jagged branches and write EXACTLY TWO branches using PyROOT."
    )
    p.add_argument("--in", dest="in_path", required=True,
                   help="Input ROOT file (e.g., inputFiles/log_kt_deltaR.root).")
    p.add_argument("--out", dest="out_path", required=True,
                   help="Output ROOT file.")
    p.add_argument("--mode", choices=["shuffle", "top10", "both"], required=True,
                   help="Operation to perform.")
    p.add_argument("--tree_name", default="auto",
                   help="TTree name; use 'auto' to detect the first TTree.")

    # Input branch names (what your file actually has)
    p.add_argument("--in_b1", default="log_kt",
                   help="Input first branch name (default: 'log_kt').")
    p.add_argument("--in_b2", default="log_1_over_deltaR",
                   help="Input second branch name (default: 'log_1_over_deltaR').")

    # Output branch names (what you want in the new file)
    # Defaults enforce the exact two names you asked for:
    p.add_argument("--out_b1", default="log_kt",
                   help="Output first branch name (default: 'log_kt').")
    p.add_argument("--out_b2", default="log_1_over_deltaR",
                   help="Output second branch name (default: 'log_1_over_deltaR').")

    p.add_argument("--seed", type=int, default=None,
                   help="Random seed for shuffling (for reproducibility).")
    return p.parse_args()


def main():
    args = parse_args()

    # Read
    a1, a2, tname = read_branches(args.in_path, args.tree_name, args.in_b1, args.in_b2)

    # Apply operations
    if args.mode == "shuffle":
        a1_out, a2_out = op_shuffle(a1, a2, seed=args.seed)
    elif args.mode == "top10":
        a1_out, a2_out = op_top10(a1, a2)
    else:  # both
        a1_tmp, a2_tmp = op_shuffle(a1, a2, seed=args.seed)
        a1_out, a2_out = op_top10(a1_tmp, a2_tmp)

    # Resolve output tree name
    resolved_tree = tname if args.tree_name == "auto" else args.tree_name

    # WRITE with PyROOT: exactly two branches (no n<name> auxiliaries)
    write_with_pyroot(
        args.out_path,
        resolved_tree,
        a1_out,
        a2_out,
        out_b1=args.out_b1,
        out_b2=args.out_b2,
    )

    # Report
    n_in = len(a1)
    n_out = len(a1_out)
    print(f"[OK] Mode={args.mode}. Input jets: {n_in} -> Output jets: {n_out}.")
    if args.mode in ("top10", "both"):
        nlen = ak.to_numpy(ak.num(a1_out))
        assert np.all(nlen == 10), "All output jets should have exactly 10 emissions."
        print("[INFO] All kept jets have exactly 10 emissions.")


if __name__ == "__main__":
    main()
