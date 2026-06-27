package provider

import (
	"context"

	"github.com/hashicorp/terraform-plugin-sdk/v2/diag"
	"github.com/hashicorp/terraform-plugin-sdk/v2/helper/schema"
	"github.com/hashicorp/terraform-plugin-sdk/v2/plugin"
)

// New returns the provider factory function for use with plugin.Serve.
func New() *schema.Provider {
	return &schema.Provider{
		Schema: map[string]*schema.Schema{
			"api_url": {
				Type:        schema.TypeString,
				Required:    true,
				DefaultFunc: schema.EnvDefaultFunc("GRC_API_URL", "https://a2zsoc.com"),
				Description: "Base URL of the A2Z SOC GRC API (e.g. https://a2zsoc.com).",
			},
			"api_key": {
				Type:        schema.TypeString,
				Required:    true,
				Sensitive:   true,
				DefaultFunc: schema.EnvDefaultFunc("GRC_API_KEY", nil),
				Description: "API key used for Bearer token authentication.",
			},
		},
		ResourcesMap: map[string]*schema.Resource{
			"grc_control":  resourceControl(),
			"grc_evidence": resourceEvidence(),
		},
		ConfigureContextFunc: providerConfigure,
	}
}

// ProviderConfig holds the resolved provider-level configuration.
type ProviderConfig struct {
	APIURL string
	APIKey string
}

func providerConfigure(_ context.Context, d *schema.ResourceData) (interface{}, diag.Diagnostics) {
	cfg := &ProviderConfig{
		APIURL: d.Get("api_url").(string),
		APIKey: d.Get("api_key").(string),
	}
	return cfg, nil
}

// Serve is the entry-point called from main.go.
func Serve() {
	plugin.Serve(&plugin.ServeOpts{
		ProviderFunc: New,
	})
}
