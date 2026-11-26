import 'dotenv/config';
import process from 'node:process';

import { defineConfig } from 'drizzle-kit';
export default defineConfig({
  dialect: 'postgresql',
  // drizzle-kit pull writes schema.mts and relations.ts into `out`
  out: './drizzle',
  schema: './src/recipe/db/schema.mts',
  // The tables are in the PostgreSQL schema `recipes`; drizzle-kit only looks at `public` otherwise.
  schemaFilter: ['recipes'],
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
