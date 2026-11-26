import { z } from 'zod';

import { difficultyEnum } from '../db/schema.mts';

/** Servings, total time and difficulty of a recipe (part of a request body). */
export const RecipeDetailsSchema = z.strictObject({
  /** Number of portions the recipe makes. */
  servings: z.int().gte(1).lte(1000),
  /** Total time from start to serving, in minutes. */
  preparation_time_minutes: z.int().gte(1).lte(10_000),
  difficulty: z.enum(difficultyEnum.enumValues),
});

export type RecipeDetailsType = z.infer<typeof RecipeDetailsSchema>;
