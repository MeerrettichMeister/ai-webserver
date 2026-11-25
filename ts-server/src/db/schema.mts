import { randomUUID } from 'node:crypto';

import {
  foreignKey,
  index,
  integer,
  numeric,
  pgSchema,
  primaryKey,
  unique,
  uuid,
  varchar,
} from 'drizzle-orm/pg-core';

export const recipeSchema = pgSchema('recipes');

export const difficultyEnum = recipeSchema.enum('difficulty', ['easy', 'medium', 'hard']);

export const recipe = recipeSchema.table(
  'recipe',
  {
    id: uuid('id')
      .notNull()
      .$defaultFn(() => randomUUID()),
    name: varchar('name', { length: 255 }).notNull(),
    // Covers the whole aggregate: bump it on every write to the recipe or its children.
    version: integer('version')
      .notNull()
      .$default(() => 1),
  },
  (t) => [
    primaryKey({ name: 'pk_recipe', columns: [t.id] }),
    // Backs paginated listing ordered by (name, id).
    index('ix_recipe_name_id').on(t.name, t.id),
  ],
);

export const ingredient = recipeSchema.table(
  'ingredient',
  {
    id: uuid('id')
      .notNull()
      .$defaultFn(() => randomUUID()),
    recipeId: uuid('recipe_id').notNull(),
    name: varchar('name', { length: 255 }).notNull(),
    // Returned as a string to keep the exact decimal value.
    amount: numeric('amount', { precision: 10, scale: 3 }).notNull(),
    unit: varchar('unit', { length: 50 }).notNull(),
    version: integer('version')
      .notNull()
      .$default(() => 1),
  },
  (t) => [
    primaryKey({ name: 'pk_ingredient', columns: [t.id] }),
    foreignKey({
      name: 'fk_ingredient_recipe_id_recipe',
      columns: [t.recipeId],
      foreignColumns: [recipe.id],
    }).onDelete('cascade'),
    unique('uq_ingredient_recipe_id_name').on(t.recipeId, t.name),
  ],
);

export const recipeDetails = recipeSchema.table(
  'recipe_details',
  {
    // 1:1 with recipe: primary key and foreign key at once.
    recipeId: uuid('recipe_id').notNull(),
    servings: integer('servings').notNull(),
    preparationTimeMinutes: integer('preparation_time_minutes').notNull(),
    difficulty: difficultyEnum('difficulty').notNull(),
  },
  (t) => [
    primaryKey({ name: 'pk_recipe_details', columns: [t.recipeId] }),
    foreignKey({
      name: 'fk_recipe_details_recipe_id_recipe',
      columns: [t.recipeId],
      foreignColumns: [recipe.id],
    }).onDelete('cascade'),
  ],
);

export const step = recipeSchema.table(
  'step',
  {
    id: uuid('id')
      .notNull()
      .$defaultFn(() => randomUUID()),
    recipeId: uuid('recipe_id').notNull(),
    position: integer('position').notNull(),
    preparationMethod: varchar('preparation_method', { length: 1000 }).notNull(),
    version: integer('version')
      .notNull()
      .$default(() => 1),
  },
  (t) => [
    primaryKey({ name: 'pk_step', columns: [t.id] }),
    foreignKey({
      name: 'fk_step_recipe_id_recipe',
      columns: [t.recipeId],
      foreignColumns: [recipe.id],
    }).onDelete('cascade'),
    unique('uq_step_recipe_id_position').on(t.recipeId, t.position),
  ],
);
