#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 28 11:21:53 2025

@author: ningyan
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ROOT
import sys
import os

def rename_keys(infile, outfile, new_names):
    """
    Rename the first three keys in a ROOT file.
    infile:  输入 ROOT 文件路径
    outfile: 输出 ROOT 文件路径
    new_names: list of new names, e.g. ["constit_pt", "constit_eta", "constit_phi"]
    """

    # 打开输入文件
    fin = ROOT.TFile.Open(infile, "READ")
    if not fin or fin.IsZombie():
        raise RuntimeError(f"Cannot open input file: {infile}")

    # 创建输出文件
    fout = ROOT.TFile.Open(outfile, "RECREATE")

    # 获取 keys
    keys = fin.GetListOfKeys()
    if keys.GetSize() < len(new_names):
        raise RuntimeError(f"Input file has fewer than {len(new_names)} keys!")

    # 遍历前三个 key，复制并改名
    for i, new_name in enumerate(new_names):
        old_key = keys.At(i)
        obj = old_key.ReadObj()
        obj.SetName(new_name)   # 修改对象名字
        fout.cd()
        obj.Write()             # 写入新文件

    # 如果想保留其余 key，也可以复制过去
    for i in range(len(new_names), keys.GetSize()):
        old_key = keys.At(i)
        obj = old_key.ReadObj()
        fout.cd()
        obj.Write()

    fout.Close()
    fin.Close()
    print(f"[Done] Saved new file: {outfile}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rename_keys.py input.root [output.root]")
        sys.exit(1)

    infile = sys.argv[1]
    outfile = sys.argv[2] if len(sys.argv) > 2 else "renamed.root"
    new_names = ["constit_pt", "constit_eta", "constit_phi"]

    rename_keys(infile, outfile, new_names)
