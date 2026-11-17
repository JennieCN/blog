import type { SectionKey } from '../config';

export interface PostSummary {
  section: SectionKey;
  slug: string;
  title: string;
  description: string;
  pubDate: Date;
  updatedDate?: Date;
  tags: string[];
  words?: number;
  minutes?: number;
}

export interface ForumFeedItem {
  title?: string;
  excerpt?: string;
  url?: string;
  author?: string;
  lastPostedAt?: string;
  createdAt?: string;
  isSolved?: boolean;
  isSticky?: boolean;
  commentCount?: number;
  tags?: { slug?: string; name?: string }[];
}

export function sortByDateDesc<T extends { pubDate: Date }>(posts: T[]): T[] {
  return [...posts].sort((x, y) => y.pubDate.getTime() - x.pubDate.getTime());
}

export function filterDrafts<T extends { draft?: boolean; data?: { draft?: boolean } }>(items: T[]): T[] {
  return items.filter((i) => i.draft !== true && i.data?.draft !== true);
}

export function formatDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function formatLocalDate(input: string | number | Date | undefined | null): string {
  if (input == null || input === '') return '';
  const d = input instanceof Date ? input : new Date(input);
  if (Number.isNaN(d.getTime())) {
    return typeof input === 'string' ? input.slice(0, 10) : '';
  }
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function slugBoundaryMatch(haystack: string, targetPath: string): boolean {
  const path = String(targetPath || '').trim();
  if (!haystack || !path) return false;
  const bare = path.replace(/\/+$/, '');
  if (!bare) return false;
  const escaped = bare.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const re = new RegExp(`(?:^|https?:\\/\\/[^/\\s]+|[^A-Za-z0-9_/-])${escaped}/?(?:$|[\\s)\\]>'"#?,.;:!，。；：！？])`);
  return re.test(haystack);
}

export function rankRelatedForumItems<T extends ForumFeedItem>(
  items: T[],
  postPath: string,
  postTitle: string,
  limit = 5,
): T[] {
  const titleNeedle = String(postTitle || '').trim();
  return [...items]
    .map((item) => {
      const hay = `${item.title || ''} ${item.excerpt || ''}`;
      const cites =
        (postPath && slugBoundaryMatch(hay, postPath)) ||
        (titleNeedle.length >= 4 && hay.includes(titleNeedle))
          ? 1
          : 0;
      const ts = Date.parse(item.lastPostedAt || item.createdAt || '') || 0;
      return { item, cites, ts };
    })
    .sort((a, b) => b.cites - a.cites || b.ts - a.ts)
    .slice(0, limit)
    .map((x) => x.item);
}

export function stripMarkdown(md: string): string {
  return String(md || '')
    .replace(/^```[^\n]*\n[\s\S]*?^```/gm, ' ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/[*_~>|-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export function wordCount(text: string): number {
  const plain = stripMarkdown(text);
  const cjk = (plain.match(/[\u4e00-\u9fa5]/g) || []).length;
  const words = (plain.replace(/[\u4e00-\u9fa5]/g, ' ').match(/[A-Za-z0-9_]+/g) || []).length;
  const n = cjk + words;
  return n >= 100 ? Math.round(n / 100) * 100 : n;
}

export function readingMinutes(text: string): number {
  const plain = stripMarkdown(text);
  const cjk = (plain.match(/[\u4e00-\u9fa5]/g) || []).length;
  const words = (plain.replace(/[\u4e00-\u9fa5]/g, ' ').match(/[A-Za-z0-9_]+/g) || []).length;
  return Math.max(1, Math.ceil((cjk + words) / 380));
}

export function byMonth<T extends { pubDate: Date }>(posts: T[]): { key: string; label: string; posts: T[] }[] {
  const groups: { key: string; label: string; posts: T[] }[] = [];
  for (const p of posts) {
    const iso = p.pubDate.toISOString();
    const key = iso.slice(0, 7);
    const year = iso.slice(0, 4);
    const month = parseInt(iso.slice(5, 7), 10);
    if (!groups.length || groups[groups.length - 1].key !== key) {
      groups.push({ key, label: `${year} 年 ${month} 月`, posts: [] });
    }
    groups[groups.length - 1].posts.push(p);
  }
  return groups;
}
