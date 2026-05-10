import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
  site: process.env.ASTRO_SITE || 'https://lessons.johnboen.com',
  base: '/',
  server: { port: 4331 },
});
