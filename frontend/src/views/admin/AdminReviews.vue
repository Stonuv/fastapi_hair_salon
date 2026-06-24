<template>
  <div>
    <div class="mb-4 grid gap-3 sm:grid-cols-3">
      <BaseSelect v-model="isPublished" placeholder="Любой статус публикации">
        <option value="true">Опубликованы</option>
        <option value="false">Скрыты</option>
      </BaseSelect>
      <BaseSelect v-model="minRating" placeholder="Любая оценка">
        <option v-for="i in 5" :key="i" :value="i">{{ i }}+ звёзд</option>
      </BaseSelect>
    </div>

    <div v-if="loading" class="space-y-3">
      <Skeleton v-for="i in 4" :key="i" height="h-24" />
    </div>

    <EmptyState v-else-if="reviews.length === 0" :icon="StarIcon" title="Отзывы не найдены" />

    <div v-else class="space-y-3">
      <BaseCard v-for="r in reviews" :key="r.id">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div class="flex items-center gap-1">
              <StarIcon v-for="i in 5" :key="i" class="h-4 w-4" :class="i <= r.rating ? 'text-accent-400' : 'text-stone-200'" aria-hidden="true" />
            </div>
            <p class="mt-1 text-sm text-ink-900">{{ r.client_name }} → {{ r.master_name }} · {{ r.service_name }}</p>
            <p v-if="r.comment" class="mt-1 text-sm text-ink-600">{{ r.comment }}</p>
            <p class="mt-1 text-xs text-ink-600/70">{{ formatDate(r.created_at) }}</p>
          </div>
          <BaseButton variant="ghost" size="sm" :loading="moderating === r.id" @click="toggle(r)">
            {{ r.is_published ? 'Скрыть' : 'Опубликовать' }}
          </BaseButton>
        </div>
      </BaseCard>
    </div>

    <Pagination v-model:page="page" :total-pages="totalPages" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { StarIcon } from '@heroicons/vue/24/solid'
import { reviewsApi } from '../../api'
import { useToastStore } from '../../stores/toast'
import { extractErrorMessage } from '../../utils/errors'
import { useDebouncedWatch } from '../../composables/useDebouncedWatch'
import BaseCard from '../../components/ui/BaseCard.vue'
import BaseSelect from '../../components/ui/BaseSelect.vue'
import BaseButton from '../../components/ui/BaseButton.vue'
import Skeleton from '../../components/ui/Skeleton.vue'
import EmptyState from '../../components/ui/EmptyState.vue'
import Pagination from '../../components/ui/Pagination.vue'

const toast = useToastStore()

const reviews = ref([])
const loading = ref(true)
const page = ref(1)
const totalPages = ref(1)
const isPublished = ref('')
const minRating = ref('')
const moderating = ref(null)

async function load() {
  loading.value = true
  try {
    const { data } = await reviewsApi.listAll({
      page: page.value, page_size: 10,
      is_published: isPublished.value === '' ? undefined : isPublished.value === 'true',
      min_rating: minRating.value || undefined,
    })
    reviews.value = data.items
    totalPages.value = data.total_pages
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить отзывы'))
  } finally {
    loading.value = false
  }
}

async function toggle(review) {
  moderating.value = review.id
  try {
    await reviewsApi.moderate(review.id, !review.is_published)
    review.is_published = !review.is_published
    toast.success(review.is_published ? 'Отзыв опубликован' : 'Отзыв скрыт')
  } catch (err) {
    toast.error(extractErrorMessage(err))
  } finally {
    moderating.value = null
  }
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ru', { day: 'numeric', month: 'long', year: 'numeric' })
}

useDebouncedWatch([isPublished, minRating], () => { page.value = 1; load() }, 0)
useDebouncedWatch(page, load, 0)
onMounted(load)
</script>
