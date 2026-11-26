import type { ingredient } from '../db/schema.mts';

export type IngredientSelect = typeof ingredient.$inferSelect;

/** An ingredient with its id and version (response body). */
export class IngredientDTO {
  /** UUID. */
  id: string;
  /** The row's version, also sent as its ETag. Send as `If-Match: "<version>"` when updating. */
  version: number;
  /** Name of the ingredient. */
  ingredient: string;
  /** Stored exactly (`numeric(10, 3)`) but sent as a plain JSON number: `400`, not `"400.000"`. */
  amount: number;
  unit: string;
  /** When the ingredient was added (ISO 8601 in JSON). */
  created_at: Date;
  /** When the ingredient last changed. */
  updated_at: Date;

  constructor(drizzleObj: IngredientSelect) {
    const { id, version, name, amount, unit, createdAt, updatedAt } = drizzleObj;
    this.id = id;
    this.version = version;
    this.ingredient = name;
    this.amount = Number.parseFloat(amount);
    this.unit = unit;
    this.created_at = createdAt;
    this.updated_at = updatedAt;
  }
}
