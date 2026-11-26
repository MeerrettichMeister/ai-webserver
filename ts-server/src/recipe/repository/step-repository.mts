/**
 * Database access for the steps of a recipe.
 *
 * Every function is scoped to one recipe, so a step id of another recipe is never touched.
 * None of them changes the recipe's version: call `incrementVersion` of the recipe repository in
 * the same transaction.
 */

import { and, asc, eq, inArray, notInArray, sql } from 'drizzle-orm';

import { db } from '../db/index.mts';
import { step } from '../db/schema.mts';
import type { StepSelect } from '../dto/step-dto.mts';
import type { Executor } from './executor.mts';

/** The fields of a step; id and version are generated, the recipe is passed separately. */
export type StepInsert = Omit<typeof step.$inferInsert, 'id' | 'recipeId' | 'version'>;

/** The steps of a recipe in the order they are performed. */
export const findByRecipeId = async (recipeId: string, ex: Executor = db): Promise<StepSelect[]> =>
  await ex.select().from(step).where(eq(step.recipeId, recipeId)).orderBy(asc(step.position));

/** Adds steps to a recipe. Returns the new rows. */
export const insertMany = async (
  recipeId: string,
  steps: readonly StepInsert[],
  ex: Executor = db,
): Promise<StepSelect[]> => {
  if (steps.length === 0) {
    return [];
  }
  return await ex
    .insert(step)
    .values(steps.map((s) => ({ ...s, recipeId })))
    .returning();
};

/**
 * Changes a step of the recipe and increments the step's version.
 *
 * @param expectedVersion only update if the step's version is still this one (e.g. from
 *   `If-Match`); `undefined` updates unconditionally.
 * @returns the updated row, or `undefined` if the recipe has no such step or its version is not
 *   `expectedVersion`.
 */
export const update = async (
  recipeId: string,
  id: string,
  fields: Partial<StepInsert>,
  expectedVersion: number | undefined,
  ex: Executor = db,
): Promise<StepSelect | undefined> => {
  const [row] = await ex
    .update(step)
    .set({ ...fields, version: sql`${step.version} + 1` })
    .where(
      and(
        eq(step.recipeId, recipeId),
        eq(step.id, id),
        expectedVersion === undefined ? undefined : eq(step.version, expectedVersion),
      ),
    )
    .returning();
  return row;
};

/**
 * Negates the positions of the given steps of the recipe. `(recipe_id, position)` is unique and
 * the constraint is checked per row, so reordering steps in place (e.g. swapping 1 and 2) fails;
 * call this first for the steps that move, in the same transaction, then {@linkcode update} each
 * of them to its new position.
 */
export const releasePositions = async (
  recipeId: string,
  ids: readonly string[],
  ex: Executor = db,
): Promise<void> => {
  if (ids.length === 0) {
    return;
  }
  await ex
    .update(step)
    .set({ position: sql`-${step.position}` })
    .where(and(eq(step.recipeId, recipeId), inArray(step.id, [...ids])));
};

/**
 * Deletes all steps of the recipe except those in `keepIds` (all of them if it is empty), as
 * when the recipe is replaced. Returns the number of deleted steps.
 */
export const deleteByRecipeIdExcept = async (
  recipeId: string,
  keepIds: readonly string[],
  ex: Executor = db,
): Promise<number> => {
  const rows = await ex
    .delete(step)
    .where(
      and(
        eq(step.recipeId, recipeId),
        keepIds.length === 0 ? undefined : notInArray(step.id, [...keepIds]),
      ),
    )
    .returning({ id: step.id });
  return rows.length;
};
