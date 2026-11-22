import 'dotenv/config';
import { defineConfig } from 'drizzle-kit';
// @ts-expect-error
import process from "node:process";
export default defineConfig({
  dialect: 'postgresql',
  // drizzle-kit pull writes schema.ts and relations.ts into `out`
  out: './drizzle',
  schema: './src/db/drizzle/schema.ts',
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
