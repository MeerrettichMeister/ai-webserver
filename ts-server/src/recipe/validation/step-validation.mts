import { z } from 'zod';

/** What to do in a step. Surrounding whitespace is stripped; then 1 to 1000 characters. */
export const PreparationMethodSchema = z.string().trim().min(1).max(1000);

const StepSchema = z.strictObject({
  /** UUID of an existing step. */
  id: z.uuid(),
  preparation_method: PreparationMethodSchema,
});

/** A step of a replaced recipe: updated if it has an `id`, otherwise added. */
export const StepReplaceSchema = StepSchema.partial({ id: true });

/** Request body to change one step. */
export const StepUpdateSchema = z.compile(StepSchema.omit({ id: true })).readonly();

export type StepReplaceType = z.infer<typeof StepReplaceSchema>;
export type StepUpdateType = z.infer<typeof StepUpdateSchema>;
