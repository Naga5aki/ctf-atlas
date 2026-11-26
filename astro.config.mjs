import { defineConfig } from 'astro/config';
import { satteri } from '@astrojs/markdown-satteri';

export default defineConfig({
  site: 'http://127.0.0.1:4321',
  output: 'static',
  // Keep CLI flags and quoted arguments copyable in the knowledge base.
  markdown: {
    processor: satteri({ features: { smartPunctuation: false } }),
    shikiConfig: { theme: 'github-light' },
  },
});
