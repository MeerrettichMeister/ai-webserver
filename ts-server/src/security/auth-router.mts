/**
 * Login, mounted at `/auth`. The only endpoint that needs no token, since it is how clients get
 * one. The server forwards the credentials to Keycloak and never stores or logs them.
 */

import { Hono } from 'hono';
import { z } from 'zod';

import { BadRequestError } from '../recipe/router/errors.mts';
import { login } from './keycloak-service.mts';

export const router = new Hono();

const LoginSchema = z.compile(
  z.strictObject({
    username: z.string().min(1),
    password: z.string().min(1),
  }),
);

/**
 * `POST /auth` with `{ "username": ..., "password": ... }`: `200` with the tokens from Keycloak
 * (`access_token`, `expires_in`, `refresh_token`, ...), `401` for wrong credentials.
 */
router.post('/', async (c) => {
  let body: unknown;
  try {
    body = await c.req.json();
  } catch {
    throw new BadRequestError('The request body is not valid JSON.');
  }
  const { username, password } = LoginSchema.parse(body);
  const tokens = await login(username, password);
  // Tokens must not end up in shared caches.
  c.header('Cache-Control', 'no-store');
  return c.json(tokens);
});
