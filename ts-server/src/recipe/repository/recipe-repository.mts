/**
 * Database access for recipes and their details (1:1, so they share this repository).
 *
 * The functions return Drizzle rows; building DTOs is up to the service. Ids must be valid UUIDs,
 * otherwise PostgreSQL rejects the query: validate them before calling.
 */

import { and, asc, eq, ilike, sql } from 'drizzle-orm';

import { db } from '../db/index.mts';
import { recipe, recipeDetails } from '../db/schema.mts';
import type { RecipeDetailsSelect } from '../dto/recipe-details-dto.mts';
import type { RecipeSelect } from '../dto/recipe-dto.mts';
import type { Executor } from './executor.mts';

/** A new recipe; id and version are generated. */
export type RecipeInsert = Omit<typeof recipe.$inferInsert, 'id' | 'version'>;
/** The details of a recipe, without the foreign key. */
export type RecipeDetailsInsert = Omit<typeof recipeDetails.$inferInsert, 'recipeId'>;

export type RecipeWithDetailsSelect = { recipe: RecipeSelect; details: RecipeDetailsSelect };

/** Escapes `%`, `_` and `\` so that a search term matches literally in `LIKE`/`ILIKE`. */
const escapeLike = (term: string): string => term.replaceAll(/[\\%_]/gu, String.raw`\$&`);

// =============================================================================
// R E A D
// =============================================================================

/**
 * All recipes, ordered by name (then id), optionally only those whose name contains `search`,
 * ignoring case.
 */
export const findAll = async (search = '', ex: Executor = db): Promise<RecipeSelect[]> =>
  await ex
    .select()
    .from(recipe)
    .where(search === '' ? undefined : ilike(recipe.name, `%${escapeLike(search)}%`))
    .orderBy(asc(recipe.name), asc(recipe.id));

/** The recipe with its details, or `undefined` if there is none with this id. */
export const findById = async (
  id: string,
  ex: Executor = db,
): Promise<RecipeWithDetailsSelect | undefined> => {
  const [row] = await ex
    .select({ recipe, details: recipeDetails })
    .from(recipe)
    .innerJoin(recipeDetails, eq(recipeDetails.recipeId, recipe.id))
    .where(eq(recipe.id, id))
    .limit(1);
  return row;
};

/** The current version of the recipe, or `undefined` if there is none with this id. */
export const findVersionById = async (
  id: string,
  ex: Executor = db,
): Promise<number | undefined> => {
  const [row] = await ex
    .select({ version: recipe.version })
    .from(recipe)
    .where(eq(recipe.id, id))
    .limit(1);
  return row?.version;
};

// =============================================================================
// W R I T E
// =============================================================================

/** Inserts a recipe together with its details, atomically. Returns the new recipe row. */
export const insert = async (
  newRecipe: RecipeInsert,
  details: RecipeDetailsInsert,
  ex: Executor = db,
): Promise<RecipeSelect> =>
  await ex.transaction(async (tx) => {
    const [row] = await tx.insert(recipe).values(newRecipe).returning();
    if (row === undefined) {
      throw new Error('INSERT into recipe returned no row');
    }
    await tx.insert(recipeDetails).values({ ...details, recipeId: row.id });
    return row;
  });

/**
 * Increments the recipe's version. The version covers the whole aggregate, so call this on every
 * write to the recipe, its details, ingredients or steps, inside the same transaction as the
 * write. The `UPDATE` also locks the row until that transaction ends.
 *
 * @param expectedVersion only increment if the version is still this one (optimistic locking,
 *   e.g. from `If-Match`); `undefined` increments unconditionally.
 * @returns the new version, or `undefined` if there is no such recipe or its version is not
 *   `expectedVersion` (tell them apart with {@linkcode findVersionById}).
 */
export const incrementVersion = async (
  id: string,
  expectedVersion: number | undefined,
  ex: Executor = db,
): Promise<number | undefined> => {
  const [row] = await ex
    .update(recipe)
    .set({ version: sql`${recipe.version} + 1` })
    .where(
      expectedVersion === undefined
        ? eq(recipe.id, id)
        : and(eq(recipe.id, id), eq(recipe.version, expectedVersion)),
    )
    .returning({ version: recipe.version });
  return row?.version;
};

/** Renames the recipe. Does not touch the version: see {@linkcode incrementVersion}. */
export const updateName = async (id: string, name: string, ex: Executor = db): Promise<boolean> => {
  const rows = await ex
    .update(recipe)
    .set({ name })
    .where(eq(recipe.id, id))
    .returning({ id: recipe.id });
  return rows.length > 0;
};

/** Replaces the recipe's details. Does not touch the version: see {@linkcode incrementVersion}. */
export const updateDetails = async (
  id: string,
  details: RecipeDetailsInsert,
  ex: Executor = db,
): Promise<boolean> => {
  const rows = await ex
    .update(recipeDetails)
    .set(details)
    .where(eq(recipeDetails.recipeId, id))
    .returning({ recipeId: recipeDetails.recipeId });
  return rows.length > 0;
};

/**
 * Deletes the recipe; its details, ingredients and steps go with it (`ON DELETE CASCADE`).
 * @returns whether there was such a recipe.
 */
export const deleteById = async (id: string, ex: Executor = db): Promise<boolean> => {
  const rows = await ex.delete(recipe).where(eq(recipe.id, id)).returning({ id: recipe.id });
  return rows.length > 0;
};
