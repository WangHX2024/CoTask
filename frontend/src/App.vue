<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useWS } from '@/composables/useWS'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const ws = useWS()

onMounted(() => {
  if (auth.isAuthed) ws.connect()
})
</script>
