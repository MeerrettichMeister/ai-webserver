import type { step } from '../db/schema.mts';

export type StepSelect = typeof step.$inferSelect;

/** A step with its id, position and version (response body). */
export class StepDTO {
  /** UUID. */
  id: string;
  /** The row's version, also sent as its ETag. Send as `If-Match: "<version>"` when updating. */
  version: number;
  position: number;
  /** What to do in this step. */
  preparation_method: string;
  /** When the step was added (ISO 8601 in JSON). */
  created_at: Date;
  /** When the step last changed, including moving to another position. */
  updated_at: Date;

  constructor(drizzleObj: StepSelect) {
    const { id, version, position, preparationMethod, createdAt, updatedAt } = drizzleObj;
    this.id = id;
    this.version = version;
    this.position = position;
    this.preparation_method = preparationMethod;
    this.created_at = createdAt;
    this.updated_at = updatedAt;
  }
}
