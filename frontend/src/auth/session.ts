import { readonly, ref } from 'vue'
import { getApiMe, postApiLogin, postApiLogout, type UserLoginSchema, type UserOutSchema } from '@/api/generated'

const user = ref<UserOutSchema | null>(null)
const restoreFailed = ref(false)
let restoration: Promise<void> | undefined

async function restoreSession() {
  const result = await getApiMe()
  user.value = result.error ? null : (result.data ?? null)
  restoreFailed.value = !user.value && result.response?.status !== 401
}

function initializeSession() {
  restoration ??= restoreSession()
  return restoration
}

async function login(body: UserLoginSchema) {
  const result = await postApiLogin({ body })
  if (!result.error && result.data) {
    user.value = result.data
    restoreFailed.value = false
  }
  return result
}

async function logout() {
  const result = await postApiLogout()
  if (result.error || !result.response?.ok) return false
  user.value = null
  return true
}

export const session = {
  user: readonly(user),
  restoreFailed: readonly(restoreFailed),
  initializeSession,
  login,
  logout,
}
