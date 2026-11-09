import { describe, it, expect } from 'vitest';
import { sortByDateDesc, filterDrafts, formatDate } from './posts';

const a = { title: 'a', pubDate: new Date('2026-01-01'), section: 'vps' as const, slug: 'a', description: '', tags: [] };
const b = { title: 'b', pubDate: new Date('2026-03-01'), section: 'vps' as const, slug: 'b', description: '', tags: [] };

describe('sortByDateDesc', () => {
  it('按日期倒序排列且不修改原数组', () => {
    const input = [a, b];
    const out = sortByDateDesc(input);
    expect(out.map((p) => p.slug)).toEqual(['b', 'a']);
    expect(input[0].slug).toBe('a');
  });
});

describe('filterDrafts', () => {
  it('过滤 draft 为 true 的条目', () => {
    expect(filterDrafts([{ draft: true }, { draft: false }, {}])).toHaveLength(2);
  });
});

describe('formatDate', () => {
  it('输出 YYYY-MM-DD', () => {
    expect(formatDate(new Date('2026-11-09T12:00:00Z'))).toBe('2026-11-09');
  });
});
