#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 27 17:57:06 2025

@author: ningyan
"""

import os, numpy as np, uproot, awkward as ak
import ROOT

# -------- paths --------
inpath  = "/Users/ningyan/Desktop/Brown/Roloff/Code/rootFiles/qcd_lund.root"
outpath = "/Users/ningyan/Desktop/Brown/Roloff/Code/rootFiles/log_kt_deltaR.root"
treename_try = "lundTree"  # 读时可用 'lundTree' 或 'lundTree;1'

# -------- read (uproot) --------
with uproot.open(inpath) as f:
    T = f[treename_try] if treename_try in f else f["lundTree;1"]
    kt = T["kt"].array(library="ak")         # jagged: 事件 -> 向量
    dR = T["deltaR"].array(library="ak")

# 数值安全（避免 log 对 0/负数、NaN/Inf）
eps = 1e-12
safe_kt = ak.where(kt > 0, kt, np.nan)
safe_dR = ak.where(dR > 0, dR, eps)

lconkt  = np.log(safe_kt)          # Log[kt]
lcondR  = np.log(1.0 / safe_dR)    # Log[1/deltaR]

# -------- per-event filter, keep ragged form --------
keepkt, keepdR = [], []
for dr_list, kt_list in zip(ak.to_list(lcondR), ak.to_list(lconkt)):
    m = min(len(dr_list), len(kt_list))      # 长度不等时截齐
    out_dr, out_kt = [], []
    for j in range(m):
        drv, ktv = dr_list[j], kt_list[j]
        if np.isfinite(drv) and np.isfinite(ktv) and (drv < 10) and (ktv > -1):
            out_dr.append(float(drv))
            out_kt.append(float(ktv))
    keepdR.append(out_dr)
    keepkt.append(out_kt)

# -------- write (PyROOT): ONLY TWO BRANCHES --------
os.makedirs(os.path.dirname(outpath), exist_ok=True)
fout  = ROOT.TFile(outpath, "RECREATE")
tree  = ROOT.TTree("lundTree", "lundTree")

v_dr  = ROOT.std.vector('float')()
v_kt  = ROOT.std.vector('float')()
tree.Branch("log_1_over_deltaR", v_dr)   # 分支1
tree.Branch("log_kt",            v_kt)   # 分支2

for dr_list, kt_list in zip(keepdR, keepkt):
    v_dr.clear(); v_kt.clear()
    for x in dr_list: v_dr.push_back(x)
    for y in kt_list: v_kt.push_back(y)
    tree.Fill()

tree.Write()
fout.Close()

# -------- sanity check --------
fchk = ROOT.TFile.Open(outpath, "READ")
tchk = fchk.Get("lundTree")
branches = [b.GetName() for b in tchk.GetListOfBranches()]
keys = [k.GetName() for k in fchk.GetListOfKeys()]
print("[TOP-LEVEL KEYS ]:", keys)           # 只应有 ['lundTree;1']
print("[TREE BRANCHES   ]:", branches)      # 只应有 ['log_1_over_deltaR','log_kt']
assert set(branches) == {"log_1_over_deltaR", "log_kt"}
fchk.Close()
