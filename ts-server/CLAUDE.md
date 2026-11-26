# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

An early-stage TypeScript web server: Hono (HTTP), Drizzle ORM on node-postgres (`pg`), Zod
(validation). So far only the scaffolding exists: `src/index.mts` just logs a message, and
`src/recipe/db` exports a Drizzle `db` built from `DATABASE_URL` (loaded via `dotenv/config`)
that nothing uses yet. There is no HTTP app and no test suite yet.

Code is organized by feature, following the Hono example project (`../../hono/src/buch/`):
`src/recipe/dto/*-dto.mts` are the response DTOs (classes built from Drizzle `$inferSelect`
rows, mapping camelCase columns to the API's snake_case fields),
`src/recipe/validation/*-validation.mts` are the request bodies as Zod schemas (a base schema, with
`*Create`/`*Update`/`*Replace` schemas derived from it and compiled with `z.compile`). The API has
no pagination.

`src/recipe/repository/*-repository.mts` hold the database access (the example has none; its
services query Drizzle directly). They export plain async functions that take and return Drizzle
rows (`$inferInsert`/`$inferSelect`, camelCase); mapping to DTOs and API fields is the service's
job. Each function takes an optional `Executor` as its last argument: pass the `tx` of
`db.transaction(...)` to make several calls atomic. The recipe `version` covers the whole
aggregate, but only `incrementVersion` changes it, so call it in the same transaction as every
write to a recipe, its details, ingredients or steps. Ingredient and step updates bump their own
row versions as well.

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
`src/recipe/db`, which does not exist; fix that before using `generate`/`push`.

## Security plan (authentication and authorization)

The API's endpoints are protected: **every endpoint requires an authenticated user** unless it is
explicitly decided otherwise. Keep this in mind for every endpoint you add.

- **Identity provider:** the Keycloak server from `scripts/docker-compose.yaml`. A realm for this
  app already exists there, with two groups:
  - `user`: regular users, the default rights.
  - `moderator`: has more rights than `user`. Treat it as a superset: anything a `user` may do, a
    `moderator` may do too.
- **The API does not handle logins or passwords.** Clients get an access token (JWT) from
  Keycloak and send it as `Authorization: Bearer <token>`. The server only verifies the token
  (signature against the realm's JWKS at
  `http://localhost:8080/realms/<realm>/protocol/openid-connect/certs`, plus `exp` and the
  issuer) and reads the user's groups from it. Hono ships suitable middleware (`hono/jwk`,
  `hono/jwt`).
- **Groups are not in the token by default.** Keycloak only puts group membership into access
  tokens if a _Group Membership_ mapper is configured on the client (or a client scope). The
  claim name and whether it holds full paths (`/moderator`) or plain names (`moderator`) depend
  on that mapper. Check the realm configuration before writing the group check.
- **Status codes:** missing or invalid token → `401 Unauthorized`; valid token but the required
  group is missing → `403 Forbidden`.

When implementing an endpoint:

1. Decide which group it needs (`user` or `moderator`) and enforce that on the server for each
   route, e.g. with a shared middleware. Do not rely on the client hiding actions.
2. Take the user's identity (the token's `sub`) and groups only from the verified token, never
   from the request body, query or custom headers.
3. Keep the auth logic in one place (verification + group check) instead of repeating it in
   handlers, so the rules can be changed for all endpoints at once.

Not yet recorded in the repository: the realm's name, the Keycloak client the API and its clients
use, and which operations exactly are reserved for `moderator`. Ask before assuming them. The
realm itself is only stored in Keycloak's database inside the `postgres_data` Docker volume, so
`docker compose ... down -v` deletes it.
