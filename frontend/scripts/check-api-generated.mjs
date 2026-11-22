import { execFileSync } from 'node:child_process'

const changes = execFileSync(
  'git',
  ['status', '--porcelain', '--untracked-files=all', '--', 'src/api/generated'],
  { encoding: 'utf8' },
)

if (changes) {
  console.error('The generated API client differs from the checked-in version:')
  console.error(changes.trimEnd())
  process.exitCode = 1
}
