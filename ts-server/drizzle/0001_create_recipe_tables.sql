CREATE SCHEMA "recipes";
--> statement-breakpoint
CREATE TYPE "recipes"."difficulty" AS ENUM('easy', 'medium', 'hard');--> statement-breakpoint
CREATE TABLE "recipes"."ingredient" (
	"id" uuid NOT NULL,
	"recipe_id" uuid NOT NULL,
	"name" varchar(255) NOT NULL,
	"amount" numeric(10, 3) NOT NULL,
	"unit" varchar(50) NOT NULL,
	"version" integer NOT NULL,
	CONSTRAINT "pk_ingredient" PRIMARY KEY("id"),
	CONSTRAINT "uq_ingredient_recipe_id_name" UNIQUE("recipe_id","name")
);
--> statement-breakpoint
CREATE TABLE "recipes"."recipe" (
	"id" uuid NOT NULL,
	"name" varchar(255) NOT NULL,
	"version" integer NOT NULL,
	CONSTRAINT "pk_recipe" PRIMARY KEY("id")
);
--> statement-breakpoint
CREATE TABLE "recipes"."recipe_details" (
	"recipe_id" uuid NOT NULL,
	"servings" integer NOT NULL,
	"preparation_time_minutes" integer NOT NULL,
	"difficulty" "recipes"."difficulty" NOT NULL,
	CONSTRAINT "pk_recipe_details" PRIMARY KEY("recipe_id")
);
--> statement-breakpoint
CREATE TABLE "recipes"."step" (
	"id" uuid NOT NULL,
	"recipe_id" uuid NOT NULL,
	"position" integer NOT NULL,
	"preparation_method" varchar(1000) NOT NULL,
	"version" integer NOT NULL,
	CONSTRAINT "pk_step" PRIMARY KEY("id"),
	CONSTRAINT "uq_step_recipe_id_position" UNIQUE("recipe_id","position")
);
--> statement-breakpoint
ALTER TABLE "recipes"."ingredient" ADD CONSTRAINT "fk_ingredient_recipe_id_recipe" FOREIGN KEY ("recipe_id") REFERENCES "recipes"."recipe"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "recipes"."recipe_details" ADD CONSTRAINT "fk_recipe_details_recipe_id_recipe" FOREIGN KEY ("recipe_id") REFERENCES "recipes"."recipe"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "recipes"."step" ADD CONSTRAINT "fk_step_recipe_id_recipe" FOREIGN KEY ("recipe_id") REFERENCES "recipes"."recipe"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "ix_recipe_name_id" ON "recipes"."recipe" USING btree ("name","id");