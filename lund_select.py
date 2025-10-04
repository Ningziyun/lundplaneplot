#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Read two jagged branches from a ROOT TTree, apply composable operations:

  - shuffle    : per-jet permutation with pair alignment
  - top10      : keep jets with >=10 emissions, then slice [:10]
  - both       : expands to shuffle + top10
  - swap       : swap the two branches' DATA on output (names follow default unless overridden)
  - swapnames  : keep DATA as-is, only swap the OUTPUT NAMES (aliases)

Pipeline order (deterministic when composing):
  shuffle -> top10 -> swap(data) -> swapnames(names)

THEN write them back using **PyROOT** as EXACTLY TWO branches.
By default, the output branch order follows the input order,
unless explicitly overridden with --out_b1 / --out_b2.

Usage examples
--------------
# single ops
python lund_select.py --in rootFiles/log_kt_deltaR.root --out shuffled.root  --mode shuffle --seed 42
python lund_select.py --in rootFiles/log_kt_deltaR.root --out top10.root     --mode top10
python lund_select.py --in rootFiles/log_kt_deltaR.root --out both.root      --mode both --seed 123
python lund_select.py --in rootFiles/log_kt_deltaR.root --out swapped.root   --mode swap
python lund_select.py --in rootFiles/log_kt_deltaR.root --out swappedn.root  --mode swapnames

# compose multiple modes (order is fixed as above)
python lund_select.py --in rootFiles/log_kt_deltaR.root --out shuffled.root  --mode shuffle --seed 42 --mode swap
python lund_select.py --in rootFiles/log_kt_deltaR.root --out top10.root     --mode top10 --mode swap
python lund_select.py --in root.root --out out.root --mode shuffle --mode top10 --mode swapnames
python lund_select.py --in root.root --out out.root --mode both --mode swap

We explicitly create std::vector<float> branches via PyROOT,
so NO auxiliary count/offset branches will appear.
"""

import argparse
from typing import Optional, List

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
    """Randomly permute emissions within each jet while keeping (a1, a2) pairs aligned."""
    rng = np.random.default_rng(seed)
    counts = ak.num(a1)
    keys_flat = rng.random(int(ak.sum(counts)))
    keys = ak.unflatten(keys_flat, counts)
    perm = ak.argsort(keys, axis=1)
    return a1[perm], a2[perm]


def op_top10(a1: ak.Array, a2: ak.Array):
    """Keep only jets with >=10 emissions and slice to the first 10 emissions."""
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
    out_b1: str,
    out_b2: str,
):
    """
    Write EXACTLY TWO branches using PyROOT as std::vector<float>.
    Output branch names are taken from arguments.
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

    # Bind branches
    t.Branch(out_b1, v1)
    t.Branch(out_b2, v2)

    # Convert to list-of-lists for efficiency in Python→C++ loop
    list1 = ak.to_list(a1_32)
    list2 = ak.to_list(a2_32)

    if len(list1) != len(list2):
        raise RuntimeError("Internal error: number of jets mismatch after processing.")

    for x1, x2 in zip(list1, list2):
        v1.clear()
        v2.clear()
        for val in x1:
            v1.push_back(float(val))
        for val in x2:
            v2.push_back(float(val))
        t.Fill()

    fout.Write()
    fout.Close()


# ---------------------------
# CLI
# ---------------------------
def parse_args():
    p = argparse.ArgumentParser(
        description="Compose shuffle/top10/swap/swapnames and write EXACTLY TWO branches via PyROOT."
    )
    p.add_argument("--in", dest="in_path", required=True,
                   help="Input ROOT file (e.g., inputFiles/log_kt_deltaR.root).")
    p.add_argument("--out", dest="out_path", required=True,
                   help="Output ROOT file.")

    # Now repeatable: use --mode multiple times (e.g. --mode shuffle --mode top10)
    p.add_argument("--mode", action="append",
                   choices=["shuffle", "top10", "both", "swap", "swapnames"],
                   required=True,
                   help=("Repeatable. Compose multiple modes. "
                         "'both' expands to shuffle+top10. "
                         "Pipeline order is shuffle -> top10 -> swap -> swapnames."))

    p.add_argument("--tree_name", default="auto",
                   help="TTree name; use 'auto' to detect the first TTree.")

    # Input branch names (what your file actually has)
    p.add_argument("--in_b1", default="log_kt",
                   help="Input first branch name (default: 'log_kt').")
    p.add_argument("--in_b2", default="log_1_over_deltaR",
                   help="Input second branch name (default: 'log_1_over_deltaR').")

    # Output branch names (follow input order by default)
    p.add_argument("--out_b1", default=None,
                   help="Output first branch name (default: same as in_b1; or swapped by swap/swapnames if not overridden).")
    p.add_argument("--out_b2", default=None,
                   help="Output second branch name (default: same as in_b2; or swapped by swap/swapnames if not overridden).")

    p.add_argument("--seed", type=int, default=None,
                   help="Random seed for shuffling (only used if 'shuffle' is selected).")
    return p.parse_args()


def _expand_modes(modes_list: List[str]) -> List[str]:
    """Expand 'both' into ['shuffle','top10'] and deduplicate while preserving pipeline order."""
    selected = set(modes_list)
    if "both" in selected:
        selected.update({"shuffle", "top10"})
    # Pipeline order enforced here
    pipeline = ["shuffle", "top10", "swap", "swapnames"]
    return [m for m in pipeline if m in selected]


def main():
    args = parse_args()

    # Read input branches
    a1, a2, tname = read_branches(args.in_path, args.tree_name, args.in_b1, args.in_b2)

    # Expand & order modes
    modes = _expand_modes(args.mode)

    # --- Apply DATA transforms in fixed pipeline order ---
    a1_out, a2_out = a1, a2
    applied = []

    if "shuffle" in modes:
        a1_out, a2_out = op_shuffle(a1_out, a2_out, seed=args.seed)
        applied.append("shuffle")

    if "top10" in modes:
        a1_out, a2_out = op_top10(a1_out, a2_out)
        applied.append("top10")

    if "swap" in modes:
        a1_out, a2_out = a2_out, a1_out
        applied.append("swap(data)")

    # --- Resolve OUTPUT NAMES ---
    # Defaults follow input order; may be swapped depending on modes and whether user provided names.
    out_b1_default = args.in_b1
    out_b2_default = args.in_b2

    if args.out_b1 is None and args.out_b2 is None:
        # If swapnames is present, it dictates swapping names (even if swap also present).
        # Else if only swap is present, keep names synced with data by swapping names too.
        if "swapnames" in modes:
            out_b1_default, out_b2_default = out_b2_default, out_b1_default
            applied.append("swapnames(names)")
        elif "swap" in modes:
            out_b1_default, out_b2_default = out_b2_default, out_b1_default
            applied.append("names_follow_data")

    out_b1 = args.out_b1 if args.out_b1 is not None else out_b1_default
    out_b2 = args.out_b2 if args.out_b2 is not None else out_b2_default

    # Resolve tree name
    resolved_tree = tname if args.tree_name == "auto" else args.tree_name

    # Write output
    write_with_pyroot(
        args.out_path,
        resolved_tree,
        a1_out,
        a2_out,
        out_b1=out_b1,
        out_b2=out_b2,
    )

    # Report
    n_in = len(a1)
    n_out = len(a1_out)
    print(f"[OK] Modes={args.mode} -> Applied={modes} ({', '.join(applied) if applied else 'none'}).")
    print(f"     Input jets: {n_in} -> Output jets: {n_out}.")
    if "top10" in modes:
        nlen = ak.to_numpy(ak.num(a1_out))
        assert np.all(nlen == 10), "All output jets should have exactly 10 emissions."
        print("[INFO] All kept jets have exactly 10 emissions.")
    print(f"[INFO] Output branches: '{out_b1}' (first), '{out_b2}' (second) in tree '{resolved_tree}'.")


if __name__ == "__main__":
    main()
