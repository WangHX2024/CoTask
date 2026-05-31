<template>
  <div class="tour-illus" :style="{ '--illus-accent': accent }">
    <div class="tour-illus__halo" aria-hidden="true" />
    <FeatureShowcaseScene :slide-id="slideId" variant="light" />
  </div>
</template>

<script setup lang="ts">
import FeatureShowcaseScene from '@/components/showcase/FeatureShowcaseScene.vue'

withDefaults(
  defineProps<{
    slideId: string
    accent?: string
  }>(),
  { accent: '#3d7eff' },
)
</script>

<style scoped lang="scss">
.tour-illus {
  position: relative;
  width: min(300px, 100%);
  min-height: 176px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tour-illus__halo {
  position: absolute;
  inset: 4% 6% 8%;
  border-radius: 50%;
  pointer-events: none;
  opacity: 0.9;
  filter: blur(28px);
  background: radial-gradient(
    ellipse 90% 75% at 50% 45%,
    color-mix(in srgb, var(--illus-accent, #3d7eff) 22%, transparent),
    transparent 72%
  );
}

.tour-illus :deep(.scene) {
  position: relative;
  z-index: 1;
  width: 100%;
}
</style>
