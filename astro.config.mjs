import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://blog.mycampusmail.com',
  output: 'static',
  integrations: [
    sitemap({
      filter: (page) => !page.includes('/yjcnb'),
    }),
  ],
  vite: {
    plugins: [tailwindcss()],
  },
});
