/**
 * Deletes all data of the app: drops the PostgreSQL schemas `recipes` (tables and data) and
 * `drizzle` (the history of applied migrations), nothing else. Run `pnpm db:migrate` afterwards to
 * recreate the tables and seed data; `pnpm db:reset` does both.
 */

import 'dotenv/config';
import process from 'node:process';

import pg from 'pg';

const url = process.env.DATABASE_URL;
if (url === undefined) {
  throw new Error('DATABASE_URL is not set (see .env).');
}

const client = new pg.Client({ connectionString: url });
await client.connect();
try {
  await client.query('DROP SCHEMA IF EXISTS recipes CASCADE');
  await client.query('DROP SCHEMA IF EXISTS drizzle CASCADE');
  console.log(`Dropped the schemas "recipes" and "drizzle" in ${new URL(url).pathname.slice(1)}.`);
} finally {
  await client.end();
}
