/**
 * Authentication and authorization for every endpoint, kept in one place.
 *
 * Clients get an access token from Keycloak and send it as `Authorization: Bearer <token>`. The
 * server only verifies it (signature against the realm's JWKS, `exp`, issuer and audience) and
 * reads the user's groups from its `groups` claim, which the Group Membership mapper of the
 * Keycloak client fills with plain group names.
 */

import type { MiddlewareHandler } from 'hono';
import { every } from 'hono/combine';
import { createMiddleware } from 'hono/factory';
import { HTTPException } from 'hono/http-exception';
import { jwk } from 'hono/jwk';
import type { HonoJsonWebKey } from 'hono/utils/jwt/jws';

import { clientId, issuer, jwksUri } from './keycloak-config.mts';

/** The realm's signing keys are fetched at most this often (Keycloak may rotate them). */
const JWKS_CACHE_MS = 5 * 60 * 1000;
let cachedKeys: { keys: HonoJsonWebKey[]; fetchedAt: number } | undefined;

const getSigningKeys = async (): Promise<HonoJsonWebKey[]> => {
  if (cachedKeys !== undefined && Date.now() - cachedKeys.fetchedAt < JWKS_CACHE_MS) {
    return cachedKeys.keys;
  }
  const response = await fetch(jwksUri);
  if (!response.ok) {
    throw new Error(`Fetching the JWKS from ${jwksUri} failed: HTTP ${response.status}`);
  }
  const { keys } = (await response.json()) as { keys: (HonoJsonWebKey & { use?: string })[] };
  // The realm also publishes an encryption key; only signing keys verify tokens.
  const signingKeys = keys.filter(({ use }) => use === undefined || use === 'sig');
  cachedKeys = { keys: signingKeys, fetchedAt: Date.now() };
  return signingKeys;
};

/** Missing or invalid token: 401 (an `HTTPException` thrown by Hono's `jwk` middleware). */
const verifyToken = jwk({
  keys: getSigningKeys,
  alg: ['RS256'],
  verification: { iss: issuer, aud: clientId },
});

export type Group = 'user' | 'moderator';

/** The groups whose members have the rights of a group: a moderator may do all a user may. */
const GRANTED_TO: Record<Group, readonly Group[]> = {
  user: ['user', 'moderator'],
  moderator: ['moderator'],
};

/** The groups in the verified token; tolerates full paths (`/moderator`) as well. */
const groupsOf = (payload: unknown): string[] => {
  const { groups } = (payload ?? {}) as { groups?: unknown };
  if (!Array.isArray(groups)) {
    return [];
  }
  return groups
    .filter((group): group is string => typeof group === 'string')
    .map((group) => group.replace(/^\//u, ''));
};

const checkGroup = (group: Group): MiddlewareHandler =>
  createMiddleware(async (c, next) => {
    const groups = groupsOf(c.get('jwtPayload'));
    if (!GRANTED_TO[group].some((granted) => groups.includes(granted))) {
      throw new HTTPException(403, { message: `This requires the group "${group}".` });
    }
    await next();
  });

/**
 * Middleware for a route: the request needs a valid token (else 401) of a user in `group` or a
 * group with more rights (else 403). The verified claims are in `c.get('jwtPayload')`; take the
 * user's identity (`sub`) only from there.
 */
export const requireGroup = (group: Group): MiddlewareHandler =>
  every(verifyToken, checkGroup(group));
