import { z } from 'zod';

/**
 * The timestamps of a `GET /recipes/:id` response, which a `PUT` body may contain so that the
 * response can be sent back changed. Their values are ignored (the database sets them), so any
 * value is accepted: clients may re-serialize dates in another format.
 */
export const ReadOnlyTimestamps = {
  created_at: z.unknown().optional(),
  updated_at: z.unknown().optional(),
};
