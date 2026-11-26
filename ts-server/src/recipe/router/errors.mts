/** Errors of the recipe router; `app.mts` turns them into HTTP responses. */

/** A write without the `If-Match` header (428). */
export class PreconditionRequiredError extends Error {}
