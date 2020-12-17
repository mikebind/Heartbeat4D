using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class VisibilityControllerScript : MonoBehaviour {
    public GameObject[] solidSegFrames;
	public List<GameObject> phaseList;
	private GameObject currentPhaseGroup;
	public int startingPhaseIndex=0;
	public int currentPhaseIndex=0;
	public bool animatingFlag = false;
	public bool LA_vis=true, LV_vis=true, Ao_vis = true, RA_vis = true, RV_vis = true, PA_vis = true;
    private List<bool> regionFlags;
    public bool pausedInControlFlag = false;
	public float timeInterval=0.25f; // time in seconds between updates
    private float timeLeft;
    //public Material testMaterial;
	



    // Use this for initialization
    void Start () {
        // Initialize Materials 

		// Initialize regionFlags
		regionFlags = new List<bool>();
		for (int i = 0; i<6; i++){
			regionFlags.Add(true);
		}
		MakeOnlyCurrentPhaseVisible();
		
		timeLeft = timeInterval;
		Debug.Log("Finished Start()");
		print("First phase should be visible");
	}
	
	// Update is called once per frame
	void Update () {
		/* If animating, and time to update: set all regions in current phase invisible
		update current phase, and set each region with enabled regionFlag to visible, reset update timer */
		if (animatingFlag && timeLeft<0.0f){
			// Next phase
			currentPhaseIndex++;
			if (currentPhaseIndex > phaseList.Count-1){
				currentPhaseIndex = 0;
			}
			// Make enabled regions of next phase visible
			MakeOnlyCurrentPhaseVisible();

			// Reset Time Left to next update
			timeLeft = timeInterval;

		}
		timeLeft -= Time.deltaTime; 
	}
	void UpdateRegionFlags(){
		regionFlags[0] = LA_vis;
		regionFlags[1] = LV_vis;
		regionFlags[2] = Ao_vis;
		regionFlags[3] = RA_vis;
		regionFlags[4] = RV_vis;
		regionFlags[5] = PA_vis;
	}
	void MakePhaseInvisible(){
		Debug.Log("Entered MakePhaseInvisible...");
		int childCount = currentPhaseGroup.transform.childCount;
		MeshRenderer meshRend;
		// Loop over all children
		for (int childInd = 0; childInd<childCount; childInd++){
			// Get child transform object (Scene hierarchies are stored by transforms)
			Transform childTrans = currentPhaseGroup.transform.GetChild(childInd);
			// Get child object (one of the heart regions)
			GameObject child = childTrans.gameObject;
			// Get the associated mesh renderer
			meshRend = child.GetComponent<MeshRenderer>();
			// Disable to make it invisible
			meshRend.enabled = false;
		}
	}

	void MakePhaseVisibile(){
		Debug.Log("Entered MakePhaseVisible...");
		for (int childInd=0; childInd<6; childInd++){
			if (regionFlags[childInd]){
				// Get child transform object (Scene hierarchies are stored by transforms)
				Transform childTrans = currentPhaseGroup.transform.GetChild(childInd);
				// Get child object (one of the heart regions)
				GameObject child = childTrans.gameObject;
				// Get the associated mesh renderer
				MeshRenderer meshRend = child.GetComponent<MeshRenderer>();
				// Disable to make it visible
				meshRend.enabled = true;
                //meshRend.material = testMaterial; // just testing
			}
		}

	}

	void MakeOnlyCurrentPhaseVisible(){
		// Make all phases invisible, then make current phase visible
		UpdateRegionFlags();
		// Make everything invisible
		for (int phaseInd=0; phaseInd<phaseList.Count; phaseInd++){
			currentPhaseGroup = phaseList[phaseInd];
			MakePhaseInvisible();
		}
		// Make current phase visible
		currentPhaseGroup = phaseList[currentPhaseIndex];
		MakePhaseVisibile();
	}

	public void ChangeCurrentPhaseIndex(int newPhaseIndex){
		Debug.Log("Entered ChangeCurrentPhaseIndex...");
		currentPhaseIndex = newPhaseIndex;
		MakeOnlyCurrentPhaseVisible();

	}
}
