import type { Context } from 'hono';
import type { ContentfulStatusCode } from 'hono/utils/http-status';

const TITLES: Partial<Record<ContentfulStatusCode, string>> = {
  400: 'Bad Request',
  401: 'Unauthorized',
  403: 'Forbidden',
  404: 'Not Found',
  409: 'Conflict',
  412: 'Precondition Failed',
  422: 'Unprocessable Content',
  428: 'Precondition Required',
  500: 'Internal Server Error',
  502: 'Bad Gateway',
};

/**
 * An error response as Problem Details for HTTP APIs (RFC 9457).
 *
 * @param detail what went wrong, e.g. a message or the issues of a failed validation.
 */
export const createProblemDetails = (
  c: Context,
  status: ContentfulStatusCode,
  detail?: unknown,
): Response => {
  const response = c.json({ title: TITLES[status] ?? 'Error', status, detail }, status);
  response.headers.set('Content-Type', 'application/problem+json');
  return response;
};
