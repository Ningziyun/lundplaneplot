# Lund Plane Plotting 



## Getting started

You need Fastjet and ROOT in order to be able to run this code.

```
brew install fastjet
brew install root
python -m venv venv
source venv/bin/activate
conda activate rootenv (for apple)
pip install pyroot
```


You may need to also add an environment variable that points to your fastjet installation. 
Your exact path may be different depending on how and where you install it, but I have provided an example.

```
PYTHONPATH=$PYTHONPATH:/opt/homebrew/Cellar/fastjet/3.4.3/lib/python3.10/site-packages/
```

## Running the code

This code is run in two steps. The first takes a set of ROOT files of events with information about the jets and their constituents, 
and converts this into another ROOT file with histograms that have condensed this information (mostly into histograms about the Lund jet plane).

```
python ljpAnalysis.py --filename fileList.txt
```

The second part does the actual plotting of these files. 
It takes the histograms that were produced in the first step, and plots ratios of the different files, and adds some stylistic features to make the plots easier to read.

```
python runPlotting.py --filename histFileNames.txt
```

In both cases, the input files can be specified, but examples have been provided for each.



