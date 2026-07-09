<template>
  <textarea
    v-if="editable && multiline"
    ref="el"
    v-bind="$attrs"
    v-model="local"
    :placeholder="placeholder"
    rows="1"
    class="sai-editable block w-full resize-none overflow-hidden border-0 bg-transparent p-0"
    @input="resize"
  />
  <input
    v-else-if="editable"
    v-bind="$attrs"
    v-model="local"
    :placeholder="placeholder"
    class="sai-editable block w-full border-0 bg-transparent p-0"
  />
  <component :is="tag" v-else v-bind="$attrs">{{ modelValue }}</component>
</template>

<script setup>
import { nextTick, onMounted, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  editable: { type: Boolean, default: false },
  multiline: { type: Boolean, default: false },
  tag: { type: String, default: 'span' },
  placeholder: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])
defineOptions({ inheritAttrs: false })

const el = ref(null)
const local = ref(props.modelValue)

watch(() => props.modelValue, (v) => {
  if (v !== local.value) local.value = v
})
watch(local, (v) => emit('update:modelValue', v))

function resize() {
  if (!el.value) return
  el.value.style.height = 'auto'
  el.value.style.height = `${el.value.scrollHeight}px`
}

onMounted(() => nextTick(resize))
watch(() => props.editable, () => nextTick(resize))
</script>

<style scoped>
.sai-editable {
  font: inherit;
  color: inherit;
  letter-spacing: inherit;
  text-transform: inherit;
  text-align: inherit;
  line-height: inherit;
  outline: none;
  border-radius: 2px;
  box-shadow: 0 0 0 1px transparent;
  transition: box-shadow 0.15s ease, background-color 0.15s ease;
}
.sai-editable:hover {
  box-shadow: 0 0 0 1px rgba(251, 191, 36, 0.6);
}
.sai-editable:focus {
  box-shadow: 0 0 0 2px rgb(251, 191, 36);
  background-color: rgba(251, 191, 36, 0.08);
}
</style>
