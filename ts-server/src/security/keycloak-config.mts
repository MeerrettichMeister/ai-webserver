/** Where the Keycloak realm of this app is, from `.env`. */

import 'dotenv/config';
import process from 'node:process';

const host = process.env.KEYCLOAK_URL ?? 'localhost';
const port = process.env.KEYCLOAK_PORT ?? '8080';
const realm = process.env.KEYCLOAK_REALM ?? 'ai-webserver';

/** The Keycloak client of this API: it must be in the tokens' `aud`, and `/auth` logs in with it. */
export const clientId = process.env.KEYCLOAK_CLIENT_ID ?? 'ts-server';

/**
 * The realm's URL, which is also the `iss` of its tokens. Keycloak runs without a fixed hostname,
 * so `iss` names the host the client asked for the token: clients must use this same host.
 */
export const issuer = `http://${host}:${port}/realms/${realm}`;

export const jwksUri = `${issuer}/protocol/openid-connect/certs`;
export const tokenUri = `${issuer}/protocol/openid-connect/token`;
