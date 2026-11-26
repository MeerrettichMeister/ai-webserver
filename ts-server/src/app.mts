import { Hono } from 'hono';
import { HTTPException } from 'hono/http-exception';
import type { ContentfulStatusCode } from 'hono/utils/http-status';
import type { ZodError } from 'zod';

import { createProblemDetails } from './problem-details.mts';
import { isUniqueViolation } from './recipe/db/errors.mts';
import { PreconditionRequiredError } from './recipe/router/errors.mts';
import { router as recipeRouter } from './recipe/router/recipe-router.mts';
import {
  InvalidReferenceError,
  NotFoundError,
  PreconditionFailedError,
} from './recipe/service/errors.mts';
import { BadRequestError } from './request-body.mts';
import { router as authRouter } from './security/auth-router.mts';
import { InvalidCredentialsError, KeycloakError } from './security/errors.mts';

/** The web application: routes and the mapping of errors to HTTP responses. */
export const app = new Hono();

app.route('/auth', authRouter);
app.route('/recipes', recipeRouter);

app.notFound((c) =>
  createProblemDetails(c, 404, `There is no route ${c.req.method} ${c.req.path}.`),
);

// oxlint-disable-next-line promise/prefer-await-to-callbacks
app.onError((error, c) => {
  if (error instanceof HTTPException) {
    // E.g. 401 from the token verification and 403 from the group check (security/auth.mts).
    const response = createProblemDetails(
      c,
      error.status as ContentfulStatusCode,
      error.message || undefined,
    );
    const challenge = error.getResponse().headers.get('WWW-Authenticate');
    if (challenge !== null) {
      response.headers.set('WWW-Authenticate', challenge);
    }
    return response;
  }
  if (error instanceof NotFoundError) {
    return createProblemDetails(c, 404, error.message);
  }
  if (error instanceof BadRequestError) {
    return createProblemDetails(c, 400, error.message);
  }
  if (error.name === 'ZodError') {
    // RFC 9457: `detail` is a string; the individual issues go into the extension `errors`.
    const { issues } = error as ZodError;
    return createProblemDetails(c, 422, 'The request body is invalid.', {
      errors: issues.map(({ path, code, message }) => ({ path, code, message })),
    });
  }
  if (error instanceof InvalidReferenceError) {
    return createProblemDetails(c, 422, error.message);
  }
  if (error instanceof PreconditionRequiredError) {
    return createProblemDetails(c, 428, error.message);
  }
  if (error instanceof PreconditionFailedError) {
    return createProblemDetails(c, 412, error.message);
  }
  if (isUniqueViolation(error)) {
    return createProblemDetails(c, 409, 'The change conflicts with existing data of the recipe.');
  }
  if (error instanceof InvalidCredentialsError) {
    return createProblemDetails(c, 401, error.message);
  }
  if (error instanceof KeycloakError) {
    console.error(error);
    return createProblemDetails(c, 502, 'The login service is not available.');
  }

  console.error(error);
  // No internals in the response; the log has them.
  return createProblemDetails(c, 500, 'An unexpected error occurred.');
});
