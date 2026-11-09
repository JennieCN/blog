import { readFileSync, existsSync } from 'node:fs';

if (!existsSync('public/yjcnb/index.html') || !existsSync('public/yjcnb/config.yml')) {
  console.error('CMS 文件缺失');
  process.exit(1);
}

const yml = readFileSync('public/yjcnb/config.yml', 'utf8');
const sections = ['vps', 'fsae', 'rm', 'ai', 'resources'];
const missing = sections.filter((s) => !yml.includes(`src/content/${s}`));
if (missing.length) {
  console.error('CMS 缺少集合:', missing.join(', '));
  process.exit(1);
}

const fields = ['title', 'description', 'pubDate', 'tags', 'draft'];
const missingFields = fields.filter((f) => !yml.includes(`name: ${f}`));
if (missingFields.length) {
  console.error('CMS 缺少字段:', missingFields.join(', '));
  process.exit(1);
}

console.log('CMS 配置校验通过');
