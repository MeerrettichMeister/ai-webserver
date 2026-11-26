/**
 * Logging in at Keycloak: exchanges a username and password for tokens with the Resource Owner
 * Password Credentials grant of the client `ts-server` ("Direct access grants" in Keycloak).
 */

import { InvalidCredentialsError, KeycloakError } from './errors.mts';
import { clientId, tokenUri } from './keycloak-config.mts';

/** The tokens of a successful login, as Keycloak returns them (OAuth 2.0 token response). */
export type TokenResponse = {
  /** Send as `Authorization: Bearer <access_token>`. */
  readonly access_token: string;
  readonly token_type: string;
  /** Seconds until the access token expires. */
  readonly expires_in: number;
  /** Gets new tokens from Keycloak without the password while it is valid. */
  readonly refresh_token: string;
  /** Seconds until the refresh token expires. */
  readonly refresh_expires_in: number;
};

/**
 * Logs the user in at Keycloak.
 * @throws InvalidCredentialsError if Keycloak rejects the credentials.
 * @throws KeycloakError if Keycloak is unreachable or fails otherwise.
 */
export const login = async (username: string, password: string): Promise<TokenResponse> => {
  let response: Response;
  try {
    response = await fetch(tokenUri, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'password',
        client_id: clientId,
        username,
        password,
      }),
    });
  } catch (error) {
    throw new KeycloakError('Keycloak is not reachable.', { cause: error });
  }

  const body = (await response.json().catch(() => ({}))) as Record<string, unknown>;
  if (response.ok) {
    const { access_token, token_type, expires_in, refresh_token, refresh_expires_in } =
      body as TokenResponse;
    return { access_token, token_type, expires_in, refresh_token, refresh_expires_in };
  }
  // Wrong username or password: 401. A disabled account or one with pending required actions
  // (e.g. "update password"): 400. Both come as `invalid_grant`.
  if (body.error === 'invalid_grant') {
    throw new InvalidCredentialsError('Invalid username or password.');
  }
  throw new KeycloakError(
    `Keycloak answered the login with ${response.status}: ${String(body.error ?? 'no error code')}.`,
  );
};
