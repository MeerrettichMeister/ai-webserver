/**
 * REST endpoints for recipes, mounted at `/recipes`. Reading requires the group `user`, writing
 * the group `moderator` (see `security/auth.mts`).
 */

import type { Context } from 'hono';
import { Hono } from 'hono';
import { z } from 'zod';

import { etag, type ExpectedVersion, matches, parseETags } from '../../etag.mts';
import { requireGroup } from '../../security/auth.mts';
import { NotFoundError } from '../service/errors.mts';
import { findAll, findById } from '../service/recipe-service.mts';
import { create, replace, update } from '../service/recipe-write-service.mts';
import {
  RecipeCreateSchema,
  RecipeReplaceSchema,
  RecipeUpdateSchema,
} from '../validation/recipe-validation.mts';
import { BadRequestError, PreconditionRequiredError } from './errors.mts';

export const router = new Hono();

/** The recipe id from the path; anything that cannot be an id is answered with 404. */
const recipeId = (c: Context): string => {
  const result = z.guid().safeParse(c.req.param('id'));
  if (!result.success) {
    throw new NotFoundError(`There is no recipe with id ${c.req.param('id')}.`);
  }
  return result.data;
};

/** The request body as JSON; it is validated with Zod afterwards. */
const readJson = async (c: Context): Promise<unknown> => {
  try {
    return await c.req.json();
  } catch {
    throw new BadRequestError('The request body is not valid JSON.');
  }
};

/** The versions named in `If-Match`, which every write requires. */
const ifMatch = (c: Context): ExpectedVersion => {
  const header = c.req.header('If-Match');
  if (header === undefined) {
    throw new PreconditionRequiredError(
      'The header "If-Match" with the recipe\'s current ETag is required.',
    );
  }
  return parseETags(header, false);
};

/** The URL of a recipe, for the `Location` header. */
const locationOf = (c: Context, id: string): string => {
  const url = new URL(c.req.url);
  return `${url.origin}${url.pathname.replace(/\/$/u, '')}/${id}`;
};

// =============================================================================
// R e a d
// =============================================================================

/** All recipes, without details, ingredients and steps; `?search=` filters by name. */
router.get('/', requireGroup('user'), async (c) => {
  const recipes = await findAll({ search: c.req.query('search') });
  return c.json(recipes);
});

/** One recipe; `304 Not Modified` if `If-None-Match` names its current version. */
router.get('/:id', requireGroup('user'), async (c) => {
  const recipe = await findById(recipeId(c));
  c.header('ETag', etag(recipe.version));
  const ifNoneMatch = c.req.header('If-None-Match');
  if (ifNoneMatch !== undefined && matches(parseETags(ifNoneMatch, true), recipe.version)) {
    return c.body(null, 304);
  }
  return c.json(recipe);
});

// =============================================================================
// W r i t e
// =============================================================================

/** Creates a recipe: `201 Created` with an empty body and the new recipe's URL in `Location`. */
router.post('/', requireGroup('moderator'), async (c) => {
  const newRecipe = RecipeCreateSchema.parse(await readJson(c));
  const id = await create(newRecipe);
  c.header('Location', locationOf(c, id));
  return c.body(null, 201);
});

/** Replaces the whole recipe; requires `If-Match`. Answers with the recipe and its new `ETag`. */
router.put('/:id', requireGroup('moderator'), async (c) => {
  const id = recipeId(c);
  const expected = ifMatch(c);
  const recipe = await replace(id, RecipeReplaceSchema.parse(await readJson(c)), expected);
  c.header('ETag', etag(recipe.version));
  return c.json(recipe);
});

/** Renames the recipe; requires `If-Match`. Answers with the recipe and its new `ETag`. */
router.patch('/:id', requireGroup('moderator'), async (c) => {
  const id = recipeId(c);
  const expected = ifMatch(c);
  const recipe = await update(id, RecipeUpdateSchema.parse(await readJson(c)), expected);
  c.header('ETag', etag(recipe.version));
  return c.json(recipe);
});
