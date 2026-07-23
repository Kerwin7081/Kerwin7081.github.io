# EnyaClawd · Kerwin Research Hub

This repository is the **public static output** for [enyaclawd.com](https://enyaclawd.com/).

It contains only material that is intended to be publicly served by the website:

- published HTML research pages;
- public CSS and browser-side JavaScript;
- public article metadata and homepage registry data;
- GitHub Pages deployment files;
- the `CNAME` custom-domain record.

## Repository boundary

The internal website-production system is **not stored here**.

- Public research methodology: `Kerwin7081/kerwin-signal-chain-research`
- Public website output: `Kerwin7081/Kerwin7081.github.io`
- Private production Skill: `Kerwin7081/kerwin-web`

Do not commit the following to this public repository:

- `kerwin-web` Skill files or internal prompts;
- credentials, API keys, tokens, cookies, or private URLs;
- client data, holdings, transactions, internal email, or private research notes;
- unpublished monitoring lists and internal operating procedures.

## Canonical visual system

The shared child-page assets implement the single EnyaClawd design system:

> Financial Times-inspired warm paper, restrained forest green, compact editorial typography, fine rules, and narrow long-form research layouts.

Compatibility asset paths:

- `assets/kerwin-system-v2.css`
- `assets/kerwin-system-v2.js`

The `v2` filename is retained for backward compatibility; it does not represent a competing visual system.

## Deployment

The site is deployed natively by GitHub Pages from the `main` branch and repository root. The root `.nojekyll` file disables Jekyll processing, and `CNAME` binds the custom domain. Every deployment must be verified at the custom domain before being described as live.
