export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === '/api/health') {
      return Response.json(
        { ok: true, service: 'hola' },
        { headers: { 'cache-control': 'no-store' } },
      );
    }

    if (url.pathname === '/api/speech/token') {
      if (!env.AZURE_SPEECH_KEY || !env.AZURE_SPEECH_REGION) {
        return Response.json({ error: 'speech_not_configured' }, { status: 503 });
      }

      const response = await fetch(
        `https://${env.AZURE_SPEECH_REGION}.api.cognitive.microsoft.com/sts/v1.0/issuetoken`,
        {
          method: 'POST',
          headers: {
            'Ocp-Apim-Subscription-Key': env.AZURE_SPEECH_KEY,
          },
        },
      );

      if (!response.ok) {
        return Response.json({ error: 'token_failed' }, { status: 502 });
      }

      return Response.json(
        {
          token: await response.text(),
          region: env.AZURE_SPEECH_REGION,
        },
        { headers: { 'cache-control': 'no-store' } },
      );
    }

    return env.ASSETS.fetch(request);
  },
};
