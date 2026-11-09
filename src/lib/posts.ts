import type { SectionKey } from '../config';

export interface PostSummary {
  section: SectionKey;
  slug: string;
  title: string;
  description: string;
  pubDate: Date;
  tags: string[];
}

export function sortByDateDesc(posts: PostSummary[]): PostSummary[] {
  return [...posts].sort((x, y) => y.pubDate.getTime() - x.pubDate.getTime());
}

export function filterDrafts<T extends { draft?: boolean }>(items: T[]): T[] {
  return items.filter((i) => i.draft !== true);
}

export function formatDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}
