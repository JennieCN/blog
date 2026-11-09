import { describe, it, expect } from 'vitest';
import { collectTags } from './tags';

const mk = (slug: string, tags: string[]) => ({
  section: 'vps' as const, slug, title: slug, description: '', pubDate: new Date(), tags,
});

describe('collectTags', () => {
  it('按标签分组，同一标签下保留多篇文章', () => {
    const m = collectTags([mk('a', ['VPS', '建站']), mk('b', ['VPS'])]);
    expect(m.get('VPS')?.map((p) => p.slug)).toEqual(['a', 'b']);
    expect(m.get('建站')).toHaveLength(1);
  });

  it('没有标签时返回空 Map', () => {
    expect(collectTags([mk('c', [])]).size).toBe(0);
  });
});
