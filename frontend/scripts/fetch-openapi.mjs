/**
 * Fetch a fresh OpenAPI schema from a running backend into ./openapi.json.
 *
 * Use this when you want the types to match the backend you are running right
 * now. For the normal workflow (and for CI) prefer the committed schema plus
 * `npm run generate:api`, which needs no backend at all.
 *
 * Usage:
 *   node scripts/fetch-openapi.mjs [url]
 *
 * Env:
 *   OPENAPI_URL   overrides the positional argument.
 *   OPENAPI_OUT   overrides the output path.
 *
 * The backend's root_path is /api/v1, so the schema lives at
 * http://localhost:8000/openapi.json (NOT under /api/v1).
 */

import { writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const FRONTEND_ROOT = resolve(HERE, '..')

const url =
  process.argv[2] ?? process.env.OPENAPI_URL ?? 'http://localhost:8000/openapi.json'
const outPath = resolve(
  FRONTEND_ROOT,
  process.env.OPENAPI_OUT ?? 'openapi.json'
)

const fetchSchema = async () => {
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error(
      `Failed to fetch ${url}: ${response.status} ${response.statusText}. ` +
        'Is the backend running? Try `uvicorn app.main:app --reload --port 8000` from backend/.'
    )
  }

  return response.json()
}

const main = async () => {
  const schema = await fetchSchema()

  // Recursively key-sorting mirrors `sort_keys=True` in
  // backend/scripts/export_openapi.py, so both ways of refreshing the schema
  // produce a byte-identical file and switching between them is a clean diff.
  const sortDeep = (value) => {
    if (Array.isArray(value)) return value.map(sortDeep)
    if (value !== null && typeof value === 'object') {
      return Object.fromEntries(
        Object.keys(value)
          .sort()
          .map((key) => [key, sortDeep(value[key])])
      )
    }
    return value
  }

  await writeFile(outPath, `${JSON.stringify(sortDeep(schema), null, 2)}\n`, 'utf8')

  console.log(`Fetched OpenAPI ${schema.openapi} from ${url}`)
  console.log(`  ${Object.keys(schema.paths ?? {}).length} paths -> ${outPath}`)
  console.log('  Next: npm run generate:api')
}

main().catch((error) => {
  console.error(`\n${error.message}\n`)
  process.exit(1)
})