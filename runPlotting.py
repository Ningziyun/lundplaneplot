import ROOT
import plotStyle as AS
import math
import os
import plotHelper as plotHelper



ROOT.gROOT.SetBatch(1);

import argparse
parser = argparse.ArgumentParser(description='Process benchmarks.')
parser.add_argument("--filename", help="", default="histFileNames.txt")
opt = parser.parse_args()


filename = opt.filename
if not os.path.exists("plots"):
    os.makedirs("plots")
if not os.path.exists("plots/ljpRatios"):
    os.makedirs("plots/ljpRatios")
if not os.path.exists("plots/extra"):
    os.makedirs("plots/extra")


rangeXLow  = 0;
rangeXHigh = 7;
rangeYLow = -1;
rangeYHigh = 8;



mcFiles = []
outNames = []
descriptions = [] 

with open(filename, 'r') as file:
 for line in file:
  words = line.split()
  mcFile = words[0]
  outName = words[1]
  description = words[2]

  # Hardcoding so that we can comment out lines
  if( mcFile[0] == '#'):
    continue;


  pos = mcFile.find(".root");
  mcFiles.append(mcFile);
  outNames.append(outName);

  while(description.find("*") >=0):
    description = description.replace("*", " ");

  descriptions.append(description);


canvas = ROOT.TCanvas("Canvas_%s"%(mcFile),"",800,600);
AS.SetAtlasStyle();
NRGBs = 11;
NCont = 99;
ROOT.gStyle.SetNumberContours(NCont);

canvas.SetRightMargin(0.18);
canvas.SetLeftMargin(0.15);
canvas.SetTopMargin(0.1);
canvas.SetBottomMargin(0.15);

for i in range(len(mcFiles)):
  file = ROOT.TFile(mcFiles[i]);
  print(mcFiles[i])
  '''
  lundPlane1 = file.Get("lundPlane");
  lundPlane1.GetZaxis().SetRangeUser(0.0, 0.128);
  '''
  lundPlane1 = file.Get("lundPlane")
  if not lundPlane1 or not lundPlane1.InheritsFrom("TH2"):
      print(f"WARNING: Could not load valid TH2 histogram 'lundPlane' from file {mcFiles[i]}")
      continue
  lundPlane1.GetZaxis().SetRangeUser(0.0, 0.128)


  lundPlane1.Draw("COLZ");
  ROOT.gStyle.SetTextSize(0.04);
  Y = 0.92;

  AS.myText( 0.15, Y, 1, "Primary LJP, %s"%(outNames[i]));
  canvas.SaveAs("plots/%s.pdf"%(outNames[i]));

  file.Close();

for i in range(len(mcFiles)):

  file = ROOT.TFile(mcFiles[i]);
  lundPlane1 = file.Get("lundPlaneKt");
  plotHelper.configureHist2D(lundPlane1)
  lundPlane1.GetZaxis().SetRangeUser(0.0, 0.128);
  lundPlane1.GetXaxis().SetRangeUser(rangeXLow, rangeXHigh);
  lundPlane1.GetYaxis().SetRangeUser(rangeYLow, rangeYHigh);
  lundPlane1.GetZaxis().SetTitle("#rho(#Delta, #it{k_{t}})");
  lundPlane1.GetYaxis().SetTitle("ln(#it{k_{t}} / GeV)");
  lundPlane1.Draw("COLZ");

   
  try:
    ROOT.gStyle.SetTextSize(0.04);
    Y = 0.92;
    AS.myText( 0.40, 0.84, 1, "Primary LJP", 0.053);
    AS.myText( 0.40, 0.78, 1, descriptions[i], 0.053);
    canvas.SaveAs("plots/Kt_%s.pdf"%(outNames[i]));
    file.Close();

  except:
    print("could not write this one")
    file.Close();



for i in range(len(mcFiles)):
  file = ROOT.TFile(mcFiles[i]);

  lundPlane1 = file.Get("lundPlane");
  lundPlaneKt1 = file.Get("lundPlaneKt");

  for j in range(lundPlane1.GetNbinsX()+1):
    lundPlane1.SetBinContent(0,j,0);
    lundPlane1.SetBinContent(j,0, 0);

  for j in range(len(mcFiles)):
    if(i==j):
      continue;

    # Only want to draw the ratios for relevant matches
    # This is a bit hacked, but it doesn't seem useful to really optimize this yet.
    mcFile2 = mcFiles[j];
    file2 = ROOT.TFile(mcFile2);

    lundPlane2 = file2.Get("lundPlane");

    for k in range(lundPlane2.GetNbinsX()+1):
      lundPlane2.SetBinContent(0,k,0);
      lundPlane2.SetBinContent(k,0, 0);

    lundPlaneKt2 = file2.Get("lundPlaneKt");
    secLundPlane2 = file2.Get("secLundPlane");
    fullLundPlane2 = file2.Get("fullLundPlane");

    lundPlane1.Divide(lundPlane2);
    lundPlane1.GetZaxis().SetRangeUser(0.0, 2.0);
    lundPlane1.Draw("COLZ");

    ROOT.gStyle.SetTextSize(0.04);
    Y = 0.92;
    AS.myText( 0.15, Y, 1, "Primary LJP, %s / %s"%(outNames[i], outNames[j]));
    canvas.SaveAs("plots/ljpRatios/%s_%s.pdf"%(outNames[i], outNames[j]));

    lundPlane1.Multiply(lundPlane2);
    lundPlaneKt1.Divide(lundPlaneKt2);
    plotHelper.configureHist2D(lundPlaneKt1)
    lundPlaneKt1.GetZaxis().SetRangeUser(0.0, 2.0);

    lundPlaneKt1.GetXaxis().SetRangeUser(rangeXLow, rangeXHigh);
    lundPlaneKt1.GetYaxis().SetRangeUser(rangeYLow, rangeYHigh);
    lundPlaneKt1.GetYaxis().SetTitle("ln(#it{k_{t}} / GeV)");


    lundPlaneKt1.Draw("COLZ");

    AS.myText( 0.40, 0.85, 1, "Primary LJP", 0.053);
    AS.myText( 0.40, 0.79, 1, "%s / %s"%(descriptions[j], descriptions[i]), 0.053);

    canvas.SaveAs("plots/ljpRatios/Kt%s_%s.pdf"%(outNames[i], outNames[j]));
    lundPlaneKt1.Multiply(lundPlaneKt2);
    canvas.SetLogz(0);


    file2.Close();

  file.Close();


colors = []
colors.append("#000000");
colors.append("#539327");
colors.append("#1180AE");
colors.append("#5F4B8B");
colors.append("#FF6F61");
colors.append("#d1244d");
colors.append("#c7c7c7");
colors.append("#009499");
canvas.SetRightMargin(0.05);

histNames = ["jetPt"]


count =0;
h_lists = {};
for k in range(len(histNames)):
  h_lists[histNames[k]] = [];

for i in range(len(mcFiles)):
  file = ROOT.TFile(mcFiles[i]);
  for k in range(len(histNames)):
    cHist = plotHelper.getHist(file, histNames[k], outNames[i], colors[count]);
    h_lists[histNames[k]].append(cHist);

  count+=1;


for k in range(len(histNames)):
  plotHelper.getRange(h_lists[histNames[k]], False, True);
  plotHelper.drawHists("plots/extra/%s"%(histNames[k]), h_lists[histNames[k]], False, [], False, "hist", "");







