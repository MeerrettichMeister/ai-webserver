import { z } from 'zod';

import { ReadOnlyTimestamps } from './read-only-fields.mts';

/** What to do in a step. Surrounding whitespace is stripped; then 1 to 1000 characters. */
export const PreparationMethodSchema = z.string().trim().min(1).max(1000);

const StepSchema = z.strictObject({
  /** UUID of an existing step. */
  id: z.uuid(),
  preparation_method: PreparationMethodSchema,
});

/**
 * A step of a replaced recipe: updated if it has an `id`, otherwise added. It may also have the
 * read-only `version`, `position` and timestamps of `GET /recipes/:id`, so that its response can be
 * sent back changed; they are ignored: the `If-Match` of the recipe is what counts, and the steps
 * are numbered in the order of the array.
 */
export const StepReplaceSchema = StepSchema.partial({ id: true }).extend({
  version: z.int().gte(0).optional(),
  position: z.int().gte(1).optional(),
  ...ReadOnlyTimestamps,
});

/** Request body to change one step. */
export const StepUpdateSchema = z.compile(StepSchema.omit({ id: true })).readonly();

export type StepReplaceType = z.infer<typeof StepReplaceSchema>;
export type StepUpdateType = z.infer<typeof StepUpdateSchema>;
