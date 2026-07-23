# EnyaClawd · Kerwin Research Hub

This repository is the **public static output** for `https://enyaclawd.com/`.

## Repository boundary

- Public research method: `Kerwin7081/kerwin-signal-chain-research`
- Public website output: `Kerwin7081/Kerwin7081.github.io`
- Private production system: `Kerwin7081/kerwin-web`

Do not commit private prompts, client data, holdings, internal notes, credentials, `.env` files, private Skill archives, or unpublished monitoring material to this repository.

## Production deployment

- Default branch: `main`
- Custom domain: `enyaclawd.com`
- Domain file: `CNAME`
- Pages source: GitHub Actions
- Canonical workflow: `.github/workflows/deploy-pages.yml`

The Pages workflow is intentionally source-only. It checks out the current repository, configures GitHub Pages, uploads the complete static site, and deploys it. It must not rewrite HTML, CSS, JavaScript, metadata, or links during deployment.

## Content structure

New directory-based reports use:

```text
<slug>/index.html
<slug>/meta.json
```

Homepage registration is maintained in `registry.json`. Every production entry should include a stable slug, title, date, summary, source, `homepage_approved`, and a Hong Kong ISO 8601 timestamp with `+08:00`.

## Asset policy

- Homepage assets are maintained under `assets/kerwin-home-*`.
- Public `assets/kerwin-system-v2.css` and `assets/kerwin-system-v2.js` are frozen legacy compatibility assets.
- Future FT warm-paper shared assets must use new `kerwin-system-v3.*` paths and be tested on a preview branch before any page migration.
- Do not overwrite public v2 files during ordinary article publishing.

## Safe publication checklist

1. Create or update the article and its metadata.
2. Update `registry.json` without removing concurrent entries.
3. Keep `CNAME`, Pages source, DNS, HTTPS and the canonical workflow unchanged.
4. Do not mix article content with shared CSS, JavaScript or infrastructure changes.
5. Audit the page for title, viewport, description, homepage route, disclaimer, internal links and mobile overflow.
6. Merge through a focused pull request.
7. Verify the homepage and the deepest new article URL on `enyaclawd.com`.

A successful commit or green workflow does not by itself prove that the custom domain is serving the expected version. Browser verification is the final release check.
