import type { NodePgQueryResultHKT } from 'drizzle-orm/node-postgres';
import type { PgDatabase } from 'drizzle-orm/pg-core';

/**
 * What the repository functions run their queries on: the `db` itself or a transaction from
 * `db.transaction(async (tx) => ...)`. Pass the same `tx` to several repository functions to make
 * their writes atomic.
 */
export type Executor = PgDatabase<NodePgQueryResultHKT>;
