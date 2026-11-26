import type { recipeDetails } from '../db/schema.mts';

export type RecipeDetailsSelect = typeof recipeDetails.$inferSelect;

/** How hard a recipe is to make. */
export type Difficulty = RecipeDetailsSelect['difficulty'];

/** Servings, total time and difficulty of a recipe (response body). */
export class RecipeDetailsDTO {
  /** Number of portions the recipe makes. */
  servings: number;
  /** Total time from start to serving, in minutes. */
  preparation_time_minutes: number;
  difficulty: Difficulty;
  /** When the details were created (ISO 8601 in JSON). */
  created_at: Date;
  /** When the details last changed (a `PUT` of the recipe always writes them). */
  updated_at: Date;

  constructor(drizzleObj: RecipeDetailsSelect) {
    const { servings, preparationTimeMinutes, difficulty, createdAt, updatedAt } = drizzleObj;
    this.servings = servings;
    this.preparation_time_minutes = preparationTimeMinutes;
    this.difficulty = difficulty;
    this.created_at = createdAt;
    this.updated_at = updatedAt;
  }
}
