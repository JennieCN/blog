import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { SECTIONS } from '../config';
import { filterDrafts, sortByDateDesc, wordCount, formatDate } from '../lib/posts';

export const GET: APIRoute = async () => {
  const posts = [];
  for (const s of SECTIONS) {
    const entries = filterDrafts(await getCollection(s.key));
    for (const e of entries) {
      posts.push({
        section: s.key,
        sectionName: s.name,
        slug: e.id,
        title: e.data.title,
        description: e.data.description,
        pubDate: e.data.pubDate,
        dateStr: formatDate(e.data.pubDate),
        tags: e.data.tags,
        words: wordCount(e.body ?? ''),
        url: `/${s.key}/${e.id}/`,
      });
    }
  }

  const sorted = sortByDateDesc(posts).map(({ pubDate: _d, ...rest }) => rest);

  return new Response(
    JSON.stringify({
      sections: SECTIONS.map((s) => ({
        key: s.key,
        name: s.name,
        description: s.description,
        color: s.color,
        icon: s.icon,
        url: `/${s.key}/`,
      })),
      posts: sorted,
    }),
    {
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
      },
    },
  );
};
