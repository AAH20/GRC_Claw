package provider

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/hashicorp/terraform-plugin-sdk/v2/diag"
	"github.com/hashicorp/terraform-plugin-sdk/v2/helper/schema"
	"github.com/hashicorp/terraform-plugin-sdk/v2/helper/validation"
)

func resourceControl() *schema.Resource {
	return &schema.Resource{
		Description:   "Manages a GRC control record in the A2Z SOC platform.",
		CreateContext: resourceControlCreate,
		ReadContext:   resourceControlRead,
		UpdateContext: resourceControlUpdate,
		DeleteContext: resourceControlDelete,
		Importer: &schema.ResourceImporter{
			StateContext: schema.ImportStatePassthroughContext,
		},
		Schema: map[string]*schema.Schema{
			"org_slug": {
				Type:        schema.TypeString,
				Required:    true,
				ForceNew:    true,
				Description: "Organization slug (e.g. acme-corp).",
			},
			"framework": {
				Type:        schema.TypeString,
				Required:    true,
				Description: "Compliance framework identifier (e.g. soc2, iso27001, hipaa).",
			},
			"control_id": {
				Type:        schema.TypeString,
				Required:    true,
				Description: "Framework-specific control identifier (e.g. CC6.1).",
			},
			"title": {
				Type:        schema.TypeString,
				Required:    true,
				Description: "Human-readable title of the control.",
			},
			"status": {
				Type:     schema.TypeString,
				Required: true,
				ValidateFunc: validation.StringInSlice(
					[]string{"compliant", "non_compliant", "not_applicable"}, false,
				),
				Description: "Compliance status: compliant | non_compliant | not_applicable.",
			},
			"evidence_url": {
				Type:        schema.TypeString,
				Optional:    true,
				Description: "URL to supporting evidence for this control.",
			},
		},
	}
}

// controlPayload is the JSON body sent to the API.
type controlPayload struct {
	OrgSlug     string `json:"org_slug"`
	Framework   string `json:"framework"`
	ControlID   string `json:"control_id"`
	Title       string `json:"title"`
	Status      string `json:"status"`
	EvidenceURL string `json:"evidence_url,omitempty"`
}

func controlEndpoint(apiURL string) string {
	return fmt.Sprintf("%s/api/platform/grc", apiURL)
}

func resourceControlCreate(ctx context.Context, d *schema.ResourceData, meta interface{}) diag.Diagnostics {
	cfg := meta.(*ProviderConfig)

	payload := controlPayload{
		OrgSlug:     d.Get("org_slug").(string),
		Framework:   d.Get("framework").(string),
		ControlID:   d.Get("control_id").(string),
		Title:       d.Get("title").(string),
		Status:      d.Get("status").(string),
		EvidenceURL: d.Get("evidence_url").(string),
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return diag.FromErr(err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, controlEndpoint(cfg.APIURL), bytes.NewBuffer(body))
	if err != nil {
		return diag.FromErr(err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+cfg.APIKey)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return diag.FromErr(err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 300 {
		return diag.Errorf("API returned status %d when creating grc_control", resp.StatusCode)
	}

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return diag.FromErr(err)
	}

	id, ok := result["id"].(string)
	if !ok {
		// Fall back to a composite key if the API doesn't return an id.
		id = fmt.Sprintf("%s/%s/%s", payload.OrgSlug, payload.Framework, payload.ControlID)
	}
	d.SetId(id)

	return resourceControlRead(ctx, d, meta)
}

func resourceControlRead(ctx context.Context, d *schema.ResourceData, meta interface{}) diag.Diagnostics {
	cfg := meta.(*ProviderConfig)

	url := fmt.Sprintf("%s/%s", controlEndpoint(cfg.APIURL), d.Id())
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return diag.FromErr(err)
	}
	req.Header.Set("Authorization", "Bearer "+cfg.APIKey)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return diag.FromErr(err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		d.SetId("")
		return nil
	}
	if resp.StatusCode >= 300 {
		return diag.Errorf("API returned status %d when reading grc_control %s", resp.StatusCode, d.Id())
	}

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return diag.FromErr(err)
	}

	setStringIfPresent(d, "org_slug", result, "org_slug")
	setStringIfPresent(d, "framework", result, "framework")
	setStringIfPresent(d, "control_id", result, "control_id")
	setStringIfPresent(d, "title", result, "title")
	setStringIfPresent(d, "status", result, "status")
	setStringIfPresent(d, "evidence_url", result, "evidence_url")

	return nil
}

func resourceControlUpdate(ctx context.Context, d *schema.ResourceData, meta interface{}) diag.Diagnostics {
	cfg := meta.(*ProviderConfig)

	payload := controlPayload{
		OrgSlug:     d.Get("org_slug").(string),
		Framework:   d.Get("framework").(string),
		ControlID:   d.Get("control_id").(string),
		Title:       d.Get("title").(string),
		Status:      d.Get("status").(string),
		EvidenceURL: d.Get("evidence_url").(string),
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return diag.FromErr(err)
	}

	url := fmt.Sprintf("%s/%s", controlEndpoint(cfg.APIURL), d.Id())
	req, err := http.NewRequestWithContext(ctx, http.MethodPut, url, bytes.NewBuffer(body))
	if err != nil {
		return diag.FromErr(err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+cfg.APIKey)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return diag.FromErr(err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 300 {
		return diag.Errorf("API returned status %d when updating grc_control %s", resp.StatusCode, d.Id())
	}

	return resourceControlRead(ctx, d, meta)
}

func resourceControlDelete(ctx context.Context, d *schema.ResourceData, meta interface{}) diag.Diagnostics {
	cfg := meta.(*ProviderConfig)

	url := fmt.Sprintf("%s/%s", controlEndpoint(cfg.APIURL), d.Id())
	req, err := http.NewRequestWithContext(ctx, http.MethodDelete, url, nil)
	if err != nil {
		return diag.FromErr(err)
	}
	req.Header.Set("Authorization", "Bearer "+cfg.APIKey)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return diag.FromErr(err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 300 && resp.StatusCode != http.StatusNotFound {
		return diag.Errorf("API returned status %d when deleting grc_control %s", resp.StatusCode, d.Id())
	}

	d.SetId("")
	return nil
}

// setStringIfPresent is a helper to safely set string attributes from API responses.
func setStringIfPresent(d *schema.ResourceData, attr string, m map[string]interface{}, key string) {
	if v, ok := m[key].(string); ok {
		_ = d.Set(attr, v)
	}
}
