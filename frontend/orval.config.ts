import { defineConfig } from 'orval'

/**
 * Orval - generate TypeScript types + TanStack Query v5 hooks from the FastAPI
 * OpenAPI schema.
 *
 * Design decisions
 * ----------------
 * - `input` points at the COMMITTED `./openapi.json`, not a live URL. Generation
 *   is therefore deterministic and works offline and in CI with no backend
 *   running. Refresh the schema with `npm run generate:api:fetch`.
 * - `client: 'react-query'` targets TanStack Query v5, already used app-wide.
 * - `httpClient: 'axios'` keeps the transport swappable.
 * - `override.mutator` routes every call through the EXISTING shared Axios
 *   instance (`src/api/mutator.ts` -> `src/lib/api.ts`) so the Firebase auth
 *   interceptor, the 401 refresh-and-retry interceptor and the base URL logic
 *   all stay in one place. Generated code never instantiates its own axios
 *   instance.
 * - `mode: 'split'` writes one file per backend tag. With 197 paths / 29 tags a
 *   single output file would be unusable.
 * - `baseUrl: ''` is deliberate: the shared Axios instance already resolves a
 *   base URL that ends in `/api/v1`, so generated paths such as `/auth/me`
 *   must NOT carry the prefix again (that was a real P0 bug in this codebase).
 *
 * Generated output lives in `src/api/generated/` and is never hand-edited.
 */
export default defineConfig({
  medicheck: {
    input: {
      target: './openapi.json',
    },
    output: {
      // 'tags-split' = one file per backend tag (with an index barrel).
      // 'split' = a single file for every operation, which produced one
      // ~880 KB unreadable file across 197 paths, hence the explicit choice.
      mode: 'tags-split',
      target: './src/api/generated/endpoints',
      schemas: './src/api/generated/model',
      client: 'react-query',
      httpClient: 'axios',
      // Tag-derived filenames: keep them predictable and kebab-cased.
      override: {
        mutator: {
          path: './src/api/mutator.ts',
          name: 'customInstance',
        },
        tag: {
          // Backend tags contain spaces, '&', '(' and ')' e.g.
          // "CMS Audit & Compliance" -> cms-audit-compliance.ts
          name: '{{name}}',
          // Drop the spec title from filenames so files are named after tags.
          useApiTag: true,
        },
      },
      baseUrl: '',
      // Emit an index.ts barrel per tag folder so consumers import from a
      // stable path instead of a specific generated filename.
      indexFiles: true,
      generateFullPath: false,
      // Stable, reviewable diffs.
      prettier: {
        semi: true,
        singleQuote: true,
        tabWidth: 2,
        printWidth: 100,
        trailingComma: 'es5',
        arrowParens: 'always',
      },
    },
  },
})