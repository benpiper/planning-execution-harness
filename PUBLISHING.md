# Publishing to Tessl

This guide walks you through claiming and promoting the planning-execution-harness skill on Tessl.

## Prerequisites

- Tessl account at https://tessl.io
- GitHub repository pushed and public
- Node.js 14+ installed

## Quick Start (5 steps)

### 1. Install Tessl CLI

```bash
npm install -g tessl
tessl --version
```

### 2. Import Your Skill

```bash
cd ~/planning-execution-harness
tessl skill import . --workspace <your-workspace>
```

This updates `tile.json` with Tessl metadata.

### 3. Validate Your Skill

```bash
tessl skill lint .
tessl skill review --optimize .
```

Both commands should pass without critical errors.

### 4. Create Tessl API Token

1. Go to https://tessl.io
2. Log in to your account
3. Navigate to **Settings** → **API Keys**
4. Click **Create New Key**
5. Choose "Skill Publishing" permission
6. Copy the token (save it safely)

### 5. Add GitHub Secret

1. Go to your GitHub repo: https://github.com/your-org/planning-execution-harness
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. **Name:** `TESSL_TOKEN`
5. **Value:** Paste your Tessl API token
6. Click **Add secret**

## Publishing Methods

### Method A: Automatic (Recommended)

Push to `main` and GitHub Actions automatically publishes:

```bash
cd ~/planning-execution-harness
git add .github/workflows/tessl-publish.yml
git commit -m "Add Tessl publishing workflow"
git push origin main
```

Check **Actions** tab in GitHub to see the workflow run.

### Method B: Manual from Local Machine

```bash
cd ~/planning-execution-harness
export TESSL_TOKEN="your-token-here"
tessl skill publish . --token $TESSL_TOKEN
```

## Verification

After publishing, verify your skill is live:

1. Visit https://tessl.io/registry
2. Search for "planning-execution-harness"
3. Check that:
   - ✅ Skill appears in registry
   - ✅ Title and description are clear
   - ✅ Download count > 0
   - ✅ Links to GitHub repo work

## Updating Your Skill

To update the published skill:

1. Make changes to `SKILL.md`, schemas, or examples
2. Increment version in `tile.json`:
   ```json
   {
     "version": "1.0.1"
   }
   ```
3. Push to GitHub
4. GitHub Actions automatically publishes the new version

## Promoting Your Skill

Once published, promote it:

### On Tessl Registry

- ✅ Add clear examples in SKILL.md
- ✅ Write evaluation scenarios
- ✅ Update description with keywords
- ✅ Link to GitHub repo in tile.json
- ✅ Request featured placement

### In Community

- 📢 Share on Twitter/X: "Check out planning-execution-harness on Tessl!"
- 🔗 Link from blog posts, docs
- 💬 Discuss in Tessel Discord/community
- 📝 Write about the architecture

## Troubleshooting

### "Skill not found" after publishing

Wait 2-3 minutes for indexing, then refresh https://tessl.io/registry.

### "Invalid token"

- Verify `TESSL_TOKEN` secret is set in GitHub Settings
- Check token hasn't expired in Tessl web UI
- Ensure no extra spaces in token

### "SKILL.md validation failed"

Check:
- `SKILL.md` frontmatter is valid YAML
- Required fields: `name`, `description`
- Markdown syntax is correct

Use linter:
```bash
tessl skill lint .
```

### GitHub Actions workflow not running

Check:
- Workflow file is in `.github/workflows/`
- File has `.yml` extension
- Push included one of the trigger paths:
  - `SKILL.md`
  - `tile.json`
  - `examples/`
  - `schemas/`
  - `contracts/`

### Want to claim an existing skill?

If Tessl auto-indexed your repo before you formally published:

1. Go to https://tessl.io/registry
2. Find your skill (may be under different workspace)
3. Click "Claim this skill"
4. Follow the workspace assignment steps

This ensures you're listed as owner in the registry.

## tile.json Reference

Your optimized `tile.json` will look like:

```json
{
  "name": "benpiper-workspace/planning-execution-harness",
  "version": "0.2.0",
  "private": false,
  "summary": "Use when you need to architect a multi-language, language-agnostic system...",
  "skills": {
    "planning-execution-harness": {
      "path": "SKILL.md"
    }
  }
}
```

Key fields (auto-optimized by Tessl):
- `name` — Workspace-qualified identifier (tessl adds your workspace)
- `version` — SemVer (auto-updated on publish)
- `summary` — From SKILL.md frontmatter description
- `private` — false to publish publicly
- `skills` — Path to SKILL.md file

## SKILL.md Frontmatter

Your `SKILL.md` should start with:

```yaml
---
name: planning-execution-harness
description: Use when you need to architect a multi-language system that separates high-level planning from low-level execution with gating, recovery, and permission control.
---
```

Critical for discovery:
- `description` must include "Use when..." for agent activation
- Be specific about trigger terms
- Keep it under 160 characters for display

## Next Steps

1. **Get Tessl token** (see step 4 above)
2. **Add GitHub secret** (see step 5 above)
3. **Push the workflow file:**
   ```bash
   git add .github/workflows/tessl-publish.yml
   git commit -m "Add Tessl publishing workflow"
   git push origin main
   ```
4. **Check GitHub Actions** for successful publish
5. **Verify on registry** at https://tessl.io/registry

## Resources

- **Tessl Docs**: https://docs.tessl.io
- **Publishing Guide**: https://docs.tessl.io/distribute/promote-or-claim-a-skill-you-have-created
- **Registry**: https://tessl.io/registry
- **Community**: https://discord.gg/tessl (if available)

---

Your skill is ready to share with the world! 🚀
