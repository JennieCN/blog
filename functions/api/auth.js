export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const code = url.searchParams.get('code');

  // 无 code 时是 Sveltia CMS 发起的授权请求，重定向到 GitHub 授权页
  if (!code) {
    const authorizeUrl = new URL('https://github.com/login/oauth/authorize');
    authorizeUrl.searchParams.set('client_id', env.GITHUB_CLIENT_ID);
    authorizeUrl.searchParams.set('redirect_uri', `${url.origin}/api/auth`);
    authorizeUrl.searchParams.set('scope', 'repo,user');
    return Response.redirect(authorizeUrl.href, 302);
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

  // 把令牌回传给打开后台的窗口，Sveltia 通过 postMessage 接收
  const payload = JSON.stringify({ token, provider: 'github' });
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
