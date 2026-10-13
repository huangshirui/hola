export default {
  async fetch(request) {
    const url = new URL(request.url);

    if (url.pathname === '/api/health') {
      return Response.json(
        { ok: true, service: 'hola' },
        { headers: { 'cache-control': 'no-store' } },
      );
    }

    return new Response('Not found', { status: 404 });
  },
};
