// 用法：node scripts/add-section.mjs <key> <中文名称> <描述>
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';

const [, , key, name, description] = process.argv;
if (!key || !name || !description) {
  console.error('用法: node scripts/add-section.mjs <key> <中文名称> <描述>');
  process.exit(1);
}
if (!/^[a-z0-9-]+$/.test(key)) {
  console.error('key 只能包含小写字母、数字和连字符');
  process.exit(1);
}

// 1. 内容目录
const dir = `src/content/${key}`;
if (!existsSync(dir)) {
  mkdirSync(dir, { recursive: true });
  writeFileSync(
    `${dir}/welcome.md`,
    `---\ntitle: ${name}开篇\ndescription: ${description}\npubDate: ${new Date().toISOString().slice(0, 10)}\ntags: [${name}]\n---\n\n这里是「${name}」分区的第一篇文章。\n`,
  );
}

// 2. src/config.ts
let cfg = readFileSync('src/config.ts', 'utf8');
if (!cfg.includes(`'${key}'`)) {
  cfg = cfg.replace(
    /export type SectionKey = ([^;]+);/,
    (_, u) => `export type SectionKey = ${u.trim()} | '${key}';`,
  );
  cfg = cfg.replace(
    /export const SECTIONS: Section\[\] = \[([\s\S]*?)\];/,
    (_, body) =>
      `export const SECTIONS: Section[] = [${body}  { key: '${key}', name: '${name}', description: '${description}' },\n];`,
  );
  writeFileSync('src/config.ts', cfg);
}

// 3. src/content.config.ts
let ccfg = readFileSync('src/content.config.ts', 'utf8');
if (!ccfg.includes(`${key}: makeCollection`)) {
  ccfg = ccfg.replace(
    /export const collections = \{([\s\S]*?)  qa:/,
    (_, body) => `export const collections = {${body}  ${key}: makeCollection('${key}'),\n  qa:`,
  );
  writeFileSync('src/content.config.ts', ccfg);
}

// 4. public/yjcnb/config.yml
let yml = readFileSync('public/yjcnb/config.yml', 'utf8');
if (!yml.includes(`folder: src/content/${key}`)) {
  const block = `  - name: ${key}\n    label: ${name}\n    label_singular: ${name}文章\n    folder: src/content/${key}\n    create: true\n    extension: md\n    format: frontmatter\n    slug: "{{slug}}"\n    fields: *post_fields\n`;
  yml = yml.replace('  - name: qa\n', `${block}  - name: qa\n`);
  writeFileSync('public/yjcnb/config.yml', yml);
}

console.log(`已添加分区: ${key} (${name})`);
