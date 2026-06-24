<template>
  <div>
    <div v-if="loading" class="space-y-3">
      <Skeleton v-for="i in 3" :key="i" height="h-20" />
    </div>

    <EmptyState v-else-if="reviews.length === 0" :icon="StarIcon" title="Пока нет отзывов" />

    <div v-else class="space-y-3">
      <BaseCard v-for="r in reviews" :key="r.id">
        <div class="flex items-center gap-1">
          <StarIcon v-for="i in 5" :key="i" class="h-4 w-4" :class="i <= r.rating ? 'text-accent-400' : 'text-stone-200'" aria-hidden="true" />
        </div>
        <p v-if="r.comment" class="mt-2 text-sm text-ink-600">{{ r.comment }}</p>
        <p class="mt-2 text-xs text-ink-600/70">{{ formatDate(r.created_at) }}</p>
      </BaseCard>
    </div>

    <Pagination v-model:page="page" :total-pages="totalPages" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { StarIcon } from '@heroicons/vue/24/solid'
import { reviewsApi } from '../../api'
import { useMasterProfileStore } from '../../stores/masterProfile'
import { useToastStore } from '../../stores/toast'
import { extractErrorMessage } from '../../utils/errors'
import { useDebouncedWatch } from '../../composables/useDebouncedWatch'
import BaseCard from '../../components/ui/BaseCard.vue'
import Skeleton from '../../components/ui/Skeleton.vue'
import EmptyState from '../../components/ui/EmptyState.vue'
import Pagination from '../../components/ui/Pagination.vue'

const profileStore = useMasterProfileStore()
const toast = useToastStore()

const reviews = ref([])
const loading = ref(true)
const page = ref(1)
const totalPages = ref(1)

async function load() {
  loading.value = true
  try {
    const { data } = await reviewsApi.listForMaster(profileStore.profile.id, { page: page.value, page_size: 10 })
    reviews.value = data.items
    totalPages.value = data.total_pages
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить отзывы'))
  } finally {
    loading.value = false
  }
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ru', { day: 'numeric', month: 'long', year: 'numeric' })
}

useDebouncedWatch(page, load, 0)
onMounted(load)
</script>
