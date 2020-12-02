import os
import unittest
import vtk, qt, ctk, slicer
import vtkSegmentationCore  # added to be able to create empty segments
from slicer.ScriptedLoadableModule import *
import logging
import datetime  # to be able to print times and elapsed times
import SegmentEditorEffects  # used for smoothing parameter effect parameters
import sys  # to be able to flush print statement buffer
import re  # regular expressions (for renaming segmentation)


#
# PropagateSegToOtherPhases
#

class PropagateSegToOtherPhases(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "PropagateSegToOtherPhases"  # TODO make this more human readable by adding spaces
        self.parent.categories = ["Examples"]
        self.parent.dependencies = []
        self.parent.contributors = [
            "Mike Bindschadler (Seattle Childrens Hospital)"]  # replace with "Firstname Lastname (Organization)"
        self.parent.helpText = """
    This module is designed to make segmentation of a 4D contrast enhanced cardiac sequence as
    straightforward as possible. It helps initialize segmentatation regions, 
    then after the user performs one careful segmentation at one time point, 
    propagates that segmentation to one or all other time points. 
    """
        self.parent.helpText += self.getDefaultModuleDocumentationLink()
        self.parent.acknowledgementText = """
    Originally developed by Mike Bindschadler, Seattle Childrens Hospital. It 
    was funded by Radiology
    """  # replace with organization, grant and thanks.


#
# PropagateSegToOtherPhasesWidget
#

class PropagateSegToOtherPhasesWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # Instantiate and connect widgets ...

        # Set up default names and colors
        LAcolor = (0.964706, 0.109804, 0.521569)  # bright pinkish color
        LVcolor = (0.894118, 0.564706, 0.160784)  # orangey color
        AortaColor = (0.866667, 0.00784314, 0.0941176)  # almost true red
        RAcolor = (0.0823529, 0.847059, 0.796078)  # cyan-ish
        RVcolor = (0.513725, 0.458824, 0.823529)  # lavender
        PAcolor = (0.054902, 0.113725, 0.933333)  # almost true blue
        OtherColor = (0.862745, 0.960784, 0.0784314)  # sort of sickly yellow
        BelowThreshColor = (0.501961, 0.682353, 0.501961)  # greenish blue

        BloodPoolColor = (196.0 / 255.0, 53.0 / 255.0, 214.0 / 255.0)  # bright bluish purple

        self.defaultSegmentNamesAndColors = [('LA', LAcolor),
                                             ('LV', LVcolor),
                                             ('Aorta', AortaColor),
                                             ('RA', RAcolor),
                                             ('RV', RVcolor),
                                             ('PA', PAcolor),
                                             ('Other', OtherColor),
                                             ('BelowThresh', BelowThreshColor)]
        self.defaultBloodPoolNameAndColor = ('BloodPool', BloodPoolColor)

        #
        #### Initialize
        # Sequence Browser Selector (allow none)
        # Initialize First Segmentation Button (creates segs, initializes colors,incl frame in name)
        #### Propagate (Individual Steps)
        # Blood Pool Threshold (slider???, set same as threshold max in seg editor??)
        # Base Segmentation Selector (initalize to created segmentation)
        # Close holes distance: 2.5 mm
        # Launch Close Holes
        # Erosion distance: 5 mm
        # "Other" Erosion Distance: 1 mm (less than 1)
        # Launch Erosion (erodes base segmenation into new segmentation)
        # PrevFrame NextFrame buttons
        # Update BelowThresh Region Button
        # Initialize GrowFromSeeds
        # Update GrowFromSeeds
        # Apply GrowFromSeeds
        # Rename New Segmentation
        #### Propagate
        # Propagate to Next Frame
        # Propagate to All Frames
        #

        #
        #### Initialize
        # Sequence Browser Selector (allow none)
        # Initialize First Segmentation Button (creates segs, initializes colors,incl frame in name)

        #
        # "Initialize" Collapsable Area
        #
        initAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        initAreaCollapsibleButton.text = 'Initialize'
        self.layout.addWidget(initAreaCollapsibleButton)
        initAreaFormLayout = qt.QFormLayout(initAreaCollapsibleButton)

        #
        # Test printing something to the interactor window
        #
        self.testPrintButton = qt.QPushButton("Test print to Interactor")
        self.testPrintButton.toolTip = "Run the algorithm."
        self.testPrintButton.enabled = True
        initAreaFormLayout.addRow('Test Print Button', self.testPrintButton)

        #
        # Sequence Browser Selector
        #
        self.sequenceBrowserSelector = slicer.qMRMLNodeComboBox()
        self.sequenceBrowserSelector.nodeTypes = ["vtkMRMLSequenceBrowserNode"]
        self.sequenceBrowserSelector.addEnabled = False  # allows additon of a new Segmentation Node
        self.sequenceBrowserSelector.removeEnabled = False  # allows deletion of Current segmentation node
        self.sequenceBrowserSelector.noneEnabled = True  # False # allows deselection
        self.sequenceBrowserSelector.showHidden = False  # ?
        self.sequenceBrowserSelector.showChildNodeTypes = False
        self.sequenceBrowserSelector.setMRMLScene(slicer.mrmlScene)
        initAreaFormLayout.addRow('Sequence Browser:', self.sequenceBrowserSelector)

        #
        # Initialize empty segmentation and segments button
        #
        self.GenerateEmptySegmentsButton = qt.QPushButton("Initialize Empty Segments/Segmentation")
        self.GenerateEmptySegmentsButton.toolTip = 'Initialize new empty Segmentation and add empty segments with default colors'
        initAreaFormLayout.addRow(self.GenerateEmptySegmentsButton)

        #### Propagate (Individual Steps)
        # Blood Pool Threshold (slider???, set same as threshold max in seg editor??)
        # Base Segmentation Selector (initalize to created segmentation)
        # Erosion distance: mm
        # "Other" Erosion Distance: 1 mm (less than 1)
        # Launch Erosion (erodes base segmenation into new segmentation)
        # PrevFrame NextFrame buttons
        # Update BelowThresh Region Button
        # Initialize GrowFromSeeds
        # Update GrowFromSeeds
        # Apply GrowFromSeeds
        # Rename New Segmentation

        # Propagate Steps Area (collapsible container)

        propStepsAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        propStepsAreaCollapsibleButton.text = 'Propagate Segmentation (individual steps)'
        self.layout.addWidget(propStepsAreaCollapsibleButton)
        propStepsAreaFormLayout = qt.QFormLayout(propStepsAreaCollapsibleButton)

        # Base Segmentation Selector
        self.baseSegmentationSelector = slicer.qMRMLNodeComboBox()
        self.baseSegmentationSelector.nodeTypes = ["vtkMRMLSegmentationNode"]
        self.baseSegmentationSelector.selectNodeUponCreation = True
        self.baseSegmentationSelector.addEnabled = False  # allows additon of a new Segmentation Node
        self.baseSegmentationSelector.removeEnabled = True  # allows deletion of Current segmentation node
        self.baseSegmentationSelector.noneEnabled = True  # False # allows deselection
        self.baseSegmentationSelector.showHidden = False  # ?
        self.baseSegmentationSelector.showChildNodeTypes = False
        self.baseSegmentationSelector.setMRMLScene(slicer.mrmlScene)
        self.baseSegmentationSelector.setToolTip("Choose the Segmentation to Start From")
        propStepsAreaFormLayout.addRow("Base Segmentation: ", self.baseSegmentationSelector)

        # spinbox to choose close holes distance
        self.closeHolesDistanceSelector = qt.QDoubleSpinBox()
        self.closeHolesDistanceSelector.setSuffix(' mm')
        self.closeHolesDistanceSelector.setRange(0, 20)
        self.closeHolesDistanceSelector.setSingleStep(0.1)
        self.closeHolesDistanceSelector.setValue(2.5)
        propStepsAreaFormLayout.addRow('Close Holes Distance: ', self.closeHolesDistanceSelector)

        # Launch Close Holes button
        self.closeHolesButton = qt.QPushButton('Launch Close Holes')
        self.closeHolesButton.toolTip = "Close holes in all regions except BelowThresh region"
        self.closeHolesButton.enabled = True
        propStepsAreaFormLayout.addRow(self.closeHolesButton)

        # Erosion Distance spinbox to choose erosion distance in mm
        self.erosionDistanceSelector = qt.QDoubleSpinBox()
        self.erosionDistanceSelector.setSuffix(' mm')
        self.erosionDistanceSelector.setRange(0, 100)
        self.erosionDistanceSelector.setValue(5)
        propStepsAreaFormLayout.addRow("Erosion Distance: ", self.erosionDistanceSelector)

        # ErosionDistance for "Other" region (spinbox to choose "Other" erosion distance in mm)
        self.otherErosionDistanceSelector = qt.QDoubleSpinBox()
        self.otherErosionDistanceSelector.setToolTip(
            'Set erosion distance for "Other" region, the above-threshold, non-blood segment')
        self.otherErosionDistanceSelector.setSuffix(' mm')
        self.otherErosionDistanceSelector.setRange(0, 100)
        self.otherErosionDistanceSelector.setValue(1)
        propStepsAreaFormLayout.addRow('"Other" Erosion Distance: ', self.otherErosionDistanceSelector)

        #
        # Erode Button
        #
        self.erodeButton = qt.QPushButton("Erode Selected Segmentation")
        self.erodeButton.toolTip = "Run erosion of segments"
        self.erodeButton.enabled = False
        propStepsAreaFormLayout.addRow(self.erodeButton)

        #
        # Prev/Next Frame Buttons
        #
        self.prevFrameButton = qt.QPushButton("Previous Frame")
        self.prevFrameButton.toolTip = "Decrement the sequence index"
        self.prevFrameButton.enabled = True
        self.nextFrameButton = qt.QPushButton("Next Frame")
        self.nextFrameButton.toolTip = "Increment the sequence index"
        self.nextFrameButton.enabled = True
        navFrameLayout = qt.QFormLayout()
        navFrameLayout.addWidget(self.prevFrameButton)
        navFrameLayout.addWidget(self.nextFrameButton)  # TODO get these on the same line
        propStepsAreaFormLayout.addRow('Frame Navigation:', navFrameLayout)
        #
        # Blood Pool Threshold Slider
        #
        self.imageThresholdSliderWidget = ctk.ctkSliderWidget()
        self.imageThresholdSliderWidget.singleStep = 1
        self.imageThresholdSliderWidget.minimum = -1024  # TODO change to image minimum
        self.imageThresholdSliderWidget.maximum = 3100  # TODO change to image maximum
        self.imageThresholdSliderWidget.value = 339.5
        self.imageThresholdSliderWidget.setToolTip(
            "Set threshold value for determining blood pool. Voxels that have intensities lower than this value will be considered non-blood.")
        propStepsAreaFormLayout.addRow("Blood Pool Threshold", self.imageThresholdSliderWidget)
        # Update BelowThresh Region Button
        updateBelowThreshButton = qt.QPushButton('Update "BelowThresh" Region')
        updateBelowThreshButton.toolTip = 'Run this only after changing the frame'
        updateBelowThreshButton.enabled = True
        self.updateBelowThreshButton = updateBelowThreshButton
        propStepsAreaFormLayout.addRow(self.updateBelowThreshButton)

        # Run GrowFromSeeds (all in one step)
        runGrowFromSeedsButton = qt.QPushButton('Run GrowFromSeeds')
        runGrowFromSeedsButton.toolTip = 'Press to run GrowFromSeeds on the current frame using the eroded segmentation'
        runGrowFromSeedsButton.enabled = True
        self.runGrowFromSeedsButton = runGrowFromSeedsButton
        propStepsAreaFormLayout.addRow(self.runGrowFromSeedsButton)
        '''
        # Initialize GrowFromSeeds
        initGrowFromSeedsButton = qt.QPushButton('Initialize GrowFromSeeds')
        initGrowFromSeedsButton.toolTip  = 'Press to run the initialization of GrowFromSeeds on the current frame using the eroded segmentation'
        initGrowFromSeedsButton.enabled = True
        self.initGrowFromSeedsButton = initGrowFromSeedsButton
        propStepsAreaFormLayout.addRow(self.initGrowFromSeedsButton)
        
        # Update GrowFromSeeds
        updateGrowFromSeedsButton = qt.QPushButton('Update GrowFromSeeds')
        updateGrowFromSeedsButton.toolTip  = 'Press to update the initialization of GrowFromSeeds after making any modifications of the current segmenatation'
        updateGrowFromSeedsButton.enabled = False # only enable after initialization 
        self.updateGrowFromSeedsButton = updateGrowFromSeedsButton
        propStepsAreaFormLayout.addRow(self.updateGrowFromSeedsButton)
        
        # Apply GrowFromSeeds
        applyGrowFromSeedsButton = qt.QPushButton('Finalize GrowFromSeeds')
        applyGrowFromSeedsButton.toolTip  = 'Press to run the initialization of GrowFromSeeds on the current frame using the eroded segmentation'
        applyGrowFromSeedsButton.enabled = True
        self.applyGrowFromSeedsButton = applyGrowFromSeedsButton
        propStepsAreaFormLayout.addRow(self.applyGrowFromSeedsButton)
        '''
        # Rename New Segmentation (and make it the new current one)
        renameSegmentationButton = qt.QPushButton('Rename Eroded and Regrown Segmentation')
        renameSegmentationButton.enabled = True
        self.renameSegmentationButton = renameSegmentationButton
        propStepsAreaFormLayout.addRow(self.renameSegmentationButton)

        # Propagate Segmentation (All steps)
        propAllAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        propAllAreaCollapsibleButton.text = 'Propagate Segmentation (all steps)'
        self.layout.addWidget(propAllAreaCollapsibleButton)
        propAllAreaFormLayout = qt.QFormLayout(propAllAreaCollapsibleButton)
        # Propagate Segmentation (single step)
        propagateSingleFrameButton = qt.QPushButton('Propagate Segmentation 1 Frame')
        self.propagateSingleFrameButton = propagateSingleFrameButton
        propAllAreaFormLayout.addRow(self.propagateSingleFrameButton)
        propagateAllFramesButton = qt.QPushButton('Propagate Segmentation to All Frames')
        self.propagateAllFramesButton = propagateAllFramesButton
        propAllAreaFormLayout.addRow(self.propagateAllFramesButton)

        # Export All to OBJ files section
        exportOBJAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        exportOBJAreaCollapsibleButton.text = 'Export to OBJ'
        self.layout.addWidget(exportOBJAreaCollapsibleButton)
        exportOBJAreaFormLayout = qt.QFormLayout(exportOBJAreaCollapsibleButton)
        # Direcory selection
        exportOBJdirSelector = ctk.ctkPathLineEdit()
        exportOBJdirSelector.filters = ctk.ctkPathLineEdit.Dirs
        exportOBJdirSelector.settingKey = 'ExportOBJOutputDir'  # not sure what this line does
        if not exportOBJdirSelector.currentPath:  # initialize
            defaultOutputPath = slicer.app.defaultScenePath
            exportOBJdirSelector.setCurrentPath(defaultOutputPath)
        self.exportOBJdirSelector = exportOBJdirSelector
        exportOBJAreaFormLayout.addRow('OBJ export folder:', exportOBJdirSelector)
        # Export button
        self.exportOBJbutton = qt.QPushButton('Export All to OBJ')
        exportOBJAreaFormLayout.addRow(self.exportOBJbutton)

        # Hollow section
        hollowAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        hollowAreaCollapsibleButton.text = 'Hollow Segmentation(s)'
        self.layout.addWidget(hollowAreaCollapsibleButton)
        hollowAreaFormLayout = qt.QFormLayout(hollowAreaCollapsibleButton)
        self.hollowSegSelector = slicer.qMRMLNodeComboBox()
        self.hollowSegSelector.nodeTypes = ["vtkMRMLSegmentationNode"]
        self.hollowSegSelector.selectNodeUponCreation = True
        self.hollowSegSelector.addEnabled = False  # allows additon of a new Segmentation Node
        self.hollowSegSelector.removeEnabled = True  # allows deletion of Current segmentation node
        self.hollowSegSelector.noneEnabled = True  # False # allows deselection
        self.hollowSegSelector.showHidden = False  # ?
        self.hollowSegSelector.showChildNodeTypes = False
        self.hollowSegSelector.setMRMLScene(slicer.mrmlScene)
        self.hollowSegSelector.setToolTip("Choose the Segmentation to Start From")
        hollowAreaFormLayout.addRow("Segmentation to Copy and Hollow: ", self.hollowSegSelector)
        self.hollowVolumeSelector = slicer.qMRMLNodeComboBox()
        self.hollowVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.hollowVolumeSelector.selectNodeUponCreation = True
        self.hollowVolumeSelector.setMRMLScene(slicer.mrmlScene)
        hollowAreaFormLayout.addRow("Volume Segmentation Refers to: ", self.hollowVolumeSelector)
        self.hollowShellThicknessMmSelector = qt.QDoubleSpinBox()
        self.hollowShellThicknessMmSelector.setSuffix(' mm')
        self.hollowShellThicknessMmSelector.setRange(0, 20)
        self.hollowShellThicknessMmSelector.setSingleStep(0.1)
        self.hollowShellThicknessMmSelector.setValue(5.0)
        hollowAreaFormLayout.addRow('Shell thickness (non-LV):', self.hollowShellThicknessMmSelector)
        self.hollowShellLVThicknessMmSelector = qt.QDoubleSpinBox()
        self.hollowShellLVThicknessMmSelector.setSuffix(' mm')
        self.hollowShellLVThicknessMmSelector.setRange(0, 30)
        self.hollowShellLVThicknessMmSelector.setSingleStep(0.1)
        self.hollowShellLVThicknessMmSelector.setValue(15.0)
        hollowAreaFormLayout.addRow('LV shell thickness:', self.hollowShellLVThicknessMmSelector)
        self.launchHollowButton = qt.QPushButton('Launch Hollowing')
        hollowAreaFormLayout.addRow(self.launchHollowButton)

        # Add vertical spacer to layout
        self.layout.addStretch(1)

        #########
        # connections
        self.sequenceBrowserSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSequenceBrowserSelectorChange)
        self.testPrintButton.connect('clicked(bool)', self.onTestPrintButtonClick)
        self.GenerateEmptySegmentsButton.connect('clicked(bool)', self.onGenerateEmptySegmentsButtonClick)
        self.closeHolesButton.connect('clicked(bool)', self.onCloseHolesButtonClick)
        self.erodeButton.connect('clicked(bool)', self.onErodeButtonClick)
        self.baseSegmentationSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSegmentationSelectorChange)
        self.prevFrameButton.connect('clicked(bool)', self.onPrevFrameButtonClick)
        self.nextFrameButton.connect('clicked(bool)', self.onNextFrameButtonClick)
        self.updateBelowThreshButton.connect('clicked(bool)', self.onUpdateBelowThreshButtonClick)

        self.runGrowFromSeedsButton.connect('clicked(bool)', self.onRunGrowFromSeedsButtonClick)
        '''self.initGrowFromSeedsButton.connect('clicked(bool)',self.onInitGrowFromSeedsButtonClick)
        self.updateGrowFromSeedsButton.connect('clicked(bool)',self.onUpdateGrowFromSeedsButtonClick)
        self.applyGrowFromSeedsButton.connect('clicked(bool)',self.onApplyGrowFromSeedsButtonClick)
        '''
        self.renameSegmentationButton.connect('clicked(bool)', self.onRenameSegmentationButtonClick)

        self.propagateAllFramesButton.connect('clicked(bool)', self.onPropagateAllFramesButtonClick)
        self.propagateSingleFrameButton.connect('clicked(bool)', self.onPropagateSingleFrameButtonClick)
        self.exportOBJbutton.connect('clicked(bool)', self.onExportOBJbuttonClick)
        self.launchHollowButton.connect('clicked(bool)', self.onLaunchHollowButtonClick)

        # Controls which don't need connections:
        # erosionDistanceSelector
        # otherErosionDistanceSelector
        # imageThresholdSliderWidget
        # exportOBJdirSelector
        # hollowShellThicknessMmSelector
        # hollowShellLVThicknessMmSelector

        # Refresh Apply button state
        # self.onSegmentationSelect()

    def getCurrentFrameNumber(self):
        # return current frame number of currently selected sequence browser.
        # returns None if there isn't a currently selected sequence browser
        curSeqBrowserNode = self.sequenceBrowserSelector.currentNode()
        if curSeqBrowserNode:  # None if there isn't one
            return curSeqBrowserNode.GetSelectedItemNumber()
        else:
            return None

    def getCloseHolesDist(self):
        # get selected hole closing distance value
        return self.closeHolesDistanceSelector.value

    def getErosionDist(self):
        # get selected erosion distance
        return self.erosionDistanceSelector.value

    def getOtherErosionDist(self):
        # get erosion distance to use for "Other" region.  Typically this should
        # be smaller than the regular erosion distance because structures usually
        # in "Other" are thin enough that eroding them 5 mm eliminates them
        # completely, which is unhelpful for consistency of segmentation...
        return self.otherErosionDistanceSelector.value

    def getShellThickness(self):
        return self.hollowShellThicknessMmSelector.value

    def getShellLVThickness(self):
        return self.hollowShellLVThicknessMmSelector.value

    def cleanup(self):
        pass

    def onSequenceBrowserSelectorChange(self):
        pass

    def onSegmentationSelectorChange(self):
        self.erodeButton.enabled = self.baseSegmentationSelector.currentNode() and True  # and self.outputSelector.currentNode()

    def onTestPrintButtonClick(self):
        logic = PropagateSegToOtherPhasesLogic()
        logic.runTestPrint('You pressed the test print button!')

    def onGenerateEmptySegmentsButtonClick(self):
        logic = PropagateSegToOtherPhasesLogic()
        segmentNamesAndColors = self.defaultSegmentNamesAndColors
        # Check if there is a selected segmentation already
        # if not, create it
        selectedSegmentationNode = self.baseSegmentationSelector.currentNode()
        if not selectedSegmentationNode:
            selectedSegmentationNode = slicer.vtkMRMLSegmentationNode()
            newSegNodeName = 'SegForFrame_' + str(self.getCurrentFrameNumber())
            selectedSegmentationNode.SetName(newSegNodeName)
            slicer.mrmlScene.AddNode(selectedSegmentationNode)  # add to hierarchy
            self.baseSegmentationSelector.setCurrentNode(
                selectedSegmentationNode)  # select the newly created segmentation node

        # Generate the empty segments
        logic.generateEmptySegments(selectedSegmentationNode, segmentNamesAndColors)

    def onPrevFrameButtonClick(self):
        logic = PropagateSegToOtherPhasesLogic()
        logic.prevFrame(self.sequenceBrowserSelector.currentNode())
        pass

    def onNextFrameButtonClick(self):
        logic = PropagateSegToOtherPhasesLogic()
        logic.nextFrame(self.sequenceBrowserSelector.currentNode())

    def onUpdateBelowThreshButtonClick(self):
        logic = PropagateSegToOtherPhasesLogic()
        seqBrowserNode = self.sequenceBrowserSelector.currentNode()
        masterSequenceVolumeNode = seqBrowserNode.GetMasterSequenceNode()
        proxyVolumeNode = seqBrowserNode.GetProxyNode(masterSequenceVolumeNode)
        segmentationNode = self.baseSegmentationSelector.currentNode()  # should be "eroded" version at this point
        belowThreshSegmentID = 'BelowThresh'  # TODO make this more flexible!! (For example, allow alternative name for BelowThresh segment)
        threshValue = self.getThreshValue()
        logic.updateBelowThreshRegion(proxyVolumeNode, segmentationNode, threshValue, belowThreshSegmentID)

    def getThreshValue(self):
        return self.imageThresholdSliderWidget.value

    def onRunGrowFromSeedsButtonClick(self):
        logic = PropagateSegToOtherPhasesLogic()
        segmentationNode = self.baseSegmentationSelector.currentNode()  # should be eroded and have cleared and renewed BelowThresh segment at this point
        seqBrowserNode = self.sequenceBrowserSelector.currentNode()
        masterSequenceVolumeNode = seqBrowserNode.GetMasterSequenceNode()
        proxyVolumeNode = seqBrowserNode.GetProxyNode(
            masterSequenceVolumeNode)  # the sequence needs to be supplied because I suppose there might be multiple sequences associated with this browser and each will have a separate proxy node
        logic.runGrowFromSeeds(segmentationNode, proxyVolumeNode)
        '''
    def onInitGrowFromSeedsButtonClick(self):
        logic = PropagateSegToOtherPhasesLogic()
        segmentationNode = self.baseSegmentationSelector.currentNode() # should be eroded and have cleared and renewed BelowThresh segment at this point
        seqBrowserNode = self.sequenceBrowserSelector.currentNode()
        masterSequenceVolumeNode = seqBrowserNode.GetMasterSequenceNode()
        proxyVolumeNode = seqBrowserNode.GetProxyNode(masterSequenceVolumeNode) # the sequence needs to be supplied because I suppose there might be multiple sequences associated with this browser and each will have a separate proxy node
        logic.initGrowFromSeeds(segmentationNode,proxyVolumeNode)
    def onUpdateGrowFromSeedsButtonClick(self):
        pass
    def onApplyGrowFromSeedsButtonClick(self):
        pass
        '''

    def onRenameSegmentationButtonClick(self):
        logic = PropagateSegToOtherPhasesLogic()
        segmentationNode = self.baseSegmentationSelector.currentNode()
        currentFrameNum = self.getCurrentFrameNumber()
        logic.renameSegmentation(segmentationNode, currentFrameNum)
        pass

    def onPropagateAllFramesButtonClick(self):
        # Propagate existing segmentation to all other frames (handle logic of going forward and backward)
        print('Entered onPropagateAllFramesButton()')
        startTime = now()

        # Show a progress bar 
        self.pb = slicer.util.createProgressDialog()
        self.pb.show()
        self.pb.value = 0
        self.pb.labelText = 'Starting to process...'

        # Update the app process events, i.e. show the progress of the
        # progress bar
        slicer.app.processEvents()

        # Go through half the frames forward, then jump back and go through the other half backwards
        startingFrameNumber = self.getCurrentFrameNumber()
        startSegNode = self.baseSegmentationSelector.currentNode()
        
        totalNumberOfFrames = self.sequenceBrowserSelector.currentNode().GetNumberOfItems()
        numberOfTimesToGoForward = int(totalNumberOfFrames-startingFrameNumber-1)
        #numberOfTimesToGoForward = int(round((totalNumberOfFrames - 1) / 2.0))
        numberOfTimesToGoBackward = int(totalNumberOfFrames - numberOfTimesToGoForward - 1)

        # 
        numberFramesComplete = 1
        def update_progress_bar(numberFramesComplete):
            progress_value = round(numberFramesComplete/totalNumberOfFrames*100)
            self.pb.value =progress_value
            self.pb.labelText = 'Processing frame %i of %i...'%(numberFramesComplete+1,totalNumberOfFrames)
            slicer.app.processEvents()
        
        update_progress_bar(numberFramesComplete)

        for ind in range(numberOfTimesToGoForward):
            self.onPropagateSingleFrameButtonClick(backwardFlag=False)
            printNow('--COMPLETED SEG OF FRAME ' + str(self.getCurrentFrameNumber()) + ' --')
            numberFramesComplete +=1
            update_progress_bar(numberFramesComplete)

        # Reset to starting frame
        logic = PropagateSegToOtherPhasesLogic()
        logic.jumpToFrame(self.sequenceBrowserSelector.currentNode(), startingFrameNumber)
        # Reset to staring segmentation!
        self.baseSegmentationSelector.setCurrentNode(startSegNode)

        for ind in range(numberOfTimesToGoBackward):
            self.onPropagateSingleFrameButtonClick(backwardFlag=True)
            printNow('--COMPLETED SEG OF FRAME ' + str(self.getCurrentFrameNumber()) + ' --')
            numberFramesComplete +=1
            update_progress_bar(numberFramesComplete)
        #self.pb.value = 100 # automatically closes progress bar

        # TODO: Assemble segmentation and hollow segmentations into sequence?
        # Export all generated to OBJ?

        printNow('-----------------------------------')
        printNow('COMPLETED ALL FRAMES IN ONE CLICK!')
        printNow('Finished in ' + str(now() - startTime))
        printNow('-----------------------------------')

    def onPropagateSingleFrameButtonClick(self, backwardFlag=False):
        # Propagate existing segmentation to one other frames (handle logic of going forward and backward)
        print('Entered onPropagateSingleFrameButton()')

        # logic = PropagateSegToOtherPhasesLogic()
        startTime = now()
        # Set up as series of button clicks
        self.onErodeButtonClick()
        if backwardFlag:
            self.onPrevFrameButtonClick()
        else:
            self.onNextFrameButtonClick()
        self.onUpdateBelowThreshButtonClick()
        self.onRunGrowFromSeedsButtonClick()
        self.onRenameSegmentationButtonClick()
        self.onCloseHolesButtonClick()
        self.doHollowSingleFrame()  # differs from hollow button click because uses seq browser and recently
        # generated segmentation rather than independent selectors
        # TODO: Add hollowing here
        # What are the issues?  Need to specify segmentation, volume, shell and LV thicknesses,
        # oldSegmentationNode, bloodPoolNameAndColor, volumeNode, thickness=5.0, LVthickness=15.0,
        #                        segmentIDsToInclude=('LA', 'LV', 'Aorta', 'RA', 'RV', 'PA'))
        #
        printNow('-----------------------------------')
        printNow('COMPLETED NEXT FRAME IN ONE CLICK!')
        printNow('Finished in ' + str(now() - startTime))
        printNow('-----------------------------------')
    def doHollowSingleFrame(self):
        logic = PropagateSegToOtherPhasesLogic()
        volumeNode = self.getProxyVolumeNode()
        oldSegmentationNode = self.baseSegmentationSelector.currentNode()
        thickness = self.getShellThickness()
        LVthickness = self.getShellLVThickness()
        newHollowSegNode = logic.hollowToNewSeg(oldSegmentationNode, self.defaultBloodPoolNameAndColor, volumeNode, thickness=thickness,
                             LVthickness=LVthickness, segmentIDsToInclude=('LA', 'LV', 'Aorta', 'RA', 'RV', 'PA'))
        logic.addSheathSegmentToHollowSegNode(newHollowSegNode,volumeNode)
        # TODO: should something be done with the new node?  Maybe add to a list of segs to export?
        # TODO: merge with other Hollow function (don't really need both, was just for testing)

    def getProxyVolumeNode(self):
        sequenceBrowserNode = self.sequenceBrowserSelector.currentNode()
        masterVolumeNode = sequenceBrowserNode.GetMasterSequenceNode()
        proxyVolumeNode = sequenceBrowserNode.GetProxyNode(masterVolumeNode)
        return proxyVolumeNode
    def onCloseHolesButtonClick(self):
        # launch close holes for all regions except "BelowThresh", with editable region only BelowThresh
        logic = PropagateSegToOtherPhasesLogic()
        baseSegmentationNode = self.baseSegmentationSelector.currentNode()
        closeHolesDistanceMm = self.getCloseHolesDist()
        proxyVolumeNode = self.getProxyVolumeNode()
        belowThreshSegmentID = 'BelowThresh'  # TODO make this more flexible!! (For example, allow alternative name for BelowThresh segment)
        logic.runCloseHoles(baseSegmentationNode, closeHolesDistanceMm, belowThreshSegmentID, proxyVolumeNode)

    def onErodeButtonClick(self):
        logic = PropagateSegToOtherPhasesLogic()
        # enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
        # imageThreshold = self.imageThresholdSliderWidget.value
        # logic.run(self.inputSelector.currentNode(), self.outputSelector.currentNode(), imageThreshold, enableScreenshotsFlag)
        seqBrowserNode = self.sequenceBrowserSelector.currentNode()
        masterSequenceVolumeNode = seqBrowserNode.GetMasterSequenceNode()
        proxyVolumeNode = seqBrowserNode.GetProxyNode(masterSequenceVolumeNode)
        newSegNode = logic.runErode(self.baseSegmentationSelector.currentNode(), self.getErosionDist(),
                                    self.getOtherErosionDist(), proxyVolumeNode)  # , self.segmentSelector.currentText)
        if newSegNode:
            self.baseSegmentationSelector.setCurrentNode(newSegNode)

    def onExportOBJbuttonClick(self):
        logic = PropagateSegToOtherPhasesLogic()
        outputPath = self.exportOBJdirSelector.currentPath
        segNodeList = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')
        # TODO: edit this list of segmentations such that it only includes those
        # which are related to the selected base segmentation.  Currently, it is
        # just a list of ALL segmentations loaded.

        logic.exportAllToOBJ(outputPath, segNodeList,decimationFraction=0.4) # added decimation fraction to reduce model output size

    def onLaunchHollowButtonClick(self):
        logic = PropagateSegToOtherPhasesLogic()
        ### Removed next few lines for testing, just using single volume not volume sequence
        # seqBrowserNode = self.sequenceBrowserSelector.currentNode()
        # masterSequenceVolumeNode = seqBrowserNode.GetMasterSequenceNode()
        # proxyVolumeNode = seqBrowserNode.GetProxyNode(masterSequenceVolumeNode)
        ### Added next line
        volumeNode = self.hollowVolumeSelector.currentNode()

        oldSegmentationNode = self.hollowSegSelector.currentNode()
        thickness = self.getShellThickness()
        LVthickness = self.getShellLVThickness()
        # Old version using proxy node
        # logic.hollowToNewSeg(oldSegmentationNode,self.defaultBloodPoolNameAndColor,proxyVolumeNode,thickness=thickness,LVthickness=LVthickness,segmentIDsToInclude=('LA','LV','Aorta','RA','RV','PA'))
        # New version using volume node
        newHollowSegNode = logic.hollowToNewSeg(oldSegmentationNode, self.defaultBloodPoolNameAndColor, volumeNode, thickness=thickness,
                             LVthickness=LVthickness, segmentIDsToInclude=('LA', 'LV', 'Aorta', 'RA', 'RV', 'PA'))
        logic.addSheathSegmentToHollowSegNode(newHollowSegNode,volumeNode)

    def updateSegmentList(self):
        # Refreshes the list of segments
        self.segmentSelector.clear()  # remove all current items before repopulating
        segmentationNode = self.inputSelector.currentNode()
        if segmentationNode:
            segmentation = segmentationNode.GetSegmentation()
            numSegs = segmentation.GetNumberOfSegments()
            for segInd in range(numSegs):
                segmentName = segmentation.GetNthSegment(segInd).GetName()
                self.segmentSelector.addItem(segmentName)

    def getLogic(self):
        return PropagateSegToOtherPhasesLogic()

#####################################
#
# PropagateSegToOtherPhasesLogic
#
#####################################

class PropagateSegToOtherPhasesLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def generateEmptySegments(self, selectedSegmentationNode, segmentNamesAndColors):
        # Generate empty segments of appropriate names and colors
        # segmentNamesAndColors should be a Nx2 tuple, where the desired segment
        # name is in the first column and a 1x3 tuple describing the color is in
        # the second column (R,G,B) where each color is between 0 and 1 inclusive
        for segNameAndColor in segmentNamesAndColors:
            newSegment = vtkSegmentationCore.vtkSegment()  # create new segment
            newSegment.SetName(segNameAndColor[0])
            newSegment.SetColor(segNameAndColor[1])
            selectedSegmentationNode.GetSegmentation().AddSegment(newSegment)

    def runGrowFromSeeds(self, segmentationNode, proxyVolumeNode):
        # Initialize and finalize GrowFromSeeds in one step

        startTime = now()
        printNow('Starting GrowFromSeeds... (' + startTime.strftime("%I:%M:%S %p") + ')')

        # Create segment editor to get access to effects
        segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
        # To show segment editor widget (useful for debugging): segmentEditorWidget.show()
        segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
        segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
        slicer.mrmlScene.AddNode(segmentEditorNode)
        segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
        segmentEditorWidget.setSegmentationNode(segmentationNode)
        segmentEditorWidget.setMasterVolumeNode(proxyVolumeNode)

        # Set up the segmentation effect
        segmentEditorWidget.setActiveEffectByName("Grow from seeds")
        effect = segmentEditorWidget.activeEffect()
        # Parameters for GrowFromSeeds should include the Auto-updated checkbox,
        # the display inputs/results slider.
        # TODO check whether it is required that all segments are visible?
        # effect.setParameter()

        # Run Initialize!
        effect.self().onPreview()
        # Finalize (because I haven't figured out how to make this multistep yet)
        effect.self().onApply()

        # Clean up
        slicer.mrmlScene.RemoveNode(segmentEditorNode)

        totTime = now() - startTime
        printNow('Total elapsed time: ' + str(totTime))
        return

    '''        
    def initGrowFromSeeds(self,segmentationNode,proxyVolumeNode):
        # Initialize GrowFromSeeds effect
        # NOT USED CURRENTLY
        
        # Create segment editor to get access to effects
        segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
        # To show segment editor widget (useful for debugging): segmentEditorWidget.show()
        segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
        segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
        slicer.mrmlScene.AddNode(segmentEditorNode)
        segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
        segmentEditorWidget.setSegmentationNode(segmentationNode)
        segmentEditorWidget.setMasterVolumeNode(proxyVolumeNode)
        
        # Set up the segmentation effect
        segmentEditorWidget.setActiveEffectByName("Grow from seeds")
        effect = segmentEditorWidget.activeEffect()
        # Parameters for GrowFromSeeds should include the Auto-updated checkbox, 
        # the display inputs/results slider. 
        # TODO check whether it is required that all segments are visible?
        #effect.setParameter()
        
        # Run Initialize!
        effect.self().onPreview() 
        # Finalize (because I haven't figured out how to make this multistep yet)
        #effect.self().onApply()
        return #effect, segmentEditorNode # because we need to access it for updating and finalizing.
    '''

    def renameSegmentation(self, segmentationNode, currentFrameNum):
        # Rename segmentation for current frame, for example, change SegForFrame_0_eroded
        # to SegForFrame_1
        startTime = now()
        printNow('Starting renameSegmentation... (' + startTime.strftime("%I:%M:%S %p") + ')')
        currentSegName = segmentationNode.GetName()
        replacementPart = '_' + str(currentFrameNum)
        nameToChangeTo = re.sub('_\d+_eroded', replacementPart, currentSegName)
        segmentationNode.SetName(nameToChangeTo)
        totTime = now() - startTime
        printNow('Total elapsed time: ' + str(totTime))

    def runCloseHoles(self, baseSegmentationNode, closeHolesDistanceMm, belowThreshSegmentID, masterVolumeNode):
        # Close holes of the specified size for all segments of the given segmentation,
        # EXCEPT the segment identified as the belowThresh segment.
        #
        # Use the segment editor smoothing effect allowing editing of only the
        # current segment and the belowThresh segment (not sure how to do this yet)
        startTime = now()
        printNow('Starting Close Holes... (' + startTime.strftime("%I:%M:%S %p") + ')')
        # Create segment editor to get access to effects
        segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
        # To show segment editor widget (useful for debugging): segmentEditorWidget.show()
        segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
        segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
        slicer.mrmlScene.AddNode(segmentEditorNode)
        segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
        segmentEditorWidget.setSegmentationNode(baseSegmentationNode)
        segmentEditorWidget.setMasterVolumeNode(masterVolumeNode)

        # Set up the segmentation effect
        segmentEditorWidget.setActiveEffectByName("Smoothing")
        effect = segmentEditorWidget.activeEffect()
        # You can change parameters by calling: effect.setParameter("MyParameterName", someValue)
        effect.setParameter("SmoothingMethod", SegmentEditorEffects.MORPHOLOGICAL_CLOSING)
        effect.setParameter("KernelSizeMm", closeHolesDistanceMm)

        # Set masking settings
        maskMode = slicer.vtkMRMLSegmentEditorNode.PaintAllowedInsideSingleSegment
        segmentEditorNode.SetMaskMode(maskMode)  # limit editable area to inside a single segment
        segmentEditorNode.SetMaskSegmentID(belowThreshSegmentID)  # sets editable area to only inside BelowThresh
        segmentEditorNode.MasterVolumeIntensityMaskOff()  # uncheck editable intensity range checkbox
        overwriteMode = slicer.vtkMRMLSegmentEditorNode.OverwriteAllSegments
        segmentEditorNode.SetOverwriteMode(
            overwriteMode)  # I think this refers to the same type of restriction as the intensity range

        # Actually run the effect on each segment except BelowThresh
        segT = baseSegmentationNode.GetSegmentation()
        for segmentInd in range(segT.GetNumberOfSegments()):
            seg = segT.GetNthSegment(segmentInd)
            ID = segT.GetSegmentIdBySegment(seg)
            if ID == belowThreshSegmentID:
                # don't smooth
                print('NOT smoothing: ' + ID)
            else:  # do smooth
                print('Smoothing segment: ' + ID)
                segmentEditorWidget.setCurrentSegmentID(ID)
                effect.self().onApply()  # execute the effect

        # Clean up
        slicer.mrmlScene.RemoveNode(segmentEditorNode)

        printNow('Finished smoothing!')
        totTime = now() - startTime
        printNow('Total elapsed time: ' + str(totTime))

    def updateBelowThreshRegion(self, proxyVolumeNode, segmentationNode, threshValue, belowThreshSegmentID):
        # Clear and rethreshold BelowThresh segment, overwriting all other segments
        # TODO : Add checking that the input segmentation node is an eroded version, I keep accidentally running this on previous non-eroded one
        startTime = now()
        printNow('Starting Update BelowThresh... (' + startTime.strftime("%I:%M:%S %p") + ')')
        # Create segment editor to get access to effects
        segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
        # To show segment editor widget (useful for debugging): segmentEditorWidget.show()
        segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
        segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
        slicer.mrmlScene.AddNode(segmentEditorNode)
        segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
        segmentEditorWidget.setSegmentationNode(segmentationNode)
        segmentEditorWidget.setMasterVolumeNode(proxyVolumeNode)

        # Set BelowThresh segment as the active one (default is the first on the list)
        segmentEditorNode.SetSelectedSegmentID(belowThreshSegmentID)
        printNow('Selected segment ID: ' + belowThreshSegmentID)

        # Set up the segmentation effect
        segmentEditorWidget.setActiveEffectByName("Logical operators")
        effect = segmentEditorWidget.activeEffect()
        # You can change parameters by calling: effect.setParameter("MyParameterName", someValue)
        effect.setParameter("Operation", SegmentEditorEffects.LOGICAL_CLEAR)
        effect.setParameter("BypassMasking", 1)  # don't use masking parameters here
        effect.setParameter("ModifierSegmentID", "")  # not used for clear

        # Run the clear
        effect.self().onApply()
        printNow('BelowThresh segment cleared...')
        finishClearingTime = now()
        printNow('Time to clear: ' + str(finishClearingTime - startTime))

        # Change Active effect to Threshold
        segmentEditorWidget.setActiveEffectByName("Threshold")
        effect = segmentEditorWidget.activeEffect()
        effect.setParameter("MinimumThreshold", -1024.)  # TODO fix hard-coding of value here
        effect.setParameter("MaximumThreshold", threshValue)

        # Set masking settings (allow paint everywhere)
        maskMode = slicer.vtkMRMLSegmentEditorNode.PaintAllowedEverywhere
        segmentEditorNode.SetMaskMode(maskMode)  # limit editable area to inside a single segment
        # segmentEditorNode.SetMaskSegmentID(belowThreshSegmentID) # sets editable area to only inside BelowThresh
        segmentEditorNode.MasterVolumeIntensityMaskOff()  # uncheck editable intensity range checkbox
        overwriteMode = slicer.vtkMRMLSegmentEditorNode.OverwriteAllSegments
        segmentEditorNode.SetOverwriteMode(
            overwriteMode)  # I think this refers to the same type of restriction as the intensity range
        printNow('Applying Threshold...')

        # Apply threshold
        effect.self().onApply()
        printNow('New BelowThresh label region created by threshold')
        printNow('Time to threshold' + str(now() - finishClearingTime))
        # Clean up
        slicer.mrmlScene.RemoveNode(segmentEditorNode)
        printNow('Total Time: ' + str(now() - startTime))

    def runTestPrint(self, textToPrint):
        print(textToPrint)
        currentDT = datetime.datetime.now()
        printNow(currentDT.strftime("%I:%M:%S %p"))

    def nextFrame(self, seqBrowserNode):
        curFrameNum = seqBrowserNode.GetSelectedItemNumber()
        self.jumpToFrame(seqBrowserNode, curFrameNum + 1)  # next one
        printNow('next frame!')

    def prevFrame(self, seqBrowserNode):
        curFrameNum = seqBrowserNode.GetSelectedItemNumber()
        self.jumpToFrame(seqBrowserNode, curFrameNum - 1)  # previous one
        printNow('prev frame!')

    def jumpToFrame(self, seqBrowserNode, frameNumToJumpTo, loopFlag=True):
        numItems = seqBrowserNode.GetNumberOfItems()
        if loopFlag:
            # loop from top to bottom and vice versa using modulo
            frameNumToJumpTo = frameNumToJumpTo % numItems
        else:
            if frameNumToJumpTo >= numItems:
                frameNumToJumpTo = numItems - 1
            elif frameNumToJumpTo < 0:
                frameNumToJumpTo = 0

        printNow('Changing to frame ' + str(frameNumToJumpTo))
        seqBrowserNode.SetSelectedItemNumber(frameNumToJumpTo)

    def runErode(self, oldSegmentationNode, erosionDistance, otherErosionDistance, volumeNode):
        """
        Run the actual algorithm
        """
        printNow('Running runErode!!')

        startTime = now()
        printNow(startTime.strftime("%I:%M:%S %p"))

        # Copy the existing selected segment to a new one with the same beginning but
        # _eroded in the name, then erode the new one
        # ACTUALLY, we are going to need a whole new segmentation... because applying the
        # margin tool makes the volume that is changing EAT anything underneath it, so
        # the non-eroded segments will be hollowed out.

        # Make a new Segmentation Node
        newSegmentationNode = slicer.vtkMRMLSegmentationNode()  # create new segmetation
        oldSegmentationName = oldSegmentationNode.GetName()
        newSegmentationName = oldSegmentationName + '_eroded'  # TODO check if seg of this name already exists
        newSegmentationNode.SetName(newSegmentationName)
        newSegmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(volumeNode)
        slicer.mrmlScene.AddNode(newSegmentationNode)  # add to hierarchy

        # Don't show new segmentation in 3D (slows stuff down too much)
        newSegmentationNode.SetScene(slicer.mrmlScene)
        newSegmentationNode.CreateDefaultDisplayNodes()
        newSegmentationDisplayNode = newSegmentationNode.GetDisplayNode()
        newSegmentationDisplayNode.SetVisibility3D(False)
        # Actually, processing is speeded by not having anything visible by default, just turn on what you want to see...
        newSegmentationDisplayNode.SetVisibility(0)

        # Copy all existing segments from old to new segmentation
        # Iterate over old segments
        oldSegT = oldSegmentationNode.GetSegmentation()
        newSegT = newSegmentationNode.GetSegmentation()
        for segmentInd in range(oldSegT.GetNumberOfSegments()):
            segStartTime = now()
            oldSegM = oldSegT.GetNthSegment(segmentInd)
            newSegM = vtkSegmentationCore.vtkSegment()  # create new segment
            newSegM.DeepCopy(oldSegM)  # perform the copy
            newSegT.AddSegment(newSegM)
            printNow('Created new segment ' + newSegT.GetSegmentIdBySegment(newSegM))
            segFinishTime = now()
            segElapsedTime = segFinishTime - segStartTime  # a timedelta object
            printNow('It took ' + str(segElapsedTime))

        printNow('Creating segments took a total of ' + str(segFinishTime - startTime))

        #
        # Set up segment editor (to be able to access effects)
        #

        printNow('Setting up segment editor...')
        # Create segment editor to get access to effects
        segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
        # To show segment editor widget (useful for debugging): segmentEditorWidget.show()
        segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
        segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
        slicer.mrmlScene.AddNode(segmentEditorNode)
        segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
        segmentEditorWidget.setSegmentationNode(newSegmentationNode)
        # vols = slicer.util.getNodesByClass("vtkMRMLScalarVolumeNode")
        # volNode = vols[0] # TODO make this smarter, currently  just uses first volume on list
        segmentEditorWidget.setMasterVolumeNode(volumeNode)

        # Run segmentation effect
        segmentEditorWidget.setActiveEffectByName("Margin")
        effect = segmentEditorWidget.activeEffect()
        # You can change parameters by calling: effect.setParameter("MyParameterName", someValue)
        effect.setParameter("MarginSizeMm", -erosionDistance)

        #
        # Do Erosion
        #
        startErosionTime = now()
        for segmentInd in range(newSegT.GetNumberOfSegments()):
            segErodeStartTime = now()
            seg = newSegT.GetNthSegment(segmentInd)
            ID = newSegT.GetSegmentIdBySegment(seg)
            if ID == 'Other':
                effect.setParameter("MarginSizeMm", -otherErosionDistance)
            else:
                effect.setParameter("MarginSizeMm", -erosionDistance)
            segmentEditorWidget.setCurrentSegmentID(ID)
            if ID == 'BelowThresh':
                # don't actually erode, since it's just going to get cleared in the next step, and eroding it takes a long time
                pass
            else:  # actually do the erosion for all others
                effect.self().onApply()  # execute the effect
            segErodeFinishTime = now()
            printNow('Eroding ' + ID + ' took ' + str(segErodeFinishTime - segErodeStartTime))

        printNow('Cleaning up...')
        # Clean up
        slicer.mrmlScene.RemoveNode(segmentEditorNode)

        printNow('Total runErode time = ' + str(now() - startTime))
        return newSegmentationNode  # so it can be set in the selector
    
    def addSheathSegmentToHollowSegNode(self,hollowSegNode,volumeNode):
        # Add a transparent sheath segment to the supplied hollow segmentation node (for glassy heart views)
        # The sheath segment is the logical union of all the other segments (i.e. the bloodpool plus all of
        # its hollowed shells)

        ####### ONLY PARTIALLY WRITTEN!! #########
        
        sheathSegment = vtkSegmentationCore.vtkSegment()
        sheathSegment.SetName('Sheath')
        white = (1,1,1) # color
        sheathSegment.SetColor(white)
        hollowSegNode.GetSegmentation().AddSegment(sheathSegment)

        segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
        segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
        slicer.mrmlScene.AddNode(segmentEditorNode)
        segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
        segmentEditorWidget.setSegmentationNode(hollowSegNode)
        segmentEditorWidget.setMRMLScene(slicer.mrmlScene)  # If I do this early, I get an error...
        segmentEditorWidget.setMasterVolumeNode(volumeNode)
        segmentEditorNode.SetAndObserveMasterVolumeNode(volumeNode)
        segmentEditorNode.SetAndObserveSegmentationNode(hollowSegNode)

        # 
        segmentEditorWidget.setActiveEffectByName('Logical operators')
        effect = segmentEditorWidget.activeEffect()
        effect.setParameter("Operation", SegmentEditorEffects.LOGICAL_UNION)
        effect.setParameter("BypassMasking", 1)
        #
        segmentEditorNode.SetSelectedSegmentID(sheathSegment.GetName())
        # Do the segment addition to create the merged sheath segment
        segmentIDsToInclude = ('LA', 'LV', 'Aorta', 'RA', 'RV', 'PA', 'BloodPool')
        for segmentID in segmentIDsToInclude:
            effect.setParameter("ModifierSegmentID", segmentID)
            effect.self().onApply()
        # The bloodpool is included so that there isn't a distracting inner surface of the sheath
            
        # Clean up    
        slicer.mrmlScene.RemoveNode(segmentEditorNode)

        # Adjust Sheath segment visibility and transparency
        dispNode = hollowSegNode.GetDisplayNode()
        sheath3DOpacity = 0.1
        dispNode.SetSegmentOpacity3D(sheathSegment.GetName(),sheath3DOpacity)
        
        return hollowSegNode # which has been modified to include Sheath segment

    def exportAllToOBJ(self, outputPath, segNodeList,smoothingFactor=None,decimationFraction=None):
        # Loop over all segmentations in the list and export each to the supplied
        # output
        # TODO: if segNodeList contains a sequence (corresponding to a series of segmentations, do each of those)
        # ( note that there could be problems with this, maybe need sequence browser and step through it?)
        formatStr = 'OBJ'
        LPSflag = True
        sizeScale = 1.0  # double for scaling (not sure what this would be useful for)
        mergeFlag = False  # not used for OBJ format
        
        
        for segNode in segNodeList:
            segDispNode = segNode.GetDisplayNode()
            visibleSegmentIds = vtk.vtkStringArray()  # string array of segment IDs to include
            segDispNode.GetVisibleSegmentIDs(visibleSegmentIds)  # this somehow sets visibleSegmentIds
            logging.info('Processing ' + segNode.GetName())
            if (smoothingFactor is not None) or (decimationFraction is not None):
                # Caller wants to specify one or both of these factors, therefore they may not already be
                # set in the default conversion.  The existing representation needs to be removed and 
                # recreated with the new parameters
                if smoothingFactor is not None:
                    segNode.GetSegmentation().SetConversionParameter('Smoothing factor','%0.2f' % (smoothingFactor))
                if decimationFraction is not None:
                    segNode.GetSegmentation().SetConversionParameter('Decimation factor','%0.2f' % (decimationFraction))
                segNode.GetSegmentation().RemoveRepresentation(vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName())
                segNode.GetSegmentation().CreateRepresentation(vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName())
            slicer.vtkSlicerSegmentationsModuleLogic.ExportSegmentsClosedSurfaceRepresentationToFiles(outputPath,
                                                                                                      segNode,
                                                                                                      visibleSegmentIds,
                                                                                                      formatStr,
                                                                                                      LPSflag,
                                                                                                      sizeScale,
                                                                                                      mergeFlag)

        return

    def hollowToNewSeg(self, oldSegmentationNode, bloodPoolNameAndColor, volumeNode, thickness=5.0, LVthickness=15.0,
                       segmentIDsToInclude=('LA', 'LV', 'Aorta', 'RA', 'RV', 'PA')):
        # Steps are: 1) create new empty segmentation,
        # 2) copy 6 heart segments over (incl color)
        # 3) form merged BloodPool segment by making a new segment, and adding each of the 6 to it
        # 4) cycle over each heart seg and hollow with the right thickness (at least 5mm? needs to be at least 1 voxel)
        # 5) subtract the BloodPool segment from each hollowed segment.
        # Note that segments will overlap in space, is this a problem?
        # As currently structured, the segments overwrite each other when overlapping. This is controlled by the
        # "Overwrite other segments" choice in the "Masking" section.  The other option would be to have "Overwrite other
        # segments" set to "None", in which case the resulting hollowed segments will overlap.  Probably, I would want to
        # resolve the overlaps before making 3D model, so I'd have to choose which one I want to win anyway.  Seems better
        # for now to note that the order of segments will affect the outcome (later segments overwrite earlier segments
        # when they overlap).

        startTime = now()
        printNow(startTime.strftime("%I:%M:%S %p"))

        # Make a new Segmentation Node
        newSegmentationNode = slicer.vtkMRMLSegmentationNode()  # create new segmetation
        oldSegmentationName = oldSegmentationNode.GetName()
        newSegmentationName = 'hollow' + oldSegmentationName  # TODO check if seg of this name already exists
        newSegmentationNode.SetName(newSegmentationName)
        newSegmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(volumeNode) # FIXES BUG WHERE HOLLOWED SHELLS WERE CLIPPED TO EXTENT OF BLOOD POOL
        slicer.mrmlScene.AddNode(newSegmentationNode)  # add to hierarchy

        # Don't show new segmentation in 3D (slows stuff down too much)
        newSegmentationNode.SetScene(slicer.mrmlScene)
        newSegmentationNode.CreateDefaultDisplayNodes()
        # Turn off 3D view
        newSegmentationDisplayNode = newSegmentationNode.GetDisplayNode()
        newSegmentationDisplayNode.SetVisibility3D(False)
        newSegmentationDisplayNode.SetVisibility(0) # Just turn off all visibility by default

        # Copy all existing segments from old to new segmentation
        # Iterate over old segments
        oldSegT = oldSegmentationNode.GetSegmentation()
        newSegT = newSegmentationNode.GetSegmentation()
        for segmentInd in range(oldSegT.GetNumberOfSegments()):
            segStartTime = now()
            oldSegM = oldSegT.GetNthSegment(segmentInd)
            oldName = oldSegM.GetName()
            if (oldName in segmentIDsToInclude):
                newSegM = vtkSegmentationCore.vtkSegment()  # create new segment
                newSegM.DeepCopy(oldSegM)  # perform the copy
                newSegT.AddSegment(newSegM)
                printNow('Created new segment ' + newSegT.GetSegmentIdBySegment(newSegM))
                segFinishTime = now()
                segElapsedTime = segFinishTime - segStartTime  # a timedelta object
                printNow('It took ' + str(segElapsedTime))
            else:
                printNow(
                    'Skipped copying segment ' + oldName + ' because it doesn\'t match anything on the list of segment names to copy!')

        # printNow('Creating segments took a total of '+str(segFinishTime-startTime))

        #
        # Set up segment editor (to be able to access effects)
        #

        printNow('Setting up segment editor...')

        ## Do we need the widget, or can we get by with just the editor node?
        # It appears we might need the widget because of being able to get access to the effect via:
        # segmentEditorWidget.activeEffect()

        # Create segment editor to get access to effects
        segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
        # To show segment editor widget (useful for debugging):
        # segmentEditorWidget.show()
        # segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
        segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
        slicer.mrmlScene.AddNode(segmentEditorNode)
        segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
        segmentEditorWidget.setSegmentationNode(newSegmentationNode)
        segmentEditorWidget.setMRMLScene(slicer.mrmlScene)  # If I do this early, I get an error...
        segmentEditorWidget.setMasterVolumeNode(volumeNode)
        segmentEditorNode.SetAndObserveMasterVolumeNode(volumeNode)
        segmentEditorNode.SetAndObserveSegmentationNode(newSegmentationNode)

        # An issue was happening here which might be related to the newly created segment missing any kind of representation
        # or possibly a display issue as well.  A workaround which should be tried is to create the segment as a deep copy
        # of an existing segment and then update it's name and color and build it up from there.

        # Create blood pool segment
        bloodPoolSegM = vtkSegmentationCore.vtkSegment()  # Create new segment
        bloodPoolSegM.DeepCopy(
            oldSegT.GetNthSegment(0))  # Start off by deep copying an existing segment (shouldn't matter
        # which one).  The goal here is to carry along anything which might help properly initialize the segmentation (like
        # maybe the display properties, not sure what else)
        bloodPoolSegM.SetName(bloodPoolNameAndColor[0])  # Set name to 'BloodPool'
        bloodPoolSegM.SetColor(bloodPoolNameAndColor[1])  # Set color to red
        newSegT.AddSegment(bloodPoolSegM)  # Add it to new segmentation
        bloodPoolID = bloodPoolSegM.GetName()  # Same as ID? maybe not

        newSegmentationNode.CreateDefaultDisplayNodes()  # maybe need to do this again because of the new segment?

        segmentEditorWidget.setActiveEffectByName("Logical operators")

        effect = segmentEditorWidget.activeEffect()
        effect.setParameter("Operation", SegmentEditorEffects.LOGICAL_UNION)
        effect.setParameter("BypassMasking", 1)

        segmentEditorNode.SetSelectedSegmentID(bloodPoolID)  # SELECT the new BloodPool segment!!

        printNow('Creating BloodPool segment...')
        # segmentEditorWidget.show()
        # segmentEditorWidget.updateWidgetFromMRML()
        segmentEditorNode.SetSelectedSegmentID(bloodPoolID)

        for segmentID in segmentIDsToInclude:
            effect.setParameter("ModifierSegmentID", segmentID)
            effect.self().onApply()
        printNow('Finished creating BloodPool segment')
        #
        # Run hollowing effect
        #
        segmentEditorWidget.setActiveEffectByName("Hollow")
        effect = segmentEditorWidget.activeEffect()
        # You can change parameters by calling: effect.setParameter("MyParameterName", someValue)
        effect.setParameter("ShellMode", SegmentEditorEffects.INSIDE_SURFACE)
        # For hollowing, allow editing everywhere, but don't overwrite anything (allow overlapping objects)
        segmentEditorNode.SetMaskMode(slicer.vtkMRMLSegmentEditorNode.PaintAllowedEverywhere)
        # Changing approach: Set overwrite mode to none.  In this case, hollowed objects can overlap, and blood pool segment
        # needs to be subtracted.  However, an advantage is that if adjacent objects are turned off, it is clearer whether
        # an observed hole is part of the structure being examined rather than just a place where an adjacent structure
        # overwrote.
        segmentEditorNode.SetOverwriteMode(slicer.vtkMRMLSegmentEditorNode.OverwriteNone)

        startHollowTime = now()
        for segmentID in segmentIDsToInclude:
            startThisSegTime = now()
            # Select current segment as the one to modify
            segmentEditorNode.SetSelectedSegmentID(segmentID)
            if segmentID in 'LV':
                shellThickness = LVthickness
            else:
                shellThickness = thickness
            effect.setParameter("ShellThicknessMm", shellThickness)  # TODO: warn if this is too small!
            effect.self().onApply()
            printNow(
                'Hollowing ' + segmentID + ' took ' + str(now() - startThisSegTime) + ' with shell thickness ' + str(
                    shellThickness) + ' mm')
        printNow('Total hollowing time: ' + str(now() - startHollowTime))  # approx 30 sec

        ### Set up subtraction of blood pool
        segmentEditorWidget.setActiveEffectByName("Logical operators")
        effect = segmentEditorWidget.activeEffect()
        effect.setParameter("Operation", SegmentEditorEffects.LOGICAL_SUBTRACT)
        effect.setParameter("BypassMasking", 1)
        effect.setParameter("ModifierSegmentID",
                            bloodPoolID)  # blood pool is always the modifier, the one being subtracted
        startSubtractTime = now()
        for segmentID in segmentIDsToInclude:
            segmentEditorNode.SetSelectedSegmentID(segmentID)
            effect.self().onApply()
            printNow("Subtracted blood pool from " + segmentID)
        printNow('Total blood pool subtraction time: ' + str(now() - startSubtractTime))  # ~3 seconds

        printNow('Cleaning up...')
        # Clean up
        slicer.mrmlScene.RemoveNode(segmentEditorNode)

        printNow('Total hollowToNewSeg time = ' + str(now() - startTime))
        return newSegmentationNode  # so it can be set in the selector if desired

    '''
    Helper function to extract frames from a multivolume one by
    one and add each frame as a separate scalar volume to the scene.
    Input: multivolume node and a reference scalar volume node that should
    have the same geometry as the multivolume.
    '''

    def explodeMultivolume(mvName, refName):
        mv = slicer.util.getNode(mvName)
        ref = slicer.util.getNode(refName)  # it would be better if this could be extracted from the multivolume itelf
        mvi = mv.GetImageData()

        for i in range(mv.GetNumberOfFrames()):
            e0 = vtk.vtkImageExtractComponents()
            e0.SetInputData(mvi)
            e0.SetComponents(i)
            e0.Update()

        # clone reference
        frame = slicer.modules.volumes.logic().CloneVolume(slicer.mrmlScene, ref, 'frame' + str(i))
        # TODO it would great if somehow the cardiac phase information was not lost here
        frame.SetAndObserveImageData(e0.GetOutput())  # copies the extracted image data into the cloned reference volume

    ######## FUNCTIONS BELOW HERE AUTO-GENERATED AND NOT USED (just for reference)
    def hasImageData(self, volumeNode):
        """This is an example logic method that
        returns true if the passed in volume
        node has valid image data
        """
        if not volumeNode:
            logging.debug('hasImageData failed: no volume node')
            return False
        if volumeNode.GetImageData() is None:
            logging.debug('hasImageData failed: no image data in volume node')
            return False
        return True

    def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
        """Validates if the output is not the same as input
        """
        if not inputVolumeNode:
            logging.debug('isValidInputOutputData failed: no input volume node defined')
            return False
        if not outputVolumeNode:
            logging.debug('isValidInputOutputData failed: no output volume node defined')
            return False
        if inputVolumeNode.GetID() == outputVolumeNode.GetID():
            logging.debug(
                'isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
            return False
        return True

    def takeScreenshot(self, name, description, type=-1):
        # show the message even if not taking a screen shot
        slicer.util.delayDisplay(
            'Take screenshot: ' + description + '.\nResult is available in the Annotations module.', 3000)

        lm = slicer.app.layoutManager()
        # switch on the type to get the requested window
        widget = 0
        if type == slicer.qMRMLScreenShotDialog.FullLayout:
            # full layout
            widget = lm.viewport()
        elif type == slicer.qMRMLScreenShotDialog.ThreeD:
            # just the 3D window
            widget = lm.threeDWidget(0).threeDView()
        elif type == slicer.qMRMLScreenShotDialog.Red:
            # red slice window
            widget = lm.sliceWidget("Red")
        elif type == slicer.qMRMLScreenShotDialog.Yellow:
            # yellow slice window
            widget = lm.sliceWidget("Yellow")
        elif type == slicer.qMRMLScreenShotDialog.Green:
            # green slice window
            widget = lm.sliceWidget("Green")
        else:
            # default to using the full window
            widget = slicer.util.mainWindow()
            # reset the type so that the node is set correctly
            type = slicer.qMRMLScreenShotDialog.FullLayout

        # grab and convert to vtk image data
        qimage = ctk.ctkWidgetsUtils.grabWidget(widget)
        imageData = vtk.vtkImageData()
        slicer.qMRMLUtils().qImageToVtkImageData(qimage, imageData)

        annotationLogic = slicer.modules.annotations.logic()
        annotationLogic.CreateSnapShot(name, description, type, 1, imageData)


class PropagateSegToOtherPhasesTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_PropagateSegToOtherPhases1()

    def test_PropagateSegToOtherPhases1(self):
        """ Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")
        #
        # first, get some data
        #
        import urllib
        downloads = (
            ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

        for url, name, loader in downloads:
            filePath = slicer.app.temporaryPath + '/' + name
            if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
                logging.info('Requesting download %s from %s...\n' % (name, url))
                urllib.urlretrieve(url, filePath)
            if loader:
                logging.info('Loading %s...' % (name,))
                loader(filePath)
        self.delayDisplay('Finished with download and loading')

        volumeNode = slicer.util.getNode(pattern="FA")
        logic = PropagateSegToOtherPhasesLogic()
        self.assertIsNotNone(logic.hasImageData(volumeNode))
        self.delayDisplay('Test passed!')


def printNow(msg):
    # A wrapper for print() which flushes the buffer
    logging.info(msg)  # print(msg)
    # sys.stdout.flush()


def now():
    return datetime.datetime.now()
