/** Reading recipes. */

import { db } from '../db/index.mts';
import { RecipeDTO } from '../dto/recipe-dto.mts';
import type { Executor } from '../repository/executor.mts';
import * as ingredientRepository from '../repository/ingredient-repository.mts';
import * as recipeRepository from '../repository/recipe-repository.mts';
import * as stepRepository from '../repository/step-repository.mts';
import { NotFoundError } from './errors.mts';
import type { SearchParams } from './search-params.mts';

/** All recipes (without details, ingredients and steps), ordered by name. */
export const findAll = async ({ search }: SearchParams): Promise<RecipeDTO[]> => {
  const rows = await recipeRepository.findAll(search ?? '');
  return rows.map((row) => new RecipeDTO(row));
};

/**
 * Loads the recipe with its details, ingredients and steps using `ex`; the write service calls
 * it inside its transaction to return what it wrote.
 * @throws NotFoundError if there is no recipe with this id.
 */
export const loadRecipe = async (id: string, ex: Executor): Promise<RecipeDTO> => {
  const row = await recipeRepository.findById(id, ex);
  if (row === undefined) {
    throw new NotFoundError(`There is no recipe with id ${id}.`);
  }
  const ingredients = await ingredientRepository.findByRecipeId(id, ex);
  const steps = await stepRepository.findByRecipeId(id, ex);
  return new RecipeDTO(row.recipe, row.details, ingredients, steps);
};

/**
 * The recipe with its details, ingredients and steps. The queries share one snapshot, so the
 * parts always belong to the version returned.
 * @throws NotFoundError if there is no recipe with this id.
 */
export const findById = async (id: string): Promise<RecipeDTO> =>
  await db.transaction(async (tx) => await loadRecipe(id, tx), {
    isolationLevel: 'repeatable read',
    accessMode: 'read only',
  });
