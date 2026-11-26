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
 * An error response as Problem Details for HTTP APIs (RFC 9457), `application/problem+json`.
 *
 * `type` is `about:blank`: the problem is just the HTTP status, so `title` is its reason phrase
 * (RFC 9457, section 4.2.1). `instance` is the path of the request.
 *
 * @param detail a human-readable explanation of this occurrence; RFC 9457 requires a string.
 * @param extensions further members, e.g. `errors` with the issues of a failed validation.
 */
export const createProblemDetails = (
  c: Context,
  status: ContentfulStatusCode,
  detail?: string,
  extensions: Record<string, unknown> = {},
): Response => {
  const problem = {
    ...extensions,
    type: 'about:blank',
    title: TITLES[status] ?? 'Error',
    status,
    detail,
    instance: c.req.path,
  };
  const response = c.json(problem, status);
  response.headers.set('Content-Type', 'application/problem+json');
  return response;
};
