import rss from '@astrojs/rss';
import type { APIContext } from 'astro';
import { getCollection } from 'astro:content';
import { SECTIONS, SITE } from '../config';
import { filterDrafts, sortByDateDesc, type PostSummary } from '../lib/posts';

export async function GET(context: APIContext) {
  const all: PostSummary[] = [];
  for (const s of SECTIONS) {
    for (const e of filterDrafts(await getCollection(s.key))) {
      all.push({ section: s.key, slug: e.id, title: e.data.title, description: e.data.description, pubDate: e.data.pubDate, tags: e.data.tags });
    }
  }
  const items = sortByDateDesc(all).map((p) => ({
    title: p.title,
    description: p.description,
    pubDate: p.pubDate,
    link: `/${p.section}/${p.slug}/`,
  }));
  return rss({ title: SITE.title, description: SITE.description, site: context.site!, items });
}
