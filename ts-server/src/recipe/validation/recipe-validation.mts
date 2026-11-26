import { z } from 'zod';

import { IngredientCreateSchema, IngredientReplaceSchema } from './ingredient-validation.mts';
import { RecipeDetailsSchema } from './recipe-details-validation.mts';
import { PreparationMethodSchema, StepReplaceSchema } from './step-validation.mts';

const isUnique = (values: readonly unknown[]): boolean => new Set(values).size === values.length;

const definedIds = (items: readonly { id?: string | undefined }[]): string[] =>
  items.flatMap(({ id }) => (id === undefined ? [] : [id]));

const RecipeSchema = z.strictObject({
  /** UUID. */
  id: z.uuid(),
  name: z.string().min(1).max(255),
  details: RecipeDetailsSchema,
});

/**
 * Request body for a new recipe; the seed recipe `seed/Pfannkuchen.json` of the py-server is an
 * example. Ingredient names must be unique.
 */
export const RecipeCreateSchema = z
  .compile(
    RecipeSchema.omit({ id: true })
      .extend({
        ingredients: z.array(IngredientCreateSchema).default([]),
        /** Instructions in the order they are performed. */
        steps: z.array(PreparationMethodSchema).default([]),
      })
      .refine(({ ingredients }) => isUnique(ingredients.map((i) => i.ingredient)), {
        message: 'Ingredient names must be unique',
        path: ['ingredients'],
      }),
  )
  .readonly();

/** Request body to rename a recipe. */
export const RecipeUpdateSchema = z.compile(RecipeSchema.pick({ name: true })).readonly();

/**
 * Request body with the complete recipe: ingredients and steps left out are deleted.
 * Ingredient names must be unique, and so must the ids of the ingredients and of the steps.
 *
 * The response of `GET /recipes/:id` is accepted as it is, so clients can change it and send it
 * back: its `id` must then be the one in the URL, and the read-only `version`s and step
 * `position`s are ignored (`If-Match` and the order of `steps` count).
 */
export const RecipeReplaceSchema = z
  .compile(
    RecipeSchema.partial({ id: true })
      .extend({
        version: z.int().gte(0).optional(),
        ingredients: z.array(IngredientReplaceSchema).default([]),
        /** Steps in the order they are performed. */
        steps: z.array(StepReplaceSchema).default([]),
      })
      .refine(({ ingredients }) => isUnique(ingredients.map((i) => i.ingredient)), {
        message: 'Ingredient names must be unique',
        path: ['ingredients'],
      })
      .refine(({ ingredients }) => isUnique(definedIds(ingredients)), {
        message: 'Ingredient ids must be unique',
        path: ['ingredients'],
      })
      .refine(({ steps }) => isUnique(definedIds(steps)), {
        message: 'Step ids must be unique',
        path: ['steps'],
      }),
  )
  .readonly();

export type RecipeCreateType = z.infer<typeof RecipeCreateSchema>;
export type RecipeUpdateType = z.infer<typeof RecipeUpdateSchema>;
export type RecipeReplaceType = z.infer<typeof RecipeReplaceSchema>;
