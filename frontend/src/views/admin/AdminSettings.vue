<template>
  <div>
    <Skeleton v-if="loading" height="h-96" />

    <form v-else class="space-y-6" @submit.prevent="save">
      <BaseCard>
        <StepTitle n="1" title="Шапка сайта" />
        <div class="grid gap-4 sm:grid-cols-2">
          <BaseInput v-model="form.header.brand_name" label="Название бренда" required />
          <BaseInput v-model="form.header.brand_tagline" label="Подпись под названием" required />
        </div>
      </BaseCard>

      <BaseCard>
        <StepTitle n="2" title="Главный экран" />
        <div class="space-y-4">
          <BaseInput v-model="form.hero.eyebrow" label="Надпись над заголовком" />
          <BaseInput v-model="form.hero.title" as="textarea" :rows="3" label="Заголовок" hint="Каждая строка — перенос строки в заголовке" required />
          <BaseInput v-model="form.hero.subtitle" as="textarea" label="Подзаголовок" />
          <div class="grid gap-4 sm:grid-cols-2">
            <BaseInput v-model="form.hero.primary_button" label="Текст основной кнопки" required />
            <BaseInput v-model="form.hero.secondary_button" label="Текст второй кнопки" required />
          </div>
          <BaseInput v-model="form.hero.photo_url" label="Фото справа (URL)" placeholder="https://…" hint="Если не указано — показывается заглушка" />
        </div>
      </BaseCard>

      <BaseCard>
        <StepTitle n="3" title="Блок «Почему мы»" />
        <div class="space-y-4">
          <div class="grid gap-4 sm:grid-cols-2">
            <BaseInput v-model="form.features.eyebrow" label="Надпись над заголовком" />
            <BaseInput v-model="form.features.title" label="Заголовок" required />
          </div>
          <div v-for="(item, i) in form.features.items" :key="i" class="grid gap-3 border-t border-stone-200 pt-4 sm:grid-cols-2">
            <BaseInput v-model="item.title" :label="`Карточка ${i + 1} — заголовок`" required />
            <BaseInput v-model="item.text" :label="`Карточка ${i + 1} — текст`" as="textarea" :rows="2" required />
          </div>
        </div>
      </BaseCard>

      <BaseCard>
        <StepTitle n="4" title="Услуги и цены" />
        <div class="grid gap-4 sm:grid-cols-2">
          <BaseInput v-model="form.services.eyebrow" label="Надпись над заголовком" />
          <BaseInput v-model="form.services.title" label="Заголовок" required />
          <BaseInput v-model="form.services.note" as="textarea" :rows="2" label="Примечание справа" class="sm:col-span-2" />
        </div>
      </BaseCard>

      <BaseCard>
        <StepTitle n="5" title="Блок «Мастера»" />
        <div class="grid gap-4 sm:grid-cols-2">
          <BaseInput v-model="form.masters.eyebrow" label="Надпись над заголовком" />
          <BaseInput v-model="form.masters.title" label="Заголовок" required />
        </div>
      </BaseCard>

      <BaseCard>
        <StepTitle n="6" title="Призыв к действию" />
        <div class="space-y-4">
          <div class="grid gap-4 sm:grid-cols-2">
            <BaseInput v-model="form.cta.eyebrow" label="Надпись над заголовком" />
            <BaseInput v-model="form.cta.title" label="Заголовок" required />
          </div>
          <BaseInput v-model="form.cta.subtitle" as="textarea" :rows="2" label="Текст" />
          <BaseInput v-model="form.cta.button_label" label="Текст кнопки" required class="sm:w-64" />
        </div>
      </BaseCard>

      <BaseCard>
        <StepTitle n="7" title="Подвал (footer)" />
        <div class="space-y-4">
          <BaseInput v-model="form.footer.tagline" as="textarea" :rows="2" label="Описание под названием бренда" />
          <div class="grid gap-4 sm:grid-cols-2">
            <BaseInput v-model="form.footer.address" as="textarea" :rows="3" label="Адрес" hint="Каждая строка — перенос строки" />
            <BaseInput v-model="form.footer.hours" as="textarea" :rows="3" label="Часы работы" hint="Каждая строка — перенос строки" />
          </div>
          <div>
            <p class="mb-2 text-sm font-medium text-ink-900">Ссылки «Мы в сети»</p>
            <div v-for="(link, i) in form.footer.social_links" :key="i" class="mb-2 grid gap-3 sm:grid-cols-2">
              <BaseInput v-model="link.label" :label="`Ссылка ${i + 1} — текст`" required />
              <BaseInput v-model="link.url" :label="`Ссылка ${i + 1} — URL`" required />
            </div>
          </div>
          <BaseInput v-model="form.footer.bottom_note" label="Нижняя строка справа" />
        </div>
      </BaseCard>

      <div class="flex justify-end">
        <BaseButton type="submit" :loading="saving">Сохранить все изменения</BaseButton>
      </div>
    </form>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { settingsApi } from '../../api'
import { useToastStore } from '../../stores/toast'
import { useSiteContentStore } from '../../stores/siteContent'
import { extractErrorMessage } from '../../utils/errors'
import BaseCard from '../../components/ui/BaseCard.vue'
import BaseInput from '../../components/ui/BaseInput.vue'
import BaseButton from '../../components/ui/BaseButton.vue'
import Skeleton from '../../components/ui/Skeleton.vue'
import StepTitle from '../../components/ui/StepTitle.vue'

const toast = useToastStore()
const siteContentStore = useSiteContentStore()

const loading = ref(true)
const saving = ref(false)
const form = reactive({})

onMounted(async () => {
  try {
    const { data } = await settingsApi.get()
    Object.assign(form, data)
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить настройки сайта'))
  } finally {
    loading.value = false
  }
})

async function save() {
  saving.value = true
  try {
    const { data } = await settingsApi.update(form)
    Object.assign(form, data)
    siteContentStore.set(data)
    toast.success('Настройки сайта сохранены')
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось сохранить настройки'))
  } finally {
    saving.value = false
  }
}
</script>
