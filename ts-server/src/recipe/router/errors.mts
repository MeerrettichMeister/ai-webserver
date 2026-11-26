/** Errors of the recipe router; `app.mts` turns them into HTTP responses. */

/** The request body is not valid JSON (400). */
export class BadRequestError extends Error {}

/** A write without the `If-Match` header (428). */
export class PreconditionRequiredError extends Error {}
