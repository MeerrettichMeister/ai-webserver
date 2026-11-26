import { z } from 'zod';

/**
 * The timestamps of a `GET /recipes/:id` response, which a `PUT` body may contain so that the
 * response can be sent back changed. They are only checked to be timestamps and then ignored: the
 * database sets them.
 */
export const ReadOnlyTimestamps = {
  created_at: z.iso.datetime({ offset: true }).optional(),
  updated_at: z.iso.datetime({ offset: true }).optional(),
};
