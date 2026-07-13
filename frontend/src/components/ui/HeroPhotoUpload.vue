<template>
  <div class="absolute inset-x-3 bottom-3 flex items-center gap-2">
    <button
      type="button"
      class="rounded bg-white/90 px-2.5 py-1.5 font-mono text-[11px] uppercase tracking-wide text-ink-900 shadow hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
      :disabled="uploading"
      @click="fileInput?.click()"
    >
      {{ uploading ? 'Загрузка…' : 'Выбрать' }}
    </button>
    <button
      v-if="modelValue"
      type="button"
      class="rounded bg-white/90 px-2.5 py-1.5 font-mono text-[11px] uppercase tracking-wide text-ink-900 shadow hover:bg-white"
      @click="$emit('update:modelValue', null)"
    >
      Убрать
    </button>
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
import { adminApi } from '../../api'
import { useToastStore } from '../../stores/toast'
import { extractErrorMessage } from '../../utils/errors'

// Оверлей поверх фото в hero-блоке /admin/settings-live — та же загрузка
// файла на сервер, что и в ImageUpload.vue (обычные «Настройки»), вместо
// текстового поля с URL, которое было тут раньше (ISSUES #29б делал это
// только для AdminSettings/AdminMasters, HomePreview остался забыт).
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
