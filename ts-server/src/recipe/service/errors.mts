/** Errors of the recipe services; `app.mts` turns them into HTTP responses. */

/** There is no recipe with the requested id (404). */
export class NotFoundError extends Error {}

/** The recipe's version is not one the client named in `If-Match` (412). */
export class PreconditionFailedError extends Error {}

/** The request names an ingredient or step id the recipe does not have (422). */
export class InvalidReferenceError extends Error {}
