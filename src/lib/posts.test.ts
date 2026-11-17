import { describe, it, expect } from 'vitest';
import {
  sortByDateDesc,
  filterDrafts,
  formatDate,
  formatLocalDate,
  slugBoundaryMatch,
  rankRelatedForumItems,
  wordCount,
  readingMinutes,
  byMonth,
} from './posts';

const a = { title: 'a', pubDate: new Date('2026-01-01'), section: 'vps' as const, slug: 'a', description: '', tags: [] };
const b = { title: 'b', pubDate: new Date('2026-03-01'), section: 'vps' as const, slug: 'b', description: '', tags: [] };
const c = { title: 'c', pubDate: new Date('2026-03-15'), section: 'ai' as const, slug: 'c', description: '', tags: [] };

describe('sortByDateDesc', () => {
  it('按日期倒序排列且不修改原数组', () => {
    const input = [a, b];
    const out = sortByDateDesc(input);
    expect(out.map((p) => p.slug)).toEqual(['b', 'a']);
    expect(input[0].slug).toBe('a');
  });
});

describe('filterDrafts', () => {
  it('过滤 draft 为 true 的条目（兼容 data.draft）', () => {
    expect(
      filterDrafts([
        { draft: true },
        { draft: false },
        {},
        { data: { draft: true } },
        { data: { draft: false } },
      ]),
    ).toHaveLength(3);
  });
});

describe('formatDate', () => {
  it('输出 YYYY-MM-DD', () => {
    expect(formatDate(new Date('2026-11-09T12:00:00Z'))).toBe('2026-11-09');
  });
});

describe('formatLocalDate', () => {
  it('格式化合法时间为 YYYY-MM-DD 并在非法输入时安全回退', () => {
    const d = new Date(2026, 10, 17, 15, 30, 0);
    expect(formatLocalDate(d)).toBe('2026-11-17');
    expect(formatLocalDate('')).toBe('');
    expect(formatLocalDate(null)).toBe('');
    expect(formatLocalDate('2026-11-17-invalid')).toBe('2026-11-17');
  });
});

describe('slugBoundaryMatch & rankRelatedForumItems', () => {
  it('匹配带斜杠或边界的文章路径并避免前缀误命中', () => {
    expect(slugBoundaryMatch('参考 https://blog.mycampusmail.com/vps/two/ 这篇', '/vps/two/')).toBe(true);
    expect(slugBoundaryMatch('详见 (/vps/two#sec1)', '/vps/two/')).toBe(true);
    expect(slugBoundaryMatch('参考 https://blog.mycampusmail.com/vps/two-years/ 这篇', '/vps/two/')).toBe(false);
    expect(slugBoundaryMatch('参考 /sub/vps/two/', '/vps/two/')).toBe(false);
  });

  it('优先置顶引用当前文章路径或标题的帖子，其余按时间倒序', () => {
    const items = [
      { title: '较新无关讨论', excerpt: '包含 /vps/two-years/ 链接', lastPostedAt: '2026-11-17T10:00:00Z' },
      { title: '引用文章的帖子', excerpt: '推荐看 https://blog.mycampusmail.com/vps/two/ 笔记', lastPostedAt: '2026-11-10T10:00:00Z' },
      { title: '最早普通讨论', excerpt: '普通提问', lastPostedAt: '2026-11-01T10:00:00Z' },
    ];
    const ranked = rankRelatedForumItems(items, '/vps/two/', '两台服务器分流指南', 5);
    expect(ranked.map((x) => x.title)).toEqual([
      '引用文章的帖子',
      '较新无关讨论',
      '最早普通讨论',
    ]);
  });
});

describe('wordCount & readingMinutes', () => {
  it('统计中英文字数并计算阅读分钟', () => {
    expect(wordCount('Hello world 你好世界')).toBe(6);
    expect(readingMinutes('短文测试')).toBe(1);
    const long = '测试'.repeat(250);
    expect(wordCount(long)).toBe(500);
    expect(readingMinutes(long)).toBe(2);
  });
});

describe('byMonth', () => {
  it('按年月分组保持倒序', () => {
    const groups = byMonth(sortByDateDesc([a, b, c]));
    expect(groups).toHaveLength(2);
    expect(groups[0].key).toBe('2026-03');
    expect(groups[0].posts.map((p) => p.slug)).toEqual(['c', 'b']);
    expect(groups[1].key).toBe('2026-01');
  });
});
