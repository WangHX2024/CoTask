<template>
  <div class="hero-showcase" :data-slide="slideId" aria-hidden="true">
    <div class="hero-showcase__halo" aria-hidden="true" />
    <FeatureShowcaseScene :slide-id="slideId" variant="glass" />
  </div>
</template>

<script setup lang="ts">
import FeatureShowcaseScene from '@/components/showcase/FeatureShowcaseScene.vue'

defineProps<{
  slideId: string
}>()
</script>

<style scoped lang="scss">
.hero-showcase {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
  max-width: 440px;
  min-height: 212px;
  padding: var(--space-3) 0 var(--space-2);
}

.hero-showcase__halo {
  position: absolute;
  left: 8%;
  right: 4%;
  top: 6%;
  height: 72%;
  border-radius: 50%;
  pointer-events: none;
  opacity: 0.55;
  filter: blur(36px);
  background: radial-gradient(
    ellipse 100% 80% at 50% 50%,
    rgba(255, 255, 255, 0.22),
    transparent 68%
  );
  transition: background 0.5s ease, opacity 0.5s ease;
}

.hero-showcase[data-slide='ai'] .hero-showcase__halo {
  background: radial-gradient(
    ellipse 100% 80% at 40% 40%,
    rgba(196, 181, 253, 0.45),
    transparent 70%
  );
}

.hero-showcase[data-slide='dashboard'] .hero-showcase__halo {
  background: radial-gradient(
    ellipse 100% 80% at 50% 50%,
    rgba(147, 197, 253, 0.38),
    transparent 70%
  );
}

.hero-showcase[data-slide='tree'] .hero-showcase__halo {
  background: radial-gradient(
    ellipse 100% 80% at 50% 50%,
    rgba(167, 139, 250, 0.38),
    transparent 70%
  );
}

.hero-showcase[data-slide='timeline'] .hero-showcase__halo {
  background: radial-gradient(
    ellipse 100% 80% at 50% 50%,
    rgba(94, 234, 212, 0.32),
    transparent 70%
  );
}

.hero-showcase[data-slide='files'] .hero-showcase__halo {
  background: radial-gradient(
    ellipse 100% 80% at 50% 50%,
    rgba(251, 191, 36, 0.28),
    transparent 70%
  );
}

.hero-showcase[data-slide='discussion'] .hero-showcase__halo {
  background: radial-gradient(
    ellipse 100% 80% at 50% 50%,
    rgba(244, 114, 182, 0.32),
    transparent 70%
  );
}

.hero-showcase[data-slide='inspiration'] .hero-showcase__halo {
  background: radial-gradient(
    ellipse 100% 80% at 50% 50%,
    rgba(250, 204, 21, 0.3),
    transparent 70%
  );
}

.hero-showcase :deep(.scene) {
  position: relative;
  z-index: 1;
  min-height: 188px;
}
</style>
