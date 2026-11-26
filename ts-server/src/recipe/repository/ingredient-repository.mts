/**
 * Database access for the ingredients of a recipe.
 *
 * Every function is scoped to one recipe, so an ingredient id of another recipe is never touched.
 * None of them changes the recipe's version: call `incrementVersion` of the recipe repository in
 * the same transaction.
 */

import { and, asc, eq, notInArray, sql } from 'drizzle-orm';

import { db } from '../db/index.mts';
import { ingredient } from '../db/schema.mts';
import type { IngredientSelect } from '../dto/ingredient-dto.mts';
import type { Executor } from './executor.mts';

/**
 * The fields of an ingredient; id and version are generated, the recipe is passed separately.
 * `amount` is a decimal string such as `'400.5'`, to keep the exact `numeric` value.
 */
export type IngredientInsert = Omit<typeof ingredient.$inferInsert, 'id' | 'recipeId' | 'version'>;

/** The ingredients of a recipe, ordered by name. */
export const findByRecipeId = async (
  recipeId: string,
  ex: Executor = db,
): Promise<IngredientSelect[]> =>
  await ex
    .select()
    .from(ingredient)
    .where(eq(ingredient.recipeId, recipeId))
    .orderBy(asc(ingredient.name));

/** Adds ingredients to a recipe. Returns the new rows. */
export const insertMany = async (
  recipeId: string,
  ingredients: readonly IngredientInsert[],
  ex: Executor = db,
): Promise<IngredientSelect[]> => {
  if (ingredients.length === 0) {
    return [];
  }
  return await ex
    .insert(ingredient)
    .values(ingredients.map((ing) => ({ ...ing, recipeId })))
    .returning();
};

/**
 * Changes an ingredient of the recipe and increments the ingredient's version.
 *
 * @param expectedVersion only update if the ingredient's version is still this one;
 *   `undefined` updates unconditionally.
 * @returns the updated row, or `undefined` if the recipe has no such ingredient or its version is
 *   not `expectedVersion`.
 */
export const update = async (
  recipeId: string,
  id: string,
  fields: Partial<IngredientInsert>,
  expectedVersion: number | undefined,
  ex: Executor = db,
): Promise<IngredientSelect | undefined> => {
  const [row] = await ex
    .update(ingredient)
    .set({ ...fields, version: sql`${ingredient.version} + 1` })
    .where(
      and(
        eq(ingredient.recipeId, recipeId),
        eq(ingredient.id, id),
        expectedVersion === undefined ? undefined : eq(ingredient.version, expectedVersion),
      ),
    )
    .returning();
  return row;
};

/**
 * Deletes all ingredients of the recipe except those in `keepIds` (all of them if it is empty),
 * as when the recipe is replaced. Returns the number of deleted ingredients.
 */
export const deleteByRecipeIdExcept = async (
  recipeId: string,
  keepIds: readonly string[],
  ex: Executor = db,
): Promise<number> => {
  const rows = await ex
    .delete(ingredient)
    .where(
      and(
        eq(ingredient.recipeId, recipeId),
        keepIds.length === 0 ? undefined : notInArray(ingredient.id, [...keepIds]),
      ),
    )
    .returning({ id: ingredient.id });
  return rows.length;
};
