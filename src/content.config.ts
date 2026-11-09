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

export const collections = {
  vps: makeCollection('vps'),
  fsae: makeCollection('fsae'),
  rm: makeCollection('rm'),
  ai: makeCollection('ai'),
  resources: makeCollection('resources'),
};
