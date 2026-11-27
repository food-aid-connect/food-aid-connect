<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { session } from '@/auth/session'
import HelloWorld from './components/HelloWorld.vue'

const { user, restoreFailed } = session
const router = useRouter()
const loggingOut = ref(false)
const logoutFailed = ref(false)

async function logout() {
  if (loggingOut.value) return
  loggingOut.value = true
  logoutFailed.value = false

  try {
    if (await session.logout()) {
      await router.replace({ name: 'login' })
    } else {
      logoutFailed.value = true
    }
  } finally {
    loggingOut.value = false
  }
}
</script>

<template>
  <header>
    <img alt="Vue logo" class="logo" src="@/assets/logo.svg" width="125" height="125" />

    <div class="wrapper">
      <HelloWorld msg="You did it!" />

      <nav aria-label="Main navigation">
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/about">About</RouterLink>
        <RouterLink v-if="user?.role === 'donor'" :to="{ name: 'my-batches' }">
          My donated batches
        </RouterLink>
        <template v-if="user?.role === 'charity'">
          <RouterLink :to="{ name: 'available-batches' }">Available batches</RouterLink>
          <RouterLink :to="{ name: 'my-reservations' }">My reservations</RouterLink>
        </template>
        <button v-if="user" type="button" :disabled="loggingOut" @click="logout">
          {{ loggingOut ? 'Logging out…' : 'Log out' }}
        </button>
        <template v-else>
          <RouterLink :to="{ name: 'login' }">Log in</RouterLink>
          <RouterLink :to="{ name: 'register' }">Register</RouterLink>
        </template>
      </nav>
      <p v-if="user">{{ user.email }} ({{ user.role }})</p>
      <p v-if="restoreFailed" role="alert">Could not check your session. Refresh the page to try again.</p>
      <p v-if="logoutFailed" role="alert">Could not log out. Please try again.</p>
    </div>
  </header>

  <RouterView v-slot="{ Component, route }">
    <component :is="Component" :key="route.path" />
  </RouterView>
</template>

<style scoped>
header {
  line-height: 1.5;
  max-height: 100vh;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}

nav {
  width: 100%;
  font-size: 12px;
  text-align: center;
  margin-top: 2rem;
}

nav a.router-link-exact-active {
  color: var(--color-text);
}

nav a.router-link-exact-active:hover {
  background-color: transparent;
}

nav a {
  display: inline-block;
  padding: 0 1rem;
  border-left: 1px solid var(--color-border);
}

nav a:first-of-type {
  border: 0;
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }

  nav {
    text-align: left;
    margin-left: -1rem;
    font-size: 1rem;

    padding: 1rem 0;
    margin-top: 1rem;
  }
}
</style>
