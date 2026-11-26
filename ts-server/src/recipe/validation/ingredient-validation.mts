import { z } from 'zod';

import { ReadOnlyTimestamps } from './read-only-fields.mts';

const IngredientSchema = z.strictObject({
  /** UUID of an existing ingredient. */
  id: z.uuid(),
  /** Name of the ingredient. */
  ingredient: z.string().min(1).max(255),
  /** Fits `numeric(10, 3)`: greater than 0, at most 7 integer and 3 decimal digits. */
  amount: z.number().gt(0).lt(10_000_000).multipleOf(0.001),
  unit: z.string().max(50),
});

/** An ingredient of a new recipe. */
export const IngredientCreateSchema = IngredientSchema.omit({ id: true });

/**
 * An ingredient of a replaced recipe: updated if it has an `id`, otherwise added. It may also have
 * the read-only `version` and timestamps of `GET /recipes/:id`, so that its response can be sent
 * back changed; they are ignored (the `If-Match` of the recipe is what counts).
 */
export const IngredientReplaceSchema = IngredientSchema.partial({ id: true }).extend({
  version: z.int().gte(0).optional(),
  ...ReadOnlyTimestamps,
});

export type IngredientCreateType = z.infer<typeof IngredientCreateSchema>;
