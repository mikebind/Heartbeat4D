using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class UIManagerScript : MonoBehaviour
{
    GameObject[] pauseObjects;
    GameObject[] regionToggleObjs;
    GameObject arCamera;
    GameObject pointLight;
    int currentFrameIndex;
    public Slider frameSlider;
    public Text frameText;
    public Slider cutSlider;
    public float cutSliderMinSlideDist = 0.5f;
    public float cutSliderMaxSlideDist = 5f;
    public float pointLightDistFromClipPlane = 0.01f;
    //public GameObject segContainer;
    public Sprite[] modeSprites; // 3 slots for mode icons (solid, hollow, glassy)
    public int currentMode = 0;
    public Button modeButton;
    public Button toggleRegionPanelButton;
    public GameObject regionPanel;
    public Sprite[] playPauseSprites; // 2 slots (pause image, play image; should start on pause)
    public GameObject playPauseBackgroundObject; // slot for the "checkmark" image
    public Button cutSliderToggleButton; // slot for scissor button

    //public VisibilityControllerScript visibilityControllerScript;

    //private VisibilityControllerScript visibilityControllerScript;

    // Start is called before the first frame update
    void Start()
    {
        Time.timeScale = 1; // In-game time matches real time
        // Initialize list of objects which should only appear when the game is paused
        pauseObjects = GameObject.FindGameObjectsWithTag("ShowOnPause");
        // Hide all those objects, because the application doesn't start off paused
        hidePaused();


        arCamera = GameObject.FindGameObjectWithTag("MainCamera");
        pointLight = GameObject.FindGameObjectWithTag("PointLight");
        //GameObject segConObj = GameObject.Find("HollowSegContainer");
        //VisibilityControllerScript visibilityControllerScript= segConObj.GetComponent<VisibilityControllerScript>();
        Debug.Log("UIManagerScript.Start was reached");
        // Add listener for slider
        frameSlider.onValueChanged.AddListener(delegate { SliderValueChanged(); });

        cutSlider.onValueChanged.AddListener(delegate { CutSliderValueChanged(); });

        regionToggleObjs = GameObject.FindGameObjectsWithTag("RegionToggle");
        // Add listeners for changes in checkboxes
        for (int i = 0; i < regionToggleObjs.Length; i++)
        {
            regionToggleObjs[i].GetComponent<Toggle>().onValueChanged.AddListener(delegate { RegionCheckboxChanged(); });
        }

        // Add listener for mode button tap
        modeButton.onClick.AddListener(delegate { ModeChangeTap(); });

        // Add listener for RegionPanel toggle
        toggleRegionPanelButton.onClick.AddListener(delegate { ToggleRegionPanel(); });

        cutSliderToggleButton.onClick.AddListener(delegate { ToggleCutSlider(); });

        // Hide the region panel on startup
        ToggleRegionPanel();
        ToggleCutSlider(); // also hide cut slider
        // Play/Pause button
        

    }

    // Update is called once per frame
    void Update()
    {
        // Detect and handle pause via key press (for testing)
        if (Input.GetKeyDown(KeyCode.P))
        {
            if (Time.timeScale == 1)
            {
                Time.timeScale = 0;
                showPaused();
            }
            else if (Time.timeScale == 0)
            {
                Time.timeScale = 1;
                hidePaused();
            }
        }


        // Update UI if phase has changed
        // For some reason, it doesn't seem to work to put the following two lines in Start(), they seem to need to be redone here 


        //GameObject gameManager = transform.gameObject;
        VisibilityControllerScriptWithModes visibilityControllerScript = GetComponent<VisibilityControllerScriptWithModes>();
        //VisibilityControllerScript visibilityControllerScript= segConObj.GetComponent<VisibilityControllerScript>();
        if (visibilityControllerScript.currentFrameIndex != currentFrameIndex)
        {
            currentFrameIndex = visibilityControllerScript.currentFrameIndex;
            updateFrameSlider();
            updateFrameText();
        }
    }

    void updateFrameSlider()
    {
        // Set frame slider to current phase index;
        frameSlider.value = currentFrameIndex;
    }
    void updateFrameText()
    {
        frameText.text = currentFrameIndex.ToString();
    }

    void SliderValueChanged()
    {
        // Force user change of slider value to change the displayed phase
        int currentFrameIndex = (int)frameSlider.value;

        VisibilityControllerScriptWithModes visibilityControllerScript = GetComponent<VisibilityControllerScriptWithModes>();
        visibilityControllerScript.ChangeCurrentFrameIndex(currentFrameIndex);
    }

    void CutSliderValueChanged()
    {
        //Debug.Log("Reached CutSliderValueChanged");
        float cutSliderValue = cutSlider.value;
        float clipPlaneDistance = cutSliderMinSlideDist + cutSliderValue * (cutSliderMaxSlideDist - cutSliderMinSlideDist);
        UpdateClipPlaneAndPointLight(clipPlaneDistance);
    }

    void UpdateClipPlaneAndPointLight(float clipPlaneDistance)
    {
        // Set camera clipping plane, and move point light so that it is not clipped

        Camera cam = arCamera.GetComponent<Camera>();
        float oldClipPlane = cam.nearClipPlane;
        float clipPlaneChange = clipPlaneDistance - oldClipPlane;
        cam.nearClipPlane = clipPlaneDistance;

        Transform lightTrans = pointLight.GetComponent<Transform>();
        Transform camTrans = arCamera.GetComponent<Transform>();
        // The Z position of the pointLight needs to be greater than the nearClipPlane for it to not be clipped 
        lightTrans.localPosition = camTrans.localPosition + Vector3.forward * (clipPlaneDistance + pointLightDistFromClipPlane);

    }

    void ModeChangeTap()
    {
        // User tapped mode button
        currentMode = (currentMode + 1) % 3; // increment current mode
        Sprite newSpriteToChangeTo = modeSprites[currentMode];
        modeButton.GetComponent<Button>().GetComponent<Image>().sprite = newSpriteToChangeTo;

        // Also need to update the display!
        VisibilityControllerScriptWithModes visibilityControllerScript = GetComponent<VisibilityControllerScriptWithModes>();
        visibilityControllerScript.UpdateBecauseOfModeChange();

    }
    void RegionCheckboxChanged()
    {
        // Scan checkbox boolean values and apply them to _vis flags in visibility controller script  

        VisibilityControllerScriptWithModes visibilityControllerScript = GetComponent<VisibilityControllerScriptWithModes>();


        for (int ind = 0; ind < regionToggleObjs.Length; ind++)
        {
            // Find the corresponding visibility boolean flag and set it to match
            GameObject curToggleObj = regionToggleObjs[ind];
            Toggle ToggleComponent = curToggleObj.GetComponent<Toggle>();
            bool isChecked = ToggleComponent.isOn;
            string regionToggleName = curToggleObj.name;

            // Set the matching visibiility flag
            // NB: This is incredibily clunky and badly fragile, but it is the only easy way to structure it that I 
            // can figure out right now.  Ideally, there would be a much better way to ensure conformance between the 
            // checkbox being clicked and the visibility flag being set.  This method relies on a a fixed, hard-coded
            // ordering of the regions, as well as hard-coded names for the regions.  This should most certainly be 
            // refactored later!!!  TODO 
            // TODO TODO TODO!!
            // Update: Slightly better now, at least relies on name matching between name of toggle and visibility field name 
            switch (regionToggleName)
            {
                case "ToggleLA":
                    visibilityControllerScript.LA_vis = isChecked;
                    break;
                case "ToggleLV":
                    visibilityControllerScript.LV_vis = isChecked;
                    break;
                case "ToggleAorta":
                    visibilityControllerScript.Ao_vis = isChecked;
                    break;
                case "ToggleRA":
                    visibilityControllerScript.RA_vis = isChecked;
                    break;
                case "ToggleRV":
                    visibilityControllerScript.RV_vis = isChecked;
                    break;
                case "TogglePA":
                    visibilityControllerScript.PA_vis = isChecked;
                    break;
                default:
                    Debug.LogError("Did not match a case in region flag checking!");
                    break;
            }
        }
        // Trigger visibility update even if animation is currently paused 
        visibilityControllerScript.ChangeCurrentFrameIndex(currentFrameIndex);
    }

    public void ToggleCutSlider()
    {
        // Toggle visibility of the cut plane slider (should it also turn on/off point light?)
        if (cutSlider.gameObject.activeSelf)
        {
            // Currently visible; hide and set clipping plane to very close 0.01
            cutSlider.gameObject.SetActive(false);
            float clipPlaneDistance = 0.05f; // NB if <0.025, Merge Reticle shows up in middle of screen 
            UpdateClipPlaneAndPointLight(clipPlaneDistance);
            pointLight.SetActive(false);
        }
        else
        {
            // Currently not visible; show and set clipping plane based on slider value
            cutSlider.gameObject.SetActive(true);
            pointLight.SetActive(true);
            CutSliderValueChanged();
        }
    }

    public void ToggleRegionPanel()
    {
        // Toggle visibility of region panel (which contains region toggle checkboxes
        regionPanel.SetActive(!regionPanel.activeSelf);
    }

    public void pauseControl()
    {
        Image backgroundImage = playPauseBackgroundObject.GetComponent<Image>();
        if (Time.timeScale == 1)
        {
            Time.timeScale = 0;
            showPaused();
            backgroundImage.sprite = playPauseSprites[1]; // Change to play image
        }
        else if (Time.timeScale == 0)
        {
            Time.timeScale = 1;
            hidePaused();
            backgroundImage.sprite = playPauseSprites[0]; // Change to pause image
        }

    }

    public void showPaused()
    {
        foreach (GameObject g in pauseObjects)
        {
            g.SetActive(true);
        }
    }

    public void hidePaused()
    {
        foreach (GameObject g in pauseObjects)
        {
            g.SetActive(false);
        }
    }
}

