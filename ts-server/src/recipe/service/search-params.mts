/** Search criteria of the recipe list (query parameters besides `page` and `size`). */
export type SearchParams = {
  /** Only recipes whose name contains this, ignoring case. Empty or missing: all recipes. */
  readonly search?: string;
};
