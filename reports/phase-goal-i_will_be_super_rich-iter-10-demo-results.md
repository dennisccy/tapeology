# Demo Results — goal-i_will_be_super_rich-iter-10

**Demo Verdict:** SKIPPED
**Reason:** Frontend at http://localhost:3650 did not respond after 90s of retries. No browser walkthrough was performed.

Likely cause: a stale/corrupt .next build (a 'next build' likely ran against the live 'next dev' .next). The harness auto-clears .next and retries; if it persists, isolate builds with NEXT_DIST_DIR (e.g. NEXT_DIST_DIR=.next-qa for build/QA commands).

Frontend log tail (/tmp/fanout-frontend-8650.log):
```
Require stack:
- /home/dennisccy/Git/tapeology/apps/frontend/.next/server/webpack-runtime.js
- /home/dennisccy/Git/tapeology/apps/frontend/.next/server/pages/_document.js
- /home/dennisccy/Git/tapeology/apps/frontend/node_modules/next/dist/server/require.js
- /home/dennisccy/Git/tapeology/apps/frontend/node_modules/next/dist/server/load-components.js
- /home/dennisccy/Git/tapeology/apps/frontend/node_modules/next/dist/build/utils.js
- /home/dennisccy/Git/tapeology/apps/frontend/node_modules/next/dist/build/swc/options.js
- /home/dennisccy/Git/tapeology/apps/frontend/node_modules/next/dist/build/swc/index.js
- /home/dennisccy/Git/tapeology/apps/frontend/node_modules/next/dist/build/analysis/parse-module.js
- /home/dennisccy/Git/tapeology/apps/frontend/node_modules/next/dist/build/analysis/get-page-static-info.js
- /home/dennisccy/Git/tapeology/apps/frontend/node_modules/next/dist/server/lib/router-utils/setup-dev-bundler.js
- /home/dennisccy/Git/tapeology/apps/frontend/node_modules/next/dist/server/lib/router-server.js
- /home/dennisccy/Git/tapeology/apps/frontend/node_modules/next/dist/server/lib/start-server.js
    at <unknown> (.next/server/app/page.js:2:37335)
    at Object.<anonymous> (.next/server/app/page.js:2:37379) {
  code: 'MODULE_NOT_FOUND',
  requireStack: [Array],
  page: '/'
}
 GET / 500 in 240ms
```
