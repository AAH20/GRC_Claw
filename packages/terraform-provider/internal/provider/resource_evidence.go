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

func resourceEvidence() *schema.Resource {
	return &schema.Resource{
		Description:   "Manages an evidence record in the A2Z SOC proof ledger.",
		CreateContext: resourceEvidenceCreate,
		ReadContext:   resourceEvidenceRead,
		UpdateContext: resourceEvidenceUpdate,
		DeleteContext: resourceEvidenceDelete,
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
			"control_id": {
				Type:        schema.TypeString,
				Required:    true,
				ForceNew:    true,
				Description: "Control identifier this evidence supports (e.g. CC6.1).",
			},
			"evidence_type": {
				Type:     schema.TypeString,
				Required: true,
				ValidateFunc: validation.StringInSlice(
					[]string{"screenshot", "log", "report", "policy", "attestation", "other"}, false,
				),
				Description: "Type of evidence artifact.",
			},
			"description": {
				Type:        schema.TypeString,
				Required:    true,
				Description: "Human-readable description of the evidence.",
			},
			"file_url": {
				Type:        schema.TypeString,
				Optional:    true,
				Description: "URL to the evidence artifact (screenshot, log export, PDF, etc.).",
			},
			"recorded_at": {
				Type:        schema.TypeString,
				Optional:    true,
				Computed:    true,
				Description: "ISO 8601 timestamp when the evidence was recorded (defaults to server time if omitted).",
			},
		},
	}
}

// evidencePayload is the JSON body sent to the proof-ledger API.
type evidencePayload struct {
	OrgSlug      string `json:"org_slug"`
	ControlID    string `json:"control_id"`
	EvidenceType string `json:"evidence_type"`
	Description  string `json:"description"`
	FileURL      string `json:"file_url,omitempty"`
	RecordedAt   string `json:"recorded_at,omitempty"`
}

func evidenceEndpoint(apiURL string) string {
	return fmt.Sprintf("%s/api/platform/proof-ledger", apiURL)
}

func resourceEvidenceCreate(ctx context.Context, d *schema.ResourceData, meta interface{}) diag.Diagnostics {
	cfg := meta.(*ProviderConfig)

	payload := evidencePayload{
		OrgSlug:      d.Get("org_slug").(string),
		ControlID:    d.Get("control_id").(string),
		EvidenceType: d.Get("evidence_type").(string),
		Description:  d.Get("description").(string),
		FileURL:      d.Get("file_url").(string),
		RecordedAt:   d.Get("recorded_at").(string),
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return diag.FromErr(err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, evidenceEndpoint(cfg.APIURL), bytes.NewBuffer(body))
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
		return diag.Errorf("API returned status %d when creating grc_evidence", resp.StatusCode)
	}

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return diag.FromErr(err)
	}

	id, ok := result["id"].(string)
	if !ok {
		id = fmt.Sprintf("%s/%s/%s", payload.OrgSlug, payload.ControlID, payload.EvidenceType)
	}
	d.SetId(id)

	return resourceEvidenceRead(ctx, d, meta)
}

func resourceEvidenceRead(ctx context.Context, d *schema.ResourceData, meta interface{}) diag.Diagnostics {
	cfg := meta.(*ProviderConfig)

	url := fmt.Sprintf("%s/%s", evidenceEndpoint(cfg.APIURL), d.Id())
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
		return diag.Errorf("API returned status %d when reading grc_evidence %s", resp.StatusCode, d.Id())
	}

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return diag.FromErr(err)
	}

	setStringIfPresent(d, "org_slug", result, "org_slug")
	setStringIfPresent(d, "control_id", result, "control_id")
	setStringIfPresent(d, "evidence_type", result, "evidence_type")
	setStringIfPresent(d, "description", result, "description")
	setStringIfPresent(d, "file_url", result, "file_url")
	setStringIfPresent(d, "recorded_at", result, "recorded_at")

	return nil
}

func resourceEvidenceUpdate(ctx context.Context, d *schema.ResourceData, meta interface{}) diag.Diagnostics {
	cfg := meta.(*ProviderConfig)

	payload := evidencePayload{
		OrgSlug:      d.Get("org_slug").(string),
		ControlID:    d.Get("control_id").(string),
		EvidenceType: d.Get("evidence_type").(string),
		Description:  d.Get("description").(string),
		FileURL:      d.Get("file_url").(string),
		RecordedAt:   d.Get("recorded_at").(string),
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return diag.FromErr(err)
	}

	url := fmt.Sprintf("%s/%s", evidenceEndpoint(cfg.APIURL), d.Id())
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
		return diag.Errorf("API returned status %d when updating grc_evidence %s", resp.StatusCode, d.Id())
	}

	return resourceEvidenceRead(ctx, d, meta)
}

func resourceEvidenceDelete(ctx context.Context, d *schema.ResourceData, meta interface{}) diag.Diagnostics {
	cfg := meta.(*ProviderConfig)

	url := fmt.Sprintf("%s/%s", evidenceEndpoint(cfg.APIURL), d.Id())
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
		return diag.Errorf("API returned status %d when deleting grc_evidence %s", resp.StatusCode, d.Id())
	}

	d.SetId("")
	return nil
}
