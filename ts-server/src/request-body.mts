/** Reading JSON request bodies, shared by all routers. */

import type { Context } from 'hono';

/** The request body is not valid JSON (400). */
export class BadRequestError extends Error {}

/**
 * The request body as JSON; validate it with Zod afterwards.
 * @throws BadRequestError if the body is not valid JSON.
 */
export const readJson = async (c: Context): Promise<unknown> =>
  await c.req.json().catch(() => {
    throw new BadRequestError('The request body is not valid JSON.');
  });
