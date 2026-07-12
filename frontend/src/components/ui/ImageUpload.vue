<template>
  <div class="flex items-center gap-3">
    <div class="flex h-16 w-16 flex-shrink-0 items-center justify-center overflow-hidden rounded-lg border border-stone-200 bg-stone-100">
      <img v-if="modelValue" :src="modelValue" alt="" class="h-full w-full object-cover" />
      <PhotoIcon v-else class="h-6 w-6 text-stone-400" aria-hidden="true" />
    </div>
    <BaseButton type="button" variant="ghost" size="sm" :loading="uploading" @click="fileInput?.click()">
      {{ modelValue ? 'Заменить' : 'Загрузить' }}
    </BaseButton>
    <BaseButton v-if="modelValue" type="button" variant="ghost" size="sm" @click="$emit('update:modelValue', null)">
      Убрать
    </BaseButton>
    <input
      ref="fileInput"
      type="file"
      accept="image/jpeg,image/png,image/webp,image/gif"
      class="hidden"
      @change="onFileChange"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { PhotoIcon } from '@heroicons/vue/24/outline'
import BaseButton from './BaseButton.vue'
import { adminApi } from '../../api'
import { useToastStore } from '../../stores/toast'
import { extractErrorMessage } from '../../utils/errors'

defineProps({ modelValue: String })
const emit = defineEmits(['update:modelValue'])

const fileInput = ref(null)
const uploading = ref(false)
const toast = useToastStore()

async function onFileChange(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  uploading.value = true
  try {
    const { data } = await adminApi.uploadImage(file)
    emit('update:modelValue', data.url)
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить изображение'))
  } finally {
    uploading.value = false
  }
}
</script>
