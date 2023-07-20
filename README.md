# Heartbeat4D

This repository is to hold code related to a workflow which allows creation of an augmented reality mobile app starting from medical 4D CT cardiac imaging.

The repository contains a Slicer module called "PropagateSegToOtherPhases" which can be added to Slicer (available at [download.slicer.org](https://download.slicer.org)).  This module facilitates the segmentation of cardiac regions across all phases of a 4D cardiac CT (sometimes also referred to as a dynamic or multiphase acquisition).  The module also facilitates the export of the segmented regions as OBJ-format surface files which can be imported into the Unity game engine for ultimate export into an augmented reality application.  C# scripts to enable animation and interactive control of dynamic surface visualization within Unity are included in the UnityProjectScripts/ folder of this repository. 

For further explanation, please see the publication associated with this repository.
_HEARTBEAT4D: An Open-source Toolbox for Turning 4D Cardiac CT into VR/AR_.  https://pubmed.ncbi.nlm.nih.gov/35614275/

Citation:

Bindschadler M, Buddhe S, Ferguson MR, Jones T, Friedman SD, Otto RK. HEARTBEAT4D: An Open-source Toolbox for Turning 4D Cardiac CT into VR/AR. J Digit Imaging. 2022 Dec;35(6):1759-1767. doi: 10.1007/s10278-022-00659-y. Epub 2022 May 25. PMID: 35614275; PMCID: PMC9712868.

