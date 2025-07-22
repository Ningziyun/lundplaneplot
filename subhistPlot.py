#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 11 16:29:53 2025

@author: ningyan
"""
import uproot
import argparse
import numpy as np
import matplotlib.pyplot as plt
import os

parser = argparse.ArgumentParser(description='Process benchmarks.')
parser.add_argument("--filename", help="", default="subhistList.txt")
parser.add_argument("--treename", help="", default="tree")
opt = parser.parse_args()

constit = ["constit_pt", "constit_eta", "constit_phi"]

# 输出目录：plots/extra
output_dir = "plots/extra"
os.makedirs(output_dir, exist_ok=True)

with open(opt.filename) as f:
    file_list = [line.strip() for line in f if line.strip() and not line.startswith("#")]

for const in constit:
    if const == "constit_pt":
        for line in file_list:
            file = uproot.open(line)
            print(line)
            const_value = np.array([])
            for key in file.keys():
                array = file[key][const].array(library="np")
                
                const_value=np.append(const_value,array)
        
            const_value = np.concatenate(const_value)

            const_value_nz = const_value[const_value > 50]
            # 绘制频数（不是 density）
            counts, bin_edges = np.histogram(const_value_nz, bins=100, density=True)
            bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

            plt.plot(bin_centers, counts, drawstyle="steps-mid", label=os.path.splitext(os.path.basename(line))[0])

        plt.xlabel(const)
        plt.ylabel("Normalized log-scale frequency")
        plt.title(const+"_logscale")
        plt.legend(loc="upper right")
        plt.yscale("log")  # 关键：y轴 log 变换
        # 保存为 PDF 到 plots/extra/
        save_path = os.path.join(output_dir, f"{const}_logscale.pdf")
        plt.savefig(save_path)
        plt.close()  # 关闭图像避免显示

for const in constit:
    for line in file_list:
        file = uproot.open(line)
        print(line)
        const_value = np.array([])
        for key in file.keys():
            array = file[key][const].array(library="np")

            const_value = np.append(const_value,array)
        
        const_value = np.concatenate(const_value)
        if const == "constit_pt":
            const_value = const_value[const_value > 50]
        
        counts, bin_edges = np.histogram(const_value, bins=100, density=True)
        bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
        plt.plot(bin_centers, counts, drawstyle="steps-mid",label=os.path.splitext(os.path.basename(line))[0])
        plt.legend(line)

    plt.xlabel(const)
    plt.ylabel("Probability Density")
    plt.title(const)
    plt.legend(loc="upper right")
    # 保存为 PDF 到 plots/extra/
    save_path = os.path.join(output_dir, f"{const}.pdf")
    plt.savefig(save_path)
    plt.close()  # 关闭图像避免显示
