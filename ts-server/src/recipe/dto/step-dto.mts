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

  constructor(drizzleObj: StepSelect) {
    const { id, version, position, preparationMethod } = drizzleObj;
    this.id = id;
    this.version = version;
    this.position = position;
    this.preparation_method = preparationMethod;
  }
}
