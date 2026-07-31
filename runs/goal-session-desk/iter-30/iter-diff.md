# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/frontend/next-env.d.ts b/apps/frontend/next-env.d.ts
index 830fb59..e61acc9 100644
--- a/apps/frontend/next-env.d.ts
+++ b/apps/frontend/next-env.d.ts
@@ -1,6 +1,6 @@
 /// <reference types="next" />
 /// <reference types="next/image-types/global" />
-/// <reference path="./.next/types/routes.d.ts" />
+/// <reference path=".//home/dennis-chan/.cache/iad/shared/claude-1000/-home-dennis-chan-Git-tapeology/ed2eda9d-a300-40af-b7d9-38fc5240ab66/scratchpad/iter30-rig/frontend-dist/types/routes.d.ts" />
 
 // NOTE: This file should not be edited
 // see https://nextjs.org/docs/app/api-reference/config/typescript for more information.
diff --git a/apps/frontend/tsconfig.json b/apps/frontend/tsconfig.json
index 424abf1..663e7bc 100644
--- a/apps/frontend/tsconfig.json
+++ b/apps/frontend/tsconfig.json
@@ -32,9 +32,10 @@
     "**/*.ts",
     "**/*.tsx",
     ".next-eval-iter10/types/**/*.ts",
+    ".next-qa/types/**/*.ts",
     ".next/types/**/*.ts",
     "next-env.d.ts",
-    ".next-qa/types/**/*.ts"
+    "/home/dennis-chan/.cache/iad/shared/claude-1000/-home-dennis-chan-Git-tapeology/ed2eda9d-a300-40af-b7d9-38fc5240ab66/scratchpad/iter30-rig/frontend-dist/types/**/*.ts"
   ],
   "exclude": [
     "node_modules"
```
