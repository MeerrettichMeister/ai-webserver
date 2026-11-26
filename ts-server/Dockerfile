# Image of the ts-server; build context is ts-server/ (see scripts/docker-compose.yaml).
# Configuration comes from environment variables (as in .env, which is not copied), and the TLS
# certificate from a volume at /app/tls (key.pem, cert.pem). Run `pnpm db:migrate` against the
# database before the first start; the image does not migrate, and refuses to start without it.

ARG NODE_VERSION=26

FROM node:${NODE_VERSION}-alpine AS base
WORKDIR /app
# Node 25+ no longer ships Corepack.
RUN npm install --global pnpm@12.21.0
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

FROM base AS prod-deps
RUN pnpm install --prod --frozen-lockfile

FROM base AS build
RUN pnpm install --frozen-lockfile
COPY tsconfig.json ./
COPY src ./src
RUN pnpm build

FROM node:${NODE_VERSION}-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=prod-deps /app/package.json ./
COPY --from=prod-deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
# For the startup check that the database is at the newest migration.
COPY drizzle/meta/_journal.json ./drizzle/meta/
USER node
EXPOSE 3000
CMD ["node", "dist/index.mjs"]
