-- Seed recipe: recipes/Sachertorte.json, created with the fixed id 5174cc9d-71cb-4d34-a3e9-ce8649192e20.
-- Ingredient and step ids are generated; versions start at 1 like for recipes created via the API.
INSERT INTO "recipes"."recipe" ("id", "name", "version")
VALUES ('5174cc9d-71cb-4d34-a3e9-ce8649192e20', 'Sachertorte', 1);
--> statement-breakpoint
INSERT INTO "recipes"."recipe_details" ("recipe_id", "servings", "preparation_time_minutes", "difficulty")
VALUES ('5174cc9d-71cb-4d34-a3e9-ce8649192e20', 12, 150, 'hard');
--> statement-breakpoint
INSERT INTO "recipes"."ingredient" ("id", "recipe_id", "name", "amount", "unit", "version")
VALUES
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 'Butter, zimmerwarm', 130, 'g', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 'Puderzucker', 110, 'g', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 'Vanillezucker', 1, 'Päckchen', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 'Eier, getrennt', 6, 'Stück', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 'Zartbitterkuvertüre (für den Teig)', 130, 'g', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 'Salz', 1, 'Prise', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 'Kristallzucker', 110, 'g', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 'Mehl', 130, 'g', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 'Marillenmarmelade (Aprikosenkonfitüre)', 200, 'g', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 'Zucker (für die Glasur)', 200, 'g', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 'Wasser (für die Glasur)', 125, 'ml', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 'Zartbitterkuvertüre (für die Glasur)', 150, 'g', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 'Schlagsahne (zum Servieren)', 200, 'ml', 1);
--> statement-breakpoint
INSERT INTO "recipes"."step" ("id", "recipe_id", "position", "preparation_method", "version")
VALUES
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 1, 'Den Backofen auf 170 °C Ober-/Unterhitze vorheizen. Den Boden einer Springform (24 cm) mit Backpapier auslegen, den Rand leicht einfetten und mit Mehl bestäuben.', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 2, 'Die Kuvertüre für den Teig grob hacken und über einem warmen Wasserbad schmelzen. Anschließend etwas abkühlen lassen, sie sollte nur noch lauwarm sein.', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 3, 'Butter mit Puderzucker und Vanillezucker cremig-schaumig rühren. Die Eigelbe einzeln unterrühren, dann die lauwarme Schokolade einrühren.', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 4, 'Die Eiweiße mit einer Prise Salz anschlagen, dabei nach und nach den Kristallzucker einrieseln lassen und zu einem festen, glänzenden Schnee schlagen.', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 5, 'Den Eischnee abwechselnd mit dem gesiebten Mehl vorsichtig unter die Schokoladenmasse heben. Nicht rühren, damit die Masse luftig bleibt.', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 6, 'Den Teig in die Form füllen, glatt streichen und im Ofen ca. 55–60 Minuten backen (Stäbchenprobe). Die Torte in der Form kurz abkühlen lassen, dann auf ein Gitter stürzen und am besten über Nacht vollständig auskühlen lassen.', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 7, 'Die Torte waagerecht halbieren. Die Marmelade erwärmen, glatt rühren und den unteren Boden damit bestreichen. Den oberen Boden auflegen und die gesamte Torte (Oberfläche und Rand) dünn mit der restlichen Marmelade einstreichen. Kurz antrocknen lassen.', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 8, 'Für die Glasur Zucker und Wasser aufkochen und ca. 5–6 Minuten sprudelnd kochen lassen. Etwas abkühlen lassen, dann die gehackte Kuvertüre darin schmelzen und so lange rühren, bis die Glasur dickflüssig wird und gleichmäßig glänzt.', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 9, 'Die Glasur in einem Zug über die Torte gießen und mit einer Palette rasch glatt streichen, auch am Rand. Die Glasur fest werden lassen, nicht im Kühlschrank, damit sie glänzend bleibt.', 1),
  (gen_random_uuid(), '5174cc9d-71cb-4d34-a3e9-ce8649192e20', 10, 'Die Sachertorte in Stücke schneiden und mit ungesüßter Schlagsahne servieren.', 1);
