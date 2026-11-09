export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const code = url.searchParams.get('code');
  if (!code) {
    return new Response('缺少授权码', { status: 400 });
  }

  const tokenRes = await fetch('https://github.com/login/oauth/access_token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({
      client_id: env.GITHUB_CLIENT_ID,
      client_secret: env.GITHUB_CLIENT_SECRET,
      code,
    }),
  });
  const { access_token: token } = await tokenRes.json();
  if (!token) {
    return new Response('获取访问令牌失败', { status: 400 });
  }

  const payload = JSON.stringify({ token });
  const html = `<!doctype html><html><body><script>
    (function(){
      function receiveMessage(e){
        window.opener.postMessage('authorization:github:success:${payload}', e.origin);
        window.removeEventListener('message', receiveMessage, false);
      }
      window.addEventListener('message', receiveMessage, false);
      window.opener.postMessage('authorizing:github', '*');
    })();
  </script></body></html>`;

  return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}
