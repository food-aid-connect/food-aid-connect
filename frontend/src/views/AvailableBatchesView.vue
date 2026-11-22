<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getApiBatches, type GetApiBatchesResponse } from '@/api/generated'

const batches = ref<GetApiBatchesResponse>([])
const loading = ref(true)
const loadFailed = ref(false)

async function loadBatches() {
  loading.value = true
  loadFailed.value = false

  try {
    const { data } = await getApiBatches({
      query: { status: 'available' },
      throwOnError: true,
    })
    batches.value = data
  } catch {
    loadFailed.value = true
  } finally {
    loading.value = false
  }
}

onMounted(loadBatches)
</script>

<template>
  <main class="available-batches">
    <h1>Available batches</h1>

    <p v-if="loading" role="status">Loading available batches…</p>
    <div v-else-if="loadFailed">
      <p role="alert">Could not load available batches.</p>
      <button type="button" @click="loadBatches">Try again</button>
    </div>
    <p v-else-if="batches.length === 0" role="status">No batches are available right now.</p>
    <ul v-else class="batch-list">
      <li v-for="(batch, index) in batches" :key="batch.id ?? `row-${index}`" class="batch">
        <h2>{{ batch.title || 'Untitled batch' }}</h2>
        <p v-if="batch.category">{{ batch.category }}</p>
        <dl>
          <div v-if="batch.quantity || batch.quantity_kg != null">
            <dt>Quantity</dt>
            <dd>{{ batch.quantity || `${batch.quantity_kg} kg` }}</dd>
          </div>
          <div v-if="batch.pickup_date || batch.pickup_address || (batch.pickup_start && batch.pickup_end)">
            <dt>Pickup</dt>
            <dd v-if="batch.pickup_date">
              <time :datetime="batch.pickup_date">{{ batch.pickup_date }}</time>
            </dd>
            <dd v-if="batch.pickup_start && batch.pickup_end">
              {{ batch.pickup_start.slice(0, 5) }}–{{ batch.pickup_end.slice(0, 5) }}
            </dd>
            <dd v-if="batch.pickup_address">{{ batch.pickup_address }}</dd>
          </div>
          <div v-if="batch.use_by_date">
            <dt>Use by</dt>
            <dd><time :datetime="batch.use_by_date">{{ batch.use_by_date }}</time></dd>
          </div>
        </dl>
      </li>
    </ul>
  </main>
</template>

<style scoped>
.available-batches {
  min-width: 0;
  padding-block: 1.5rem;
}

h1 {
  margin-bottom: 1rem;
}

.batch-list {
  display: grid;
  gap: 0.75rem;
  padding: 0;
  list-style: none;
}

.batch {
  padding: 1rem;
  overflow-wrap: anywhere;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
}

dl {
  display: grid;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

dt {
  font-weight: 600;
}

dd {
  margin: 0;
}

button {
  margin-top: 0.5rem;
  padding: 0.4rem 0.75rem;
  color: var(--color-text);
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  cursor: pointer;
}
</style>
