import { defineConfig } from '@hey-api/openapi-ts'

export default defineConfig({
  input: 'http://127.0.0.1:5000/openapi.json',
  output: 'src/api/generated',
  parser: {
    filters: {
      operations: { exclude: ['/^[A-Z]+ (?!\/api\/)/'] },
    },
  },
  plugins: [
    '@hey-api/typescript',
    '@hey-api/sdk',
    {
      name: '@hey-api/client-fetch',
      baseUrl: false,
      runtimeConfigPath: './src/api/client-config.ts',
    },
  ],
})
