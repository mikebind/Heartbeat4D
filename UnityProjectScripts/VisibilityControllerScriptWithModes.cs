using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Assertions;


public class VisibilityControllerScriptWithModes : MonoBehaviour
{
    // Create slots for game objects which are parents of all solid segmentations and hollow segmentations
    public GameObject SolidSegContainer; //parent object which contains solid segmentation frames, in order
    public GameObject HollowSegContainer; // same for hollow segmentation frames, in order. These also contain the merged bloodpool and glassy sheath objects
    public Material[] materialsList; // in order, LA,LV,Ao,RA,RV,PA,BloodPool,Sheath,Other
    //private List<GameObject> phaseList;
    //private GameObject currentPhaseGroup;
    private int frameCount;
    public int startingFrameIndex = 0;
    public int currentFrameIndex = 0;
    public bool animatingFlag = false;
    public bool LA_vis = true, LV_vis = true, Ao_vis = true, RA_vis = true, RV_vis = true, PA_vis = true;
    private List<bool> regionFlags;
    public bool pausedInControlFlag = false;
    public float timeInterval = 0.25f; // time in seconds between updates
    private float timeLeft;
    public int currentMode = 0;




    // Use this for initialization
    void Start()
    {
        // Initialize Materials 
        // loop over all solid segmentations and apply the appropriate material
        
        frameCount = SolidSegContainer.transform.childCount;
        for (int frameInd = 0; frameInd < frameCount; frameInd++)
        {
            // Get child transform object (Scene hierarchies are stored by transforms)
            Transform frameTrans = SolidSegContainer.transform.GetChild(frameInd);
            int regCount = frameTrans.transform.childCount;
            for (int regInd=0; regInd<regCount; regInd++)
            {
                Transform regTrans = frameTrans.transform.GetChild(regInd);
                GameObject reg = regTrans.gameObject;
                MeshRenderer meshRend = reg.GetComponent<MeshRenderer>();
                if (regInd == 6)
                {
                    //"Other"
                    meshRend.material = materialsList[8]; // the yellow "other" material is #8
                    meshRend.enabled = false; // Also hide these on initialization (currently no controls to show this either, but those could be added if desired)
                }
                else
                {
                    // The rest of the materials can be assigned by index
                    meshRend.material = materialsList[regInd];
                }
                
            }
        }
        int hollowFrameCount = HollowSegContainer.transform.childCount;
        Assert.AreEqual(hollowFrameCount, frameCount); // the # of phases must match 

        // Loop over all hollow segs and assign materials
        for (int frameInd = 0; frameInd<hollowFrameCount; frameInd++)
        {
            Transform frameTrans = HollowSegContainer.transform.GetChild(frameInd);
            int regCount = frameTrans.transform.childCount;
            for (int regInd = 0; regInd < regCount; regInd++)
            {
                Transform regTrans = frameTrans.transform.GetChild(regInd);
                GameObject reg = regTrans.gameObject;
                MeshRenderer meshRend = reg.GetComponent<MeshRenderer>();
                meshRend.material = materialsList[regInd];
            }
        }


        // Initialize regionFlags
        regionFlags = new List<bool>();
        for (int i = 0; i < 6; i++)
        {
            regionFlags.Add(true);
        }
        MakeOnlyCurrentPhaseVisible();

        timeLeft = timeInterval;
        Debug.Log("Finished Start()");
        print("First phase should be visible");
    }

    // Update is called once per frame
    void Update()
    {
        /* If animating, and time to update: set all regions in current phase invisible
        update current phase, and set each region with enabled regionFlag to visible, reset update timer */
        if (animatingFlag && timeLeft < 0.0f)
        {
            // Next phase
            currentFrameIndex++;
            if (currentFrameIndex > frameCount - 1)
            {
                currentFrameIndex = 0;
            }
            // Make enabled regions of next phase visible
            MakeOnlyCurrentPhaseVisible();

            // Reset Time Left to next update
            timeLeft = timeInterval;

        }
        timeLeft -= Time.deltaTime;
    }
    void UpdateRegionFlags()
    {
        regionFlags[0] = LA_vis;
        regionFlags[1] = LV_vis;
        regionFlags[2] = Ao_vis;
        regionFlags[3] = RA_vis;
        regionFlags[4] = RV_vis;
        regionFlags[5] = PA_vis;
    }
    void MakePhaseInvisible()
    {
        Debug.Log("Entered MakePhaseInvisible...");
        HideAll(HollowSegContainer);
        HideAll(SolidSegContainer);
        /*
        int childCount = currentPhaseGroup.transform.childCount;
        MeshRenderer meshRend;
        // Loop over all children
        for (int childInd = 0; childInd < childCount; childInd++)
        {
            // Get child transform object (Scene hierarchies are stored by transforms)
            Transform childTrans = currentPhaseGroup.transform.GetChild(childInd);
            // Get child object (one of the heart regions)
            GameObject child = childTrans.gameObject;
            // Get the associated mesh renderer
            meshRend = child.GetComponent<MeshRenderer>();
            // Disable to make it invisible
            meshRend.enabled = false;
        }
        */
    }

    void MakePhaseVisibile()
    {
        // Branch based on mode
        int mode = GetCurrentMode();
        if (mode == 0) // SOLID COLORED
        {
            // Solid colored segmentation  (show solidSeg, hide hollowSeg; respect regionFlags)
            HideAll(HollowSegContainer);
            Transform currentSolidSegFrame = SolidSegContainer.transform.GetChild(currentFrameIndex);
            // Loop over 1st 6 regions
            for (int childInd = 0; childInd < 6; childInd++)
            {
                if (regionFlags[childInd])
                {
                    // Get child transform object (Scene hierarchies are stored by transforms)
                    Transform childTrans = currentSolidSegFrame.transform.GetChild(childInd);
                    // Get child object (one of the heart regions)
                    GameObject child = childTrans.gameObject;
                    // Get the associated mesh renderer
                    MeshRenderer meshRend = child.GetComponent<MeshRenderer>();
                    // Enable to make it visible
                    meshRend.enabled = true;
                }
            }
        }
        else if (mode == 1) // HOLLOW COLORED
        {
            // Hollow colored segmentation (show hollowSeg, hide solidSeg; respect regionFlags; hide bloodpool and sheath)
            HideAll(SolidSegContainer);
            Transform currentHollowSegFrame = HollowSegContainer.transform.GetChild(currentFrameIndex);
            // Loop over 1st 6 regions
            for (int childInd = 0; childInd < 6; childInd++)
            {
                if (regionFlags[childInd])
                {
                    // Get child transform object (Scene hierarchies are stored by transforms)
                    Transform childTrans = currentHollowSegFrame.transform.GetChild(childInd);
                    // Get child object (one of the heart regions)
                    GameObject child = childTrans.gameObject;
                    // Get the associated mesh renderer
                    MeshRenderer meshRend = child.GetComponent<MeshRenderer>();
                    // Enable to make it visible
                    meshRend.enabled = true;
                }
            }
            // Hide bloodpool and sheath
            for (int childInd=6; childInd<8; childInd++)
            {
                Transform childTrans = currentHollowSegFrame.transform.GetChild(childInd);
                childTrans.gameObject.GetComponent<MeshRenderer>().enabled = false; // hide
            }
        }
        else if (mode > 1) // GLASSY BLOODPOOL
        {
            // Glassy bloodpool version (hide solidSeg, hide hollowSeg regions; ignore regionFlags; show bloodpool and sheath)
            HideAll(SolidSegContainer);
            Transform currentHollowSegFrame = HollowSegContainer.transform.GetChild(currentFrameIndex);
            // Hide 1st 6 regions
            for (int childInd = 0; childInd < 6; childInd++)
            {
                Transform childTrans = currentHollowSegFrame.transform.GetChild(childInd);
                childTrans.gameObject.GetComponent<MeshRenderer>().enabled = false; // hide
            }
            // Show 7 & 8
            for (int childInd = 6; childInd < 8; childInd++)
            {
                Transform childTrans = currentHollowSegFrame.transform.GetChild(childInd);
                childTrans.gameObject.GetComponent<MeshRenderer>().enabled = true; // show
            }
        }
        /*
        Debug.Log("Entered MakePhaseVisible...");
        for (int childInd = 0; childInd < 6; childInd++)
        {
            if (regionFlags[childInd])
            {
                // Get child transform object (Scene hierarchies are stored by transforms)
                Transform childTrans = currentPhaseGroup.transform.GetChild(childInd);
                // Get child object (one of the heart regions)
                GameObject child = childTrans.gameObject;
                // Get the associated mesh renderer
                MeshRenderer meshRend = child.GetComponent<MeshRenderer>();
                // Disable to make it visible
                meshRend.enabled = true;
            }
        }
        */
 
    }

    void MakeOnlyCurrentPhaseVisible()
    {
        // Make all phases invisible, then make current phase visible
        UpdateRegionFlags();
        // Make everything invisible
        HideAll(HollowSegContainer);
        HideAll(SolidSegContainer);
        /*
        for (int phaseInd = 0; phaseInd < phaseList.Count; phaseInd++)
        {
            currentPhaseGroup = phaseList[phaseInd];
            MakePhaseInvisible();
        }
        // Make current phase visible
        currentPhaseGroup = phaseList[currentFrameIndex];
        */
        MakePhaseVisibile();
    }

    public void UpdateBecauseOfModeChange()
    {
        // Called from UIManagerScript when after mode change tap
        MakeOnlyCurrentPhaseVisible();
    }
    public void ChangeCurrentFrameIndex(int newFrameIndex)
    {
        Debug.Log("Entered ChangeCurrentFrameIndex...");
        currentFrameIndex = newFrameIndex;
        MakeOnlyCurrentPhaseVisible();

    }

    int GetCurrentMode()
    {
        // Needs code to obtain and return the currentMode from UIManagerScript
        UIManagerScript uIManagerScript = GetComponent<UIManagerScript>();
        int mode = uIManagerScript.currentMode;
        return mode;
    }

    void HideAll(GameObject container)
    {
        foreach(Transform frameTrans in container.transform)
        {
            foreach (Transform regTrans in frameTrans)
            {
                GameObject reg = regTrans.gameObject;
                reg.GetComponent<MeshRenderer>().enabled = false;
            }
        }
    }
    
}

