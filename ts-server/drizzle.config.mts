import 'dotenv/config';
import process from 'node:process';

import { defineConfig } from 'drizzle-kit';
export default defineConfig({
  dialect: 'postgresql',
  // drizzle-kit pull writes schema.mts and relations.ts into `out`
  out: './drizzle',
  schema: './src/db/drizzle/schema.mts',
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
