/** Errors of the login (`/auth`); `app.mts` turns them into HTTP responses. */

/** Keycloak rejected the username or password (401). */
export class InvalidCredentialsError extends Error {}

/** Keycloak could not be reached or answered with an unexpected error (502). */
export class KeycloakError extends Error {}
