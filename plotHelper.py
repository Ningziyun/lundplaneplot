import math
import ROOT
import plotStyle as AS

def getRangeMinMax(minVal, maxVal, isLog, isZeroed):
  if(isLog):
    if(minVal <=0):
      minVal = 1e-10;
    if(maxVal <=0):
      maxVal = 1e-8;

    maxVal = maxVal + pow(10, math.log10(maxVal)+  (math.log10(maxVal)-math.log10(minVal))/2.);
    minVal = minVal / 2;

  else:
    if(isZeroed):
      minVal = 1e-7;

    diff = maxVal - minVal;
    maxVal += diff*1.0;
    if(not isZeroed):
      minVal -= diff*0.20;

  if(minVal == 0):
    minVal = 1e-7;

  return minVal, maxVal;

def getHist(file, histName, title, color):
  hist = file.Get(histName);
  hist.SetDirectory(0);
  hist.SetTitle(title);
  hist.SetMarkerColor(ROOT.TColor.GetColor(color));
  hist.SetLineColor(ROOT.TColor.GetColor(color));
  return hist;




def configureHist2D(hist):
    hist.GetXaxis().SetTitleSize(0.055);
    hist.GetYaxis().SetTitleSize(0.055);
    hist.GetZaxis().SetTitleSize(0.055);
    hist.GetXaxis().SetLabelSize(0.045); 
    hist.GetYaxis().SetLabelSize(0.045);
    hist.GetZaxis().SetTitleOffset(1.15);
    hist.GetXaxis().SetTitleOffset(0.95);
    hist.GetYaxis().SetTitleOffset(0.85);

def configureHist(hist, color, lineStyle, markerStyle, fillStyle, fillColor, fillAlpha, xAxis, yAxis):
      hist.UseCurrentStyle();
      hist.GetXaxis().SetTitle(xAxis);
      hist.GetYaxis().SetTitle(yAxis);
      hist.SetMarkerColor(color);
      hist.SetLineColor(color);
      hist.SetLineStyle(lineStyle);
      hist.SetFillStyle(fillStyle);
      hist.SetMarkerStyle(markerStyle);
      hist.SetMarkerSize(1.5);
      hist.SetFillColorAlpha(fillColor, fillAlpha);
      hist.SetLineWidth(2);



  
def configureHist(hist, refHist):
  isTransparent = refHist.IsTransparent();
  fillAlpha = 0.0;
  configureHist(hist, refHist.GetMarkerColor(), refHist.GetLineStyle(), refHist.GetMarkerStyle(), refHist.GetFillStyle(), refHist.GetFillColor(), fillAlpha, refHist.GetXaxis().GetTitle(), refHist.GetYaxis().GetTitle());
    
  
def configurePlot(hist, padHeight):
  hist.GetYaxis().SetLabelSize(0.032 / padHeight);
  hist.GetYaxis().SetTitleSize(0.032 / padHeight);
  hist.GetYaxis().SetTitleOffset(1.96 * padHeight);
  hist.GetYaxis().SetTickLength(0.03);
    
  hist.GetXaxis().SetLabelSize(0.032 / padHeight);
  hist.GetXaxis().SetTitleSize(0.032 / padHeight);
  hist.GetXaxis().SetTitleOffset(1.3);
  hist.GetYaxis().SetTickLength(0.03);
  hist.GetXaxis().SetTickLength(0.02 / padHeight);
    

def getRange(hists, isLog, isZeroed, setMinVal=0, setMaxVal=0):
  if(setMinVal != setMaxVal) :
    if(setMinVal == 0):
      setMinVal = 1e-7;
    setMaxVal = setMaxVal - 1e-7;
    for i in range(len(hists)):
      hists[i].GetYaxis().SetRangeUser(setMinVal, setMaxVal);
    return;

  maxVal = -1000000;
  minVal = 10000000;

  for fit in range(len(hists)):
    hists[fit].GetYaxis().UnZoom();
    if(hists[fit].GetBinContent(hists[fit].GetMaximumBin()) > maxVal):
       maxVal = hists[fit].GetBinContent(hists[fit].GetMaximumBin());
    if(hists[fit].GetBinContent(hists[fit].GetMinimumBin()) < minVal):
       minVal = hists[fit].GetBinContent(hists[fit].GetMinimumBin());

  myMin, myMax = getRangeMinMax(minVal, maxVal, isLog, isZeroed);

  for i in range(len(hists)):
      hists[i].GetYaxis().SetRangeUser(myMin, myMax);



  
def makeLabels(labels, atlasLabel, padHeight, xPos):
    textSize = 0.030 / padHeight;
    
    ROOT.gStyle.SetTextSize(textSize);
    Y = 0.88;
    delta = textSize*1.2;
    Y = Y-delta;

    for i in range(len(labels)):
      myText( xPos, Y, 1, labels[i]);
      Y = Y-delta;

    ROOT.gStyle.SetTextSize(0.04);
    
  
def makeLegends(hists, drawStyle, padHeight,xPos, dX=0, nColumns=1):
  Ystart = 0.9;

  spacing = 0.03 / padHeight;
  dY = len(hists) * spacing / padHeight;

  if(dX>1 or dX==0):
    dX = 0.97 - xPos;

  yLow = Ystart-dY;
  if( yLow < 0):
    yLow = 0.6;

  leg = ROOT.TLegend(xPos, yLow, xPos+dX, Ystart, "","brNDC");
  leg.SetNColumns(nColumns);
  leg.SetBorderSize(0);
  leg.SetLineColor(1);
  leg.SetLineStyle(1);
  leg.SetLineWidth(1);
  leg.SetFillColor(0);
  leg.SetFillStyle(0);
  leg.SetTextFont(42);

  for fit in range(len(hists)):
    if(drawStyle[fit].find("hist p") >= 0 or drawStyle[fit].find("HIST P") >= 0):
      leg.AddEntry(hists[fit], hists[fit].GetTitle(), "lp");
    elif(drawStyle[fit].find("hist") >= 0 or drawStyle[fit].find("HIST") >= 0):
      leg.AddEntry(hists[fit], hists[fit].GetTitle(), "l");
    elif(drawStyle[fit] == "p" or drawStyle[fit].find("P") >=0):
      leg.AddEntry(hists[fit], hists[fit].GetTitle(), "p");
    elif(drawStyle[fit] == "px" or drawStyle[fit].find("PX") >=0):
      leg.AddEntry(hists[fit], hists[fit].GetTitle(), "p");
    elif(drawStyle[fit] == "p2" or drawStyle[fit].find("P2") >=0):
      leg.AddEntry(hists[fit], hists[fit].GetTitle(), "p");

  return leg;




def drawHists(fileName, hists, isLog, histLabels, isLogX, drawStyle, atlasLabel):
  if(len(hists) ==0):
    return;
  c1 = ROOT.TCanvas("c1","c1", 800,600);
  c1.cd();
  c1.SetLogy(isLog);
  c1.SetLogx(isLogX);

  configurePlot(hists[0], 0.9);
  hists[0].DrawCopy("AXIS");
  drawStyles = []

  for i in range(len(hists)):
    configurePlot(hists[i], 0.9);
    hists[i].DrawCopy("%s SAME"%(drawStyle));
    drawStyles.append(drawStyle);

  makeLabels(histLabels, atlasLabel, 0.9, 0.2);
  leg = makeLegends(hists, drawStyles, 0.85, 0.6);
  leg.Draw();
  ROOT.gPad.RedrawAxis();

  printHist(c1, fileName);


def printHist(c1, fileName):
  c1.Print("%s.pdf"%(fileName));


