import 'dotenv/config';
import { readFileSync } from 'node:fs';
import { createSecureServer } from 'node:http2';
import process from 'node:process';

import { serve } from '@hono/node-server';

import { app } from './app.mts';
import { db } from './recipe/db/index.mts';
import { checkMigrations } from './recipe/db/migrations-check.mts';

const port = Number(process.env.PORT ?? 3000);

// Refuse to start on a database that is not at the newest migration.
try {
  await checkMigrations();
} catch (error) {
  // Drizzle's message only names the failed query; the cause says why (e.g. ECONNREFUSED).
  const { cause } = error as { cause?: unknown };
  console.error(error instanceof Error ? error.message : error);
  if (cause !== undefined) {
    console.error('Cause:', cause instanceof Error ? cause.message || cause.name : cause);
  }
  await db.$client.end();
  process.exit(1);
}

// Self-signed development certificate for localhost (see CLAUDE.md), relative to src/ and dist/.
const tlsDir = new URL('../tls/', import.meta.url);

// HTTP/2 over TLS: browsers only use HTTP/2 with TLS. Clients agree on the protocol in the TLS
// handshake (ALPN); `allowHTTP1` still serves clients that only speak HTTP/1.1.
const server = serve(
  {
    fetch: app.fetch,
    port,
    createServer: createSecureServer,
    serverOptions: {
      key: readFileSync(new URL('key.pem', tlsDir)),
      cert: readFileSync(new URL('cert.pem', tlsDir)),
      // Node's default minimum, TLS 1.2, is kept on purpose: Windows 10's TLS stack (Schannel,
      // used by its curl.exe and PowerShell) has no TLS 1.3. HTTP/2 itself needs TLS 1.2+.
      allowHTTP1: true,
    },
  },
  (info) => {
    console.log(`Listening on https://localhost:${info.port} (HTTP/2, HTTP/1.1 as fallback)`);
  },
);

const shutdown = (): void => {
  server.close(() => {
    db.$client.end().catch((error: unknown) => console.error(error));
  });
};
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
