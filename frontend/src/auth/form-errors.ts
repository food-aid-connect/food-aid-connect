const fieldLabels = {
  email: 'Email',
  password: 'Password',
  role: 'Role',
}

export function authFormErrors(error: unknown, status: number | undefined, fallback: string) {
  if (status === undefined) return ['Could not connect to the server. Please try again.']
  if (status === 401) return ['Invalid email or password.']
  if (status === 409) return ['This email is already registered.']
  if (status !== 422) return [fallback]

  // APIFlask groups validation messages by request location and field.
  const fields = (error as { detail?: { json?: Record<string, unknown> } } | undefined)?.detail?.json
  const messages = Object.entries(fieldLabels).flatMap(([field, label]) => {
    const errors = fields?.[field]
    return Array.isArray(errors)
      ? errors.filter((message) => typeof message === 'string').map((message) => `${label}: ${message}`)
      : []
  })
  return messages.length ? messages : ['Check the information you entered and try again.']
}
