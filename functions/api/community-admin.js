// 仅允许站点所有者（JennieCN）通过后台一键指定或移除全站管理员（博客专栏 + 问答社区合一），或配置社区 Resend API Key
const FLARUM_BASE = 'https://qa.mycampusmail.com';
const DEFAULT_FLARUM_KEY = 'rFMkeThmUMb1yy5v1xqlxzrCpofDXT5TZX1JjiUk';

async function verifyOwner(request) {
  const auth = request.headers.get('Authorization') || '';
  if (!auth.startsWith('Bearer ')) return false;
  const r = await fetch('https://api.github.com/user', {
    headers: { Authorization: auth, 'User-Agent': 'rongxi-blog-admin' },
  });
  if (!r.ok) return false;
  const u = await r.json();
  return u && u.login === 'JennieCN';
}

export async function onRequest({ request, env }) {
  if (!(await verifyOwner(request))) {
    return new Response(JSON.stringify({ error: '仅站点所有者可操作' }), {
      status: 403,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const key = env.FLARUM_API_KEY || DEFAULT_FLARUM_KEY;
  const headers = {
    Authorization: `Token ${key}; userId=1`,
    'Content-Type': 'application/json',
  };

  if (request.method === 'GET') {
    const r = await fetch(`${FLARUM_BASE}/sync-admin.php`, { headers });
    const d = await r.json();
    return new Response(JSON.stringify({ admins: d.admins || [] }), {
      headers: { 'Content-Type': 'application/json' },
    });
  }

  if (request.method === 'POST') {
    const body = await request.json();

    // 配置 Resend API Key
    if (body.resendKey) {
      const rk = String(body.resendKey).trim();
      const sr = await fetch(`${FLARUM_BASE}/api/settings`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          mail_driver: 'smtp',
          mail_host: 'smtp.resend.com',
          mail_port: '465',
          mail_encryption: 'ssl',
          mail_username: 'resend',
          mail_password: rk,
          mail_from: 'noreply@qa.mycampusmail.com',
        }),
      });
      return new Response(JSON.stringify({ ok: sr.ok }), {
        status: sr.ok ? 200 : 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const { username, role } = body;
    const sr = await fetch(`${FLARUM_BASE}/sync-admin.php`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ username, role }),
    });
    const sd = await sr.json();
    return new Response(JSON.stringify(sd), {
      status: sr.ok ? 200 : 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  return new Response('Method Not Allowed', { status: 405 });
}
