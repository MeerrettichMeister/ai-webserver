/**
 * Startup check: is the database at the newest migration in `drizzle/`? Otherwise every query
 * that names a missing table or column would fail later with a 500. `drizzle-kit migrate` records
 * each applied migration with the `when` of its journal entry as `created_at`.
 */

import { readFile } from 'node:fs/promises';

import { sql } from 'drizzle-orm';

import { db } from './index.mts';

/** `drizzle/meta/_journal.json`, from `src/recipe/db/` as well as `dist/recipe/db/`. */
const journalUrl = new URL('../../../drizzle/meta/_journal.json', import.meta.url);

type Journal = { entries: { tag: string; when: number }[] };

/** PostgreSQL's undefined_table and invalid_schema_name: never migrated. */
const NOT_MIGRATED_CODES = new Set(['42P01', '3F000']);

/** The `when` of the newest applied migration, or `undefined` if the database was never migrated. */
const newestAppliedMigration = async (): Promise<number | undefined> => {
  try {
    const {
      rows: [row],
    } = await db.execute<{ created_at: string }>(
      sql`SELECT created_at FROM drizzle.__drizzle_migrations ORDER BY created_at DESC LIMIT 1`,
    );
    return row === undefined ? undefined : Number(row.created_at);
  } catch (error) {
    const code = (error as { cause?: { code?: unknown } }).cause?.code;
    if (typeof code === 'string' && NOT_MIGRATED_CODES.has(code)) {
      return undefined;
    }
    throw error;
  }
};

/** @throws Error with what to do, if the database is not at the newest migration. */
export const checkMigrations = async (): Promise<void> => {
  const { entries } = JSON.parse(await readFile(journalUrl, 'utf8')) as Journal;
  const latest = entries.at(-1);
  if (latest === undefined) {
    return;
  }

  const applied = await newestAppliedMigration();
  if (applied === latest.when) {
    return;
  }
  throw new Error(
    applied === undefined
      ? 'The database has no migrations applied. Run `pnpm db:migrate`.'
      : `The database is not at the newest migration "${latest.tag}". Run \`pnpm db:migrate\`; if it fails, the migration history was rewritten (squashed): \`pnpm db:reset\` rebuilds the database, deleting its data.`,
  );
};
