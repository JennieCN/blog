import { existsSync } from 'node:fs';

const required = ['dist/index.html', 'dist/pagefind/pagefind.js'];
const missing = required.filter((p) => !existsSync(p));
if (missing.length) {
  console.error('构建产物缺失:', missing.join(', '));
  process.exit(1);
}
console.log('构建产物完整');
