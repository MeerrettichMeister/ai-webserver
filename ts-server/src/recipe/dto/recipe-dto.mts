import type { recipe } from '../db/schema.mts';
import { IngredientDTO, type IngredientSelect } from './ingredient-dto.mts';
import { RecipeDetailsDTO, type RecipeDetailsSelect } from './recipe-details-dto.mts';
import { StepDTO, type StepSelect } from './step-dto.mts';

export type RecipeSelect = typeof recipe.$inferSelect;

/**
 * A recipe (response body). In lists only `id`, `version` and `name` are set; a single recipe
 * also has its details, ingredients and steps.
 */
export class RecipeDTO {
  /** UUID. */
  id: string;
  /** The row's version, also sent as its ETag. Send as `If-Match: "<version>"` when updating. */
  version: number;
  name: string;
  /** When the recipe was created (ISO 8601 in JSON). */
  created_at: Date;
  /** When the recipe or anything in it (details, ingredients, steps) last changed. */
  updated_at: Date;
  details?: RecipeDetailsDTO;
  ingredients?: IngredientDTO[];
  /** In the order they are performed: pass the rows sorted by `position`. */
  steps?: StepDTO[];

  constructor(
    drizzleRecipe: RecipeSelect,
    drizzleDetails?: RecipeDetailsSelect,
    drizzleIngredients?: IngredientSelect[],
    drizzleSteps?: StepSelect[],
  ) {
    const { id, version, name, createdAt, updatedAt } = drizzleRecipe;
    this.id = id;
    this.version = version;
    this.name = name;
    this.created_at = createdAt;
    this.updated_at = updatedAt;
    if (drizzleDetails !== undefined) {
      this.details = new RecipeDetailsDTO(drizzleDetails);
    }
    if (drizzleIngredients !== undefined) {
      this.ingredients = drizzleIngredients.map((ing) => new IngredientDTO(ing));
    }
    if (drizzleSteps !== undefined) {
      this.steps = drizzleSteps.map((s) => new StepDTO(s));
    }
  }
}
