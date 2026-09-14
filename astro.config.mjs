// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
export default defineConfig({
  site: 'https://daily-yangmao.2315935618.workers.dev',
  integrations: [sitemap()],
});
