import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const postSchema = z.object({
  title: z.string(),
  description: z.string(),
  pubDate: z.coerce.date(),
  updatedDate: z.coerce.date().optional(),
  tags: z.array(z.string()).default([]),
  draft: z.boolean().default(false),
  cover: z.string().optional(),
});

const makeCollection = (name: string) =>
  defineCollection({
    loader: glob({ pattern: '**/*.md', base: `./src/content/${name}` }),
    schema: postSchema,
  });

// 问答：问题本身是一篇 Markdown，回答通过页面底部的 Waline 评论收集
const qaSchema = z.object({
  question: z.string(),
  description: z.string(),
  pubDate: z.coerce.date(),
  tags: z.array(z.string()).default([]),
  draft: z.boolean().default(false),
  solved: z.boolean().default(false),
});

export const collections = {
  vps: makeCollection('vps'),
  fsae: makeCollection('fsae'),
  rm: makeCollection('rm'),
  ai: makeCollection('ai'),
  resources: makeCollection('resources'),
  qa: defineCollection({
    loader: glob({ pattern: '**/*.md', base: './src/content/qa' }),
    schema: qaSchema,
  }),
};
