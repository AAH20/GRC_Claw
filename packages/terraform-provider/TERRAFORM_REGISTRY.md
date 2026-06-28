# Publishing to the Terraform Registry

## Prerequisites
1. Create account at registry.terraform.io
2. Connect your GitHub account
3. Generate a GPG key pair for release signing
4. Add to GitHub secrets:
   - GPG_PRIVATE_KEY (exported private key)
   - PASSPHRASE (GPG passphrase)

## Register the provider
1. Go to registry.terraform.io/publish/provider
2. Select github.com/AAH20/GRC_Claw
3. The registry auto-discovers releases tagged terraform-v*

## Release
git tag terraform-v0.8.0
git push origin terraform-v0.8.0

goreleaser builds cross-platform binaries, signs with GPG, publishes to GitHub Releases.
The Terraform Registry picks up the release within minutes.

## Usage after publish
terraform {
  required_providers {
    grc = {
      source  = "a2zsoc/grc"
      version = "~> 0.8"
    }
  }
}
