<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { postApiRegister, type UserRegisterSchema } from '@/api/generated'
import { authFormErrors } from '@/auth/form-errors'
import { session } from '@/auth/session'

const props = defineProps<{ register?: boolean }>()
const route = useRoute()
const router = useRouter()
const email = ref('')
const password = ref('')
const role = ref<UserRegisterSchema['role'] | ''>('')
const errors = ref<string[]>([])
const submitting = ref(false)

async function submit() {
  if (submitting.value) return

  errors.value = []
  submitting.value = true
  const credentials = { email: email.value, password: password.value }

  try {
    if (props.register) {
      if (!role.value) {
        errors.value = ['Choose an account role.']
        return
      }
      const result = await postApiRegister({ body: { ...credentials, role: role.value } })
      if (result.error || result.response?.status !== 201) {
        errors.value = authFormErrors(result.error, result.response?.status, 'Could not create your account. Please try again.')
        return
      }
      await router.replace({ name: 'login', query: { registered: '1' } })
    } else {
      const result = await session.login(credentials)
      if (result.error || !result.data) {
        errors.value = authFormErrors(result.error, result.response?.status, 'Could not log in. Please try again.')
        return
      }
      await router.replace({ name: 'home' })
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="auth">
    <h1>{{ register ? 'Create an account' : 'Log in' }}</h1>
    <p v-if="!register && route.query.registered === '1'" role="status">
      Account created. You can now log in.
    </p>
    <div v-if="errors.length" role="alert">
      <p v-for="(error, index) in errors" :key="index">{{ error }}</p>
    </div>
    <form @submit.prevent="submit">
      <fieldset :disabled="submitting">
        <label for="auth-email">Email</label>
        <input id="auth-email" v-model.trim="email" name="email" type="email" autocomplete="email" required />

        <label for="auth-password">Password</label>
        <input
          id="auth-password"
          v-model="password"
          name="password"
          type="password"
          :autocomplete="register ? 'new-password' : 'current-password'"
          :aria-describedby="register ? 'password-requirement' : undefined"
          required
        />
        <small v-if="register" id="password-requirement">Use at least 6 characters.</small>

        <template v-if="register">
          <label for="auth-role">Role</label>
          <select id="auth-role" v-model="role" name="role" required>
            <option value="" disabled>Choose a role</option>
            <option value="donor">Donor</option>
            <option value="charity">Charity</option>
          </select>
        </template>

        <button type="submit">
          {{ submitting ? 'Submitting…' : register ? 'Create account' : 'Log in' }}
        </button>
      </fieldset>
    </form>
    <RouterLink v-if="register" :to="{ name: 'login' }">Log in</RouterLink>
    <RouterLink v-else :to="{ name: 'register' }">Create an account</RouterLink>
  </main>
</template>

<style scoped>
.auth {
  min-width: 0;
  max-width: 28rem;
  padding-block: 1.5rem;
}

form {
  margin-block: 1rem;
}

fieldset {
  display: grid;
  gap: 0.5rem;
  padding: 0;
  border: 0;
}

input,
select,
button {
  padding: 0.5rem;
  font: inherit;
}

button {
  justify-self: start;
  margin-top: 0.5rem;
}
</style>
