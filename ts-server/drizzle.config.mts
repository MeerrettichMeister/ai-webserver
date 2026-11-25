import 'dotenv/config';
// @ts-expect-error
import process from 'node:process';

import { defineConfig } from 'drizzle-kit';
export default defineConfig({
  dialect: 'postgresql',
  // drizzle-kit pull writes schema.ts and relations.ts into `out`
  out: './drizzle',
  schema: './src/db/drizzle/schema.ts',
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
