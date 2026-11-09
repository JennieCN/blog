import type { PostSummary } from './posts';

export function collectTags(posts: PostSummary[]): Map<string, PostSummary[]> {
  const map = new Map<string, PostSummary[]>();
  for (const p of posts) {
    for (const t of p.tags) {
      const list = map.get(t) ?? [];
      list.push(p);
      map.set(t, list);
    }
  }
  return map;
}
