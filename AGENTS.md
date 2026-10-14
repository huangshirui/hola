# Project instructions

- This is a Spanish practice website for Chinese-speaking children, deployed as Cloudflare Workers + Static Assets.
- Keep browser-delivered application files in `dist/`; Worker API code lives in `worker/`.
- The Cloudflare build runs `npm install` + `npm run build`; the build copies the pinned Azure Speech SDK browser bundle into `dist/vendor/` before deploy.
- Azure Speech SDK is the primary speech-recognition path. Force recognition language to `es-ES`; do not silently fall back to native Web Speech recognition.
- Preserve responsive layouts and keyboard/touch accessibility.
- Do not add accounts, tracking, persistent answers, or recording storage without explicit authorization.
- Preserve Spanish accents and grammatical gender in educational content.
- Do not claim speech recognition is a professional pronunciation assessment.
- Never commit credentials, `.env` files, Azure keys, or hosting secrets.
- Document third-party teaching assets separately from any source-code license.
- After JavaScript changes run `node --check dist/app.js`, `node --check dist/azure-speech-recognition.js`, and the test suite.
