/**
 * CI guard: fail if the committed generated client is out of date.
 *
 * Regenerates from the committed ./openapi.json into a throwaway directory and
 * compares it with src/api/generated. Drift means someone changed the backend
 * schema (or orval.config.ts) without re-running `npm run generate:api`.
 *
 * Generation happens into a temp dir on purpose: this script must not modify
 * tracked files, so a failing check leaves the working tree untouched.
 */

import { spawnSync } from 'node:child_process'
import {
  mkdirSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync,
} from 'node:fs'
import { dirname, join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const FRONTEND_ROOT = resolve(HERE, '..')
const GENERATED_DIR = resolve(FRONTEND_ROOT, 'src/api/generated')
const TMP_DIR = resolve(FRONTEND_ROOT, '.orval-check')
const TMP_CONFIG = resolve(FRONTEND_ROOT, 'orval.config.check.ts')

const walk = (dir, files = []) => {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry)
    if (statSync(full).isDirectory()) walk(full, files)
    else files.push(full)
  }
  return files
}

/**
 * Normalise content before comparing.
 *
 * Orval emits the mutator import as a path relative to the output directory, so
 * the throwaway output lands at `.orval-check/endpoints/<tag>/<tag>.ts` and
 * correctly imports `../../../src/api/mutator` while the committed tree imports
 * `../../../mutator`. That difference is an artefact of where the files were
 * written, not real drift, so it is normalised away.
 */
const normalise = (content) =>
  content.replace(/from '\.\.\/\.\.\/\.\.\/(?:src\/api\/)?mutator'/g, "from '<mutator>'")

const snapshot = (dir) => {
  const map = new Map()
  for (const file of walk(dir)) {
    map.set(
      relative(dir, file).replace(/\\/g, '/'),
      normalise(readFileSync(file, 'utf8'))
    )
  }
  return map
}

const cleanup = () => {
  rmSync(TMP_DIR, { force: true, recursive: true })
  rmSync(TMP_CONFIG, { force: true })
}

const main = () => {
  const committed = snapshot(GENERATED_DIR)

  // Reuse the real config, only redirecting the output paths.
  writeFileSync(
    TMP_CONFIG,
    `import config from './orval.config'\n` +
      `const spec = config.medicheck\n` +
      `spec.output.target = './.orval-check/endpoints'\n` +
      `spec.output.schemas = './.orval-check/model'\n` +
      `export default { medicheck: spec }\n`,
    'utf8'
  )

  mkdirSync(TMP_DIR, { recursive: true })

  // Args are fixed literals (no user input), so shell:false is safe and avoids
  // Node's DEP0190 warning about unescaped args under shell:true.
  const result = spawnSync('npx', ['orval', '--config', 'orval.config.check.ts'], {
    cwd: FRONTEND_ROOT,
    encoding: 'utf8',
    shell: process.platform === 'win32',
  })

  if (result.status !== 0) {
    console.error('Orval failed while verifying generated code:\n')
    console.error(result.stdout ?? '')
    console.error(result.stderr ?? '')
    cleanup()
    process.exit(1)
  }

  const fresh = snapshot(TMP_DIR)
  cleanup()

  const added = [...fresh.keys()].filter((k) => !committed.has(k))
  const removed = [...committed.keys()].filter((k) => !fresh.has(k))
  const changed = [...fresh.keys()].filter(
    (k) => committed.has(k) && committed.get(k) !== fresh.get(k)
  )

  if (!added.length && !removed.length && !changed.length) {
    console.log('Generated API client is up to date.')
    return
  }

  console.error('\nGenerated API client is OUT OF DATE with the committed openapi.json.\n')
  if (added.length) {
    console.error(`  added (${added.length}):\n${added.map((f) => `    + ${f}`).join('\n')}`)
  }
  if (removed.length) {
    console.error(`  removed (${removed.length}):\n${removed.map((f) => `    - ${f}`).join('\n')}`)
  }
  if (changed.length) {
    console.error(`  changed (${changed.length}):\n${changed.map((f) => `    ~ ${f}`).join('\n')}`)
  }
  console.error('\nBackend schema changed? Refresh it first: npm run generate:api:fetch')
  console.error('Then regenerate and commit:            npm run generate:api\n')

  process.exit(1)
}

main()