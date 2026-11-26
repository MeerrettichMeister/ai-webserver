import 'dotenv/config';
import process from 'node:process';

import { serve } from '@hono/node-server';

import { app } from './app.mts';
import { db } from './recipe/db/index.mts';

const port = Number(process.env.PORT ?? 3000);

const server = serve({ fetch: app.fetch, port }, (info) => {
  console.log(`Listening on http://localhost:${info.port}`);
});

const shutdown = (): void => {
  server.close(() => {
    db.$client.end().catch((error: unknown) => console.error(error));
  });
};
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
