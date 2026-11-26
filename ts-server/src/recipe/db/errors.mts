/**
 * Whether a failed query violated a unique constraint or primary key (PostgreSQL's
 * `unique_violation`), e.g. two ingredients of a recipe with the same name. Drizzle wraps the
 * driver's error, which has the SQLSTATE `code`, in `cause`.
 */
export const isUniqueViolation = (error: unknown): boolean =>
  error instanceof Error && (error.cause as { code?: unknown } | undefined)?.code === '23505';
