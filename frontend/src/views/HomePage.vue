<template>
  <HomePreview :content="content" />
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useSiteContentStore } from '../stores/siteContent'
import HomePreview from '../components/HomePreview.vue'

const { content } = storeToRefs(useSiteContentStore())
</script>
