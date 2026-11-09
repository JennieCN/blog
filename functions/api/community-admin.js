// 仅允许站点所有者（JennieCN）通过后台一键指定或移除问答社区（Flarum）管理员
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
    const r = await fetch(`${FLARUM_BASE}/api/users?page%5Blimit%5D=50`, { headers });
    const d = await r.json();
    const admins = (d.data || [])
      .filter((u) => {
        const groups = u.relationships?.groups?.data || [];
        return groups.some((g) => g.id === '1');
      })
      .map((u) => ({ id: u.id, username: u.attributes.username, email: u.attributes.email }));
    return new Response(JSON.stringify({ admins }), {
      headers: { 'Content-Type': 'application/json' },
    });
  }

  if (request.method === 'POST') {
    const { username, role } = await request.json();
    const sr = await fetch(
      `${FLARUM_BASE}/api/users?filter%5Bq%5D=${encodeURIComponent(username)}`,
      { headers },
    );
    const sd = await sr.json();
    const user = (sd.data || []).find(
      (u) => (u.attributes.username || '').toLowerCase() === username.toLowerCase(),
    );
    if (!user) {
      return new Response(JSON.stringify({ error: '未找到该社区用户名，请让对方先在社区注册' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    const groups = role === 'admin' ? [{ type: 'groups', id: '1' }] : [];
    const pr = await fetch(`${FLARUM_BASE}/api/users/${user.id}`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify({
        data: { type: 'users', id: user.id, relationships: { groups: { data: groups } } },
      }),
    });
    return new Response(JSON.stringify({ ok: pr.ok }), {
      status: pr.ok ? 200 : 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  return new Response('Method Not Allowed', { status: 405 });
}
