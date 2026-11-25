# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

An early-stage TypeScript web server: Hono (HTTP), Drizzle ORM on node-postgres (`pg`), Zod
(validation). So far only the scaffolding exists: `src/index.mts` just logs a message, and
`src/db/index.mts` exports a Drizzle `db` built from `DATABASE_URL` (loaded via `dotenv/config`)
that nothing uses yet. There is no HTTP app and no test suite yet.

The git repository root is the parent directory (`ai-webserver/`). This project lives in
`ts-server/`. The sibling `py-server/` is a separate FastAPI recipe API with its own `CLAUDE.md`.

## Commands

The package manager is **pnpm**. Prefer the scripts or `pnpm exec <bin>`: `npx` fails from Git
Bash here because the project path contains a space.

```sh
pnpm install
pnpm dev          # node --watch src/index.mts (Node runs the .mts directly, no build step)
pnpm build        # tsc -> dist/*.mjs
pnpm start        # node dist/index.mjs
pnpm typecheck    # tsc --noEmit
pnpm lint         # oxlint (.oxlintrc.json); pnpm lint:fix to autofix
pnpm fmt          # oxfmt (.oxfmtrc.json); pnpm fmt:check to only check
pnpm db:pull      # drizzle-kit pull: introspect the database into drizzle/
```

## TypeScript conventions

- Source files are **`.mts`**, not `.ts`; `tsconfig.json` only includes `src/**/*.mts`
  (`rootDir: src`, output in `dist/` as `.mjs`).
- Relative imports name the `.mts` file (`import { db } from './db/index.mts'`);
  `rewriteRelativeImportExtensions` turns them into `.mjs` on build.
- `erasableSyntaxOnly` and `verbatimModuleSyntax` are on, so Node can strip the types itself: no
  `enum`, `namespace` or parameter properties, and type-only imports must use `import type`
  (oxlint also enforces `typescript/consistent-type-imports`).
- TypeScript 6 defaults `types` to `[]` and `rootDir` to the tsconfig directory, which is why both
  are set explicitly; add further `@types/*` packages to `types`.
- Formatting (oxfmt): 100 columns, single quotes (double in YAML), semicolons, trailing commas,
  imports sorted.

## Database and Drizzle

`scripts/docker-compose.yaml` starts PostgreSQL 18 (`postgres`/`postgres`, port 5432) and
Keycloak 26 (`start-dev`, http://localhost:8080, admin `admin`/`admin`). Keycloak stores its data
in a `keycloak` database that `scripts/init-keycloak-db.sql` creates, but only when the
`postgres_data` volume is first initialized.

```sh
docker compose -f scripts/docker-compose.yaml up -d
```

`DATABASE_URL` comes from `.env` (which is committed). On Windows, prefer `127.0.0.1` over
`localhost` in the URL: `localhost` resolves to `::1` first, where the Docker port forward can
accept the connection and then never answer (see `py-server/CLAUDE.md`).

Drizzle is used database-first so far: `pnpm db:pull` writes `schema.mts`, `relations.mts` and the
SQL/meta snapshot into `drizzle/` (generated, plain `.ts`, excluded from formatting and partly from
linting). The config is `drizzle.config.mts`, which drizzle-kit does not find on its own, so pass
`--config=drizzle.config.mts` to every drizzle-kit command. Its `schema` option points to
`./src/db/drizzle/schema.ts`, which does not exist; fix that before using `generate`/`push`.
