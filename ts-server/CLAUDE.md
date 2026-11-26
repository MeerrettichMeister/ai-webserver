# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

An early-stage TypeScript web server: Hono (HTTP, served by `@hono/node-server`), Drizzle ORM on
node-postgres (`pg`), Zod (validation). `src/index.mts` starts the server on
`https://localhost:<PORT>` (default 3000), see "HTTP/2 and TLS"; `src/app.mts` mounts the routers and maps errors to Problem Details responses
(`src/problem-details.mts`, RFC 9457). `src/recipe/db` exports the Drizzle `db` built from
`DATABASE_URL` (loaded via `dotenv/config`). There is no test suite yet.

Before the first start, create the tables and seed data with `pnpm db:migrate` (see "Database and
Drizzle").

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

`src/recipe/service/` has the business logic (`recipe-service.mts` reads, `recipe-write-service.mts`
writes, each write in one transaction) and throws the errors in `service/errors.mts`.
`src/recipe/router/recipe-router.mts` is mounted at `/recipes`; its contract follows py-server:
`GET /` (list, `?search=`), `GET /:id` (`ETag`, `304` on `If-None-Match`), `POST /` (`201`, empty body,
the new recipe's URL in `Location`), `PUT /:id` (replace; accepts a changed `GET /:id` response as it is: its `id` must match the
URL, the read-only `version`s, timestamps and step `position`s are ignored, the order of `steps`
counts) and
`PATCH /:id` (rename). Writes require `If-Match` (`428` if
missing, `412` if not the current version; `src/etag.mts`) and answer with the recipe and its new
`ETag`. Invalid JSON is `400`, a failed Zod validation or an unknown ingredient/step id `422`, a
unique violation (e.g. two ingredients swapping names in one `PUT`) `409`.

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
pnpm db:migrate   # drizzle-kit migrate: apply the pending migrations in drizzle/
pnpm db:generate  # drizzle-kit generate: new migration from changes to src/recipe/db/schema.mts
pnpm db:pull      # drizzle-kit pull: introspect the database into drizzle/
pnpm db:reset     # scripts/reset-db.mts drops the schemas recipes + drizzle, then db:migrate
pnpm dev:reset    # db:reset, then dev
```

`db:reset` deletes all app data (only the PostgreSQL schemas `recipes` and `drizzle`, nothing else
in the database). The WebStorm run configurations in `.run/` (shared, committed) are "Start server"
(`dev`) and "Reset database and start server" (`dev:reset`).

## HTTP/2 and TLS

The server speaks **HTTP/2 over TLS** (`createSecureServer` from `node:http2`); there is no plain
HTTP port. Clients choose the protocol in the TLS handshake (ALPN): HTTP/2 if they support it,
otherwise HTTP/1.1 (`allowHTTP1`, e.g. for Bruno or Schannel-based tools). The minimum TLS version
stays at Node's default, 1.2, because Windows 10's Schannel (used by its `curl.exe` and PowerShell)
has no TLS 1.3. Git Bash's and Windows' `curl` have no HTTP/2 support, so they always use
HTTP/1.1; test HTTP/2 with a browser or Node's `http2.connect`.

The certificate is a self-signed development certificate for `localhost`, `127.0.0.1` and `::1`
in `tls/` (`key.pem`, `cert.pem`, valid until 2029-02). Clients have to trust `tls/cert.pem` or
skip verification (`curl -k`). `tls/key.pem` is git-ignored, so after cloning the server does not
start until both files are created. The committed `cert.pem` only fits the key it was made with,
so create both together. To create them (in Git Bash, `MSYS_NO_PATHCONV=1` keeps
`/CN=...` from being turned into a Windows path):

```sh
MSYS_NO_PATHCONV=1 openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -nodes \
  -keyout tls/key.pem -out tls/cert.pem -days 825 -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:::1"
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

The schema is defined in code, `src/recipe/db/schema.mts`, in the PostgreSQL schema `recipes`.
The database is changed **only through Drizzle migrations** in `drizzle/` (`NNNN_name.sql` plus
`meta/_journal.json` and snapshots; generated, excluded from formatting and partly from linting).
There is no production database yet, so the history was squashed into a single migration,
`0000_init`: the generated `CREATE` statements for the whole schema, followed by hand-added SQL
inserting `recipes/Sachertorte.json` with the fixed id `5174cc9d-71cb-4d34-a3e9-ce8649192e20`
(ingredient and step ids from `gen_random_uuid()`, timestamps from the column defaults). The seed
SQL was generated once from the JSON; editing the JSON does not change it.

While there is no production database, squashing again is fine: delete `drizzle/0*.sql` and
`drizzle/meta/`, run `pnpm db:generate --name=init`, append the seed SQL to the new file after a
`--> statement-breakpoint`, and `pnpm db:reset` every local database (its recorded history no
longer matches). Once a production database exists, only add new migrations.

**Timestamps:** every table spreads `timestamps` from `schema.mts`. The database fills both on
insert; `updated_at` gets `now()` through Drizzle's `$onUpdate` on every `UPDATE` made through
Drizzle, so repository functions need not set it. `now()` is the start of the transaction, so all
rows of one request share a time. The recipe's `updated_at` covers the whole recipe (like its
version, since `incrementVersion` updates the row); ingredients and steps only change theirs when
they actually change. The DTOs return them as `created_at`/`updated_at` (ISO 8601), and `PUT`
accepts and ignores them (`validation/read-only-fields.mts`).

`drizzle-kit migrate` fails **without an error message** (only exit code 1) if a migration
fails, e.g. on a database whose tables were created without migrations: check
`drizzle.__drizzle_migrations` then, and `pnpm db:reset` if the data may go.

`pnpm db:migrate` applies the pending migrations (recorded in `drizzle.__drizzle_migrations`);
run it on a fresh database before the first start, the server does not create tables itself.
After changing `schema.mts`, run `pnpm db:generate --name=<what>` and commit the new migration;
for data, `pnpm db:generate --custom --name=<what>` creates an empty SQL file to fill in. Never
edit an applied migration, and do not use `drizzle-kit push`, which bypasses the migration
history. The config is `drizzle.config.mts`, which drizzle-kit does not find on its own, so pass
`--config=drizzle.config.mts` to every drizzle-kit command (the scripts do); its
`schemaFilter: ['recipes']` makes drizzle-kit look only at the `recipes` schema. `drizzle/schema.mts`
and `drizzle/relations.mts` are the stale output of that early `db:pull`, not the real schema.

## Security plan (authentication and authorization)

The API's endpoints are protected: **every endpoint requires an authenticated user** unless it is
explicitly decided otherwise. Keep this in mind for every endpoint you add. The one exception so
far is the login, `POST /auth`, which cannot require a token since it is how clients get one.

- **Identity provider:** the Keycloak server from `scripts/docker-compose.yaml`. A realm for this
  app already exists there, with two groups:
  - `user`: regular users, the default rights.
  - `moderator`: has more rights than `user`. Treat it as a superset: anything a `user` may do, a
    `moderator` may do too.
- **Logins go to Keycloak; the API never checks or stores passwords.** Clients get an access token
  (JWT) either from Keycloak directly or through `POST /auth` (below), and send it as
  `Authorization: Bearer <token>`. The server verifies the token
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

The implementation is `src/security/auth.mts`: put `requireGroup('user' | 'moderator')` on every
route. It verifies the token with `hono/jwk` (RS256, issuer, `aud`, `exp`; the JWKS is cached for
5 minutes) and then checks the groups. The verified claims are in `c.get('jwtPayload')`. The
Keycloak URLs and client id come from `.env` via `src/security/keycloak-config.mts`.

**Login (`src/security/auth-router.mts`, `keycloak-service.mts`):** `POST /auth` with
`{ "username", "password" }` forwards the credentials to Keycloak's token endpoint (password
grant, i.e. "Direct access grants" of the client `ts-server`) and answers `200` with
`access_token`, `token_type`, `expires_in`, `refresh_token` and `refresh_expires_in`
(`Cache-Control: no-store`). Wrong credentials, a disabled account or pending required actions
(Keycloak's `invalid_grant`) give `401`; Keycloak unreachable or failing gives `502`; invalid JSON
`400`, a missing field `422`. Never log the request body there. Tokens from `/auth` always carry the
issuer the server expects, as the server asks Keycloak at `KEYCLOAK_URL`.

- **Realm and client** (from `.env`): realm `ai-webserver`, client `ts-server` (public, standard
  flow and direct access grants, redirect `https://localhost:3000/*`). The client has a _Group
  Membership_ mapper writing plain group names into the `groups` claim and an audience mapper
  putting `ts-server` into `aud`, which the server requires.
- **Users:** `recipe-admin` (group `moderator`). The realm's user profile has email, first and last
  name as optional. If they are required again, Keycloak refuses password logins of users without
  them ("Account is not fully set up", `invalid_grant`), which `/auth` answers with `401`.
- **Issuer:** Keycloak runs without a fixed hostname, so `iss` names the host the client asked for
  the token. Clients must get tokens from the same host as `KEYCLOAK_URL` (`localhost`), or every
  token is rejected with `401`.
- **Rights:** reading recipes needs `user`; creating, replacing and renaming them needs
  `moderator`. Ask before assuming the group for new operations.

The realm and its client are only stored in Keycloak's database inside the `postgres_data` Docker
volume, so `docker compose ... down -v` deletes them.
