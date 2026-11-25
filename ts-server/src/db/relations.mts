import { relations } from 'drizzle-orm/relations';

import { ingredient, recipe, recipeDetails, step } from './schema.mts';

export const recipeRelations = relations(recipe, ({ one, many }) => ({
  details: one(recipeDetails),
  ingredients: many(ingredient),
  steps: many(step),
}));

export const recipeDetailsRelations = relations(recipeDetails, ({ one }) => ({
  recipe: one(recipe, { fields: [recipeDetails.recipeId], references: [recipe.id] }),
}));

export const ingredientRelations = relations(ingredient, ({ one }) => ({
  recipe: one(recipe, { fields: [ingredient.recipeId], references: [recipe.id] }),
}));

export const stepRelations = relations(step, ({ one }) => ({
  recipe: one(recipe, { fields: [step.recipeId], references: [recipe.id] }),
}));
