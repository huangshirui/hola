# Project instructions

- This is a Spanish practice web app for Chinese-speaking children.
- Keep all frontend deployable files in `dist/`; keep Worker API code in `worker/` and deployment configuration in `wrangler.jsonc`.
- Cloudflare Workers Static Assets serves the frontend; Worker code should handle only `/api/*` unless there is an explicit reason to change routing.
- No frontend build step is required.
- Production deployment is handled by Cloudflare Workers Builds connected to GitHub `main`; do not add a GitHub Actions deployment workflow.
- The existing GitHub Actions audio workflow is only for generating fixed Azure Speech audio assets and committing them back to the repository.
- Preserve responsive layouts and keyboard/touch accessibility.
- Do not add accounts, tracking, persistent answers, or recording storage without explicit authorization.
- Preserve Spanish accents and grammatical gender in educational content.
- Do not claim speech recognition is a professional pronunciation assessment.
- Never commit credentials, `.env` files, or hosting identity. Runtime secrets belong in Cloudflare Worker secrets/bindings.
- Document third-party teaching assets separately from any source-code license.
- Run `node --check dist/app.js` after frontend JavaScript changes and `node --check worker/index.js` after Worker JavaScript changes.
