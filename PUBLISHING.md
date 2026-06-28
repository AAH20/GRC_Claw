# Publishing GRC_Claw to npm

## First publish
1. Create an npm account and organization at npmjs.com
2. Run `npm login`
3. Create an npm automation token (type: Automation)
4. Add to GitHub repo secrets: Settings → Secrets → `NPM_TOKEN`

## Release a version
git tag v0.8.0
git push origin v0.8.0

The release.yml workflow fires automatically, builds all packages, and publishes to npm under the @grc-claw scope.

## Verify
npm view @grc-claw/sdk
npm view @grc-claw/cli

## Manual publish (emergency)
NPM_TOKEN=xxx npm publish --workspaces --access public
