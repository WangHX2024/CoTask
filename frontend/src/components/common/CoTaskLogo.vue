<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    /** sm: sidebar; md: default; lg: login hero */
    size?: 'sm' | 'md' | 'lg'
    /** White wordmark on gradient panels; dark wordmark on light surfaces */
    variant?: 'on-dark' | 'on-light'
    showWordmark?: boolean
  }>(),
  {
    size: 'md',
    variant: 'on-light',
    showWordmark: true,
  },
)

const classes = computed(() => [
  'cotask-logo',
  `cotask-logo--${props.size}`,
  `cotask-logo--${props.variant}`,
])
</script>

<template>
  <div class="cotask-logo" :class="classes" role="img" aria-label="CoTask">
    <svg
      class="cotask-logo__mark"
      viewBox="0 0 44 44"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect width="44" height="44" rx="10" class="cotask-logo__mark-bg" />
      <circle cx="16.5" cy="22" r="8.5" class="cotask-logo__mark-ring" />
      <circle cx="27.5" cy="22" r="8.5" class="cotask-logo__mark-ring" />
      <circle cx="22" cy="22" r="3" class="cotask-logo__mark-core" />
    </svg>
    <span v-if="showWordmark" class="cotask-logo__word" aria-hidden="true">
      <span class="cotask-logo__co">Co</span><span class="cotask-logo__task">Task</span>
    </span>
  </div>
</template>

<style scoped lang="scss">
.cotask-logo {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  line-height: 1;
  user-select: none;
}

.cotask-logo__mark {
  flex-shrink: 0;
  display: block;
}

.cotask-logo__mark-bg {
  fill: var(--color-primary);
}

.cotask-logo__mark-ring {
  fill: var(--text-inverse);
}

.cotask-logo__mark-core {
  fill: var(--color-primary);
}

.cotask-logo__word {
  display: inline-flex;
  align-items: baseline;
  font-weight: 700;
  letter-spacing: -0.04em;
  white-space: nowrap;
}

.cotask-logo__co {
  color: var(--color-primary);
}

.cotask-logo--on-light .cotask-logo__task {
  color: var(--text-primary);
}

.cotask-logo--on-dark .cotask-logo__co {
  color: rgba(255, 255, 255, 0.92);
}

.cotask-logo--on-dark .cotask-logo__task {
  color: var(--text-inverse);
}

.cotask-logo--sm {
  gap: var(--space-2);

  .cotask-logo__mark {
    width: 28px;
    height: 28px;
  }

  .cotask-logo__word {
    font-size: var(--fs-md);
  }
}

.cotask-logo--md {
  gap: var(--space-2);

  .cotask-logo__mark {
    width: 32px;
    height: 32px;
  }

  .cotask-logo__word {
    font-size: var(--fs-lg);
  }
}

.cotask-logo--lg {
  gap: var(--space-3);

  .cotask-logo__mark {
    width: 40px;
    height: 40px;
  }

  .cotask-logo__word {
    font-size: var(--fs-2xl);
  }
}
</style>
