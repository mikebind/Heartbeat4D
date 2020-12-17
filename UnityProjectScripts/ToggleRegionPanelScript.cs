using UnityEngine;
using System.Collections;

public class ToggleRegionPanelScript : MonoBehaviour {

    public void TogglePanel (GameObject panel) {
        panel.SetActive (!panel.activeSelf);
    }
}