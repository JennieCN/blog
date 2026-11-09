import { readdirSync, readFileSync } from 'node:fs';

const sections = ['vps', 'fsae', 'rm', 'ai', 'resources'];
const required = ['title:', 'description:', 'pubDate:', 'tags:'];

for (const s of sections) {
  const dir = `src/content/${s}`;
  const files = readdirSync(dir).filter((f) => f.endsWith('.md'));
  for (const f of files) {
    const text = readFileSync(`${dir}/${f}`, 'utf8').split('---')[1] ?? '';
    const missing = required.filter((k) => !text.includes(k));
    if (missing.length) {
      console.error(`${dir}/${f} 缺少字段: ${missing.join(', ')}`);
      process.exit(1);
    }
  }
}
console.log('内容 frontmatter 校验通过');
