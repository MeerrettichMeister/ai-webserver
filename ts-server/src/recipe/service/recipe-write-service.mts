/**
 * Creating and changing recipes. Every change runs in one transaction and increments the recipe's
 * version, which covers the whole recipe.
 */

import type { ExpectedVersion } from '../../etag.mts';
import { matches } from '../../etag.mts';
import { db } from '../db/index.mts';
import type { RecipeDTO } from '../dto/recipe-dto.mts';
import type { Executor } from '../repository/executor.mts';
import * as ingredientRepository from '../repository/ingredient-repository.mts';
import type { IngredientInsert } from '../repository/ingredient-repository.mts';
import * as recipeRepository from '../repository/recipe-repository.mts';
import type { RecipeDetailsInsert } from '../repository/recipe-repository.mts';
import * as stepRepository from '../repository/step-repository.mts';
import type { IngredientCreateType } from '../validation/ingredient-validation.mts';
import type { RecipeDetailsType } from '../validation/recipe-details-validation.mts';
import type {
  RecipeCreateType,
  RecipeReplaceType,
  RecipeUpdateType,
} from '../validation/recipe-validation.mts';
import { InvalidReferenceError, NotFoundError, PreconditionFailedError } from './errors.mts';
import { loadRecipe } from './recipe-service.mts';

// =============================================================================
// M a p p i n g   ( A P I   f i e l d s   ->   c o l u m n s )
// =============================================================================

const toDetailsInsert = (details: RecipeDetailsType): RecipeDetailsInsert => ({
  servings: details.servings,
  preparationTimeMinutes: details.preparation_time_minutes,
  difficulty: details.difficulty,
});

const toIngredientInsert = ({
  ingredient,
  amount,
  unit,
}: IngredientCreateType): IngredientInsert => ({
  name: ingredient,
  // The validation allows at most 3 decimal places and less than 10^7, so no exponent notation.
  amount: String(amount),
  unit,
});

// =============================================================================
// V e r s i o n
// =============================================================================

/**
 * Checks the recipe's version against `If-Match` and increments it, which also locks the recipe
 * until the transaction ends.
 * @throws NotFoundError if there is no recipe with this id.
 * @throws PreconditionFailedError if its version is not one in `expected`.
 */
const incrementVersion = async (
  id: string,
  expected: ExpectedVersion,
  tx: Executor,
): Promise<void> => {
  const current = await recipeRepository.findVersionById(id, tx);
  if (current === undefined) {
    throw new NotFoundError(`There is no recipe with id ${id}.`);
  }
  if (!matches(expected, current)) {
    throw new PreconditionFailedError(`The recipe's current version is ${current}.`);
  }
  // Conditional on `current`: fails if another request changed the recipe in between.
  if ((await recipeRepository.incrementVersion(id, current, tx)) === undefined) {
    throw new PreconditionFailedError('The recipe was changed concurrently.');
  }
};

/** @throws InvalidReferenceError if an id is not one of `existingIds`. */
const checkReferences = (
  kind: 'ingredient' | 'step',
  ids: readonly string[],
  existingIds: ReadonlySet<string>,
): void => {
  const unknown = ids.filter((id) => !existingIds.has(id));
  if (unknown.length > 0) {
    throw new InvalidReferenceError(`The recipe has no ${kind} with id ${unknown.join(', ')}.`);
  }
};

// =============================================================================
// C r e a t e
// =============================================================================

/**
 * Creates a recipe with its details, ingredients and steps (numbered in list order).
 * @returns the id of the new recipe.
 */
export const create = async (newRecipe: RecipeCreateType): Promise<string> =>
  await db.transaction(async (tx) => {
    const { id } = await recipeRepository.insert(
      { name: newRecipe.name },
      toDetailsInsert(newRecipe.details),
      tx,
    );
    await ingredientRepository.insertMany(id, newRecipe.ingredients.map(toIngredientInsert), tx);
    await stepRepository.insertMany(
      id,
      newRecipe.steps.map((preparationMethod, i) => ({ position: i + 1, preparationMethod })),
      tx,
    );
    return id;
  });

// =============================================================================
// U p d a t e   ( r e n a m e )
// =============================================================================

/**
 * Renames a recipe.
 * @throws NotFoundError, PreconditionFailedError (see `incrementVersion`).
 */
export const update = async (
  id: string,
  { name }: RecipeUpdateType,
  expected: ExpectedVersion,
): Promise<RecipeDTO> =>
  await db.transaction(async (tx) => {
    await incrementVersion(id, expected, tx);
    await recipeRepository.updateName(id, name, tx);
    return await loadRecipe(id, tx);
  });

// =============================================================================
// R e p l a c e
// =============================================================================

/**
 * Ingredients with an id are updated (only if they changed, so the others keep their version),
 * those without one are added, and the recipe's other ingredients are deleted.
 */
const replaceIngredients = async (
  recipeId: string,
  ingredients: RecipeReplaceType['ingredients'],
  tx: Executor,
): Promise<void> => {
  const existing = new Map(
    (await ingredientRepository.findByRecipeId(recipeId, tx)).map((row) => [row.id, row]),
  );
  const keptIds = ingredients.flatMap(({ id }) => (id === undefined ? [] : [id]));
  checkReferences('ingredient', keptIds, new Set(existing.keys()));

  await ingredientRepository.deleteByRecipeIdExcept(recipeId, keptIds, tx);
  for (const ingredient of ingredients) {
    const current = ingredient.id === undefined ? undefined : existing.get(ingredient.id);
    if (current === undefined) {
      continue;
    }
    const fields = toIngredientInsert(ingredient);
    const changed =
      current.name !== fields.name ||
      Number(current.amount) !== ingredient.amount ||
      current.unit !== fields.unit;
    if (changed) {
      // oxlint-disable-next-line no-await-in-loop -- one transaction runs one query at a time
      await ingredientRepository.update(recipeId, current.id, fields, undefined, tx);
    }
  }
  await ingredientRepository.insertMany(
    recipeId,
    ingredients.filter(({ id }) => id === undefined).map(toIngredientInsert),
    tx,
  );
};

/**
 * Steps are renumbered in list order. Steps with an id are updated (only if their text or
 * position changed), those without one are added, and the recipe's other steps are deleted.
 */
const replaceSteps = async (
  recipeId: string,
  steps: RecipeReplaceType['steps'],
  tx: Executor,
): Promise<void> => {
  const existing = new Map(
    (await stepRepository.findByRecipeId(recipeId, tx)).map((row) => [row.id, row]),
  );
  const keptIds = steps.flatMap(({ id }) => (id === undefined ? [] : [id]));
  checkReferences('step', keptIds, new Set(existing.keys()));

  await stepRepository.deleteByRecipeIdExcept(recipeId, keptIds, tx);
  const targets = steps.map((s, i) => ({
    ...s,
    position: i + 1,
    current: s.id === undefined ? undefined : existing.get(s.id),
  }));
  // Free the positions of the steps that move, so they can take each other's places.
  const moving = targets.flatMap(({ current, position }) =>
    current !== undefined && current.position !== position ? [current.id] : [],
  );
  await stepRepository.releasePositions(recipeId, moving, tx);

  for (const { current, position, preparation_method: preparationMethod } of targets) {
    if (
      current !== undefined &&
      (current.position !== position || current.preparationMethod !== preparationMethod)
    ) {
      // oxlint-disable-next-line no-await-in-loop -- one transaction runs one query at a time
      await stepRepository.update(
        recipeId,
        current.id,
        { position, preparationMethod },
        undefined,
        tx,
      );
    }
  }
  await stepRepository.insertMany(
    recipeId,
    targets.flatMap(({ id, position, preparation_method: preparationMethod }) =>
      id === undefined ? [{ position, preparationMethod }] : [],
    ),
    tx,
  );
};

/**
 * Replaces the whole recipe: name, details, ingredients and steps.
 * @throws NotFoundError, PreconditionFailedError (see `incrementVersion`).
 * @throws InvalidReferenceError if an ingredient or step id is not one of the recipe's.
 */
export const replace = async (
  id: string,
  recipe: RecipeReplaceType,
  expected: ExpectedVersion,
): Promise<RecipeDTO> =>
  await db.transaction(async (tx) => {
    await incrementVersion(id, expected, tx);
    await recipeRepository.updateName(id, recipe.name, tx);
    await recipeRepository.updateDetails(id, toDetailsInsert(recipe.details), tx);
    await replaceIngredients(id, recipe.ingredients, tx);
    await replaceSteps(id, recipe.steps, tx);
    return await loadRecipe(id, tx);
  });
