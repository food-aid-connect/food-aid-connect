import type { CreateClientConfig } from './generated/client.gen'

export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  // The generated operation paths already start with /api.
  baseUrl: '',
  credentials: 'include',
})
