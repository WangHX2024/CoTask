<template>
  <el-select
    :model-value="modelValue"
    class="group-select"
    :class="{
      'group-select--sm': size === 'sm',
      'group-select--dash': variant === 'dash',
    }"
    popper-class="group-select-popper"
    :clearable="clearable"
    :placeholder="placeholder"
    :disabled="disabled || !groups.length"
    @update:model-value="onChange"
  >
    <template #prefix>
      <el-icon class="group-select-icon"><School /></el-icon>
    </template>
    <template v-if="selectedGroup" #label>
      <span class="group-select-value">
        <span v-if="variant !== 'dash'" class="group-select-course">{{ selectedGroup.course_name }}</span>
        <span class="group-select-name">{{ selectedGroup.name }}</span>
        <span class="group-select-role" :class="selectedGroup.role">
          {{ selectedGroup.role === 'leader' ? '组长' : '组员' }}
        </span>
      </span>
    </template>
    <el-option
      v-for="g in groups"
      :key="g.id"
      :value="g.id"
      :label="`${g.course_name} · ${g.name}`"
    >
      <div class="group-opt">
        <span class="group-opt-text">
          <span class="group-opt-course">{{ g.course_name }}</span>
          <span class="group-opt-name">{{ g.name }}</span>
        </span>
        <span class="group-opt-role" :class="g.role">
          {{ g.role === 'leader' ? '组长' : '组员' }}
        </span>
      </div>
    </el-option>
  </el-select>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { School } from '@element-plus/icons-vue'
import type { GroupBrief } from '@/api'

const props = withDefaults(
  defineProps<{
    groups: GroupBrief[]
    modelValue: number | null
    clearable?: boolean
    placeholder?: string
    size?: 'md' | 'sm'
    variant?: 'topbar' | 'dash'
    disabled?: boolean
  }>(),
  {
    clearable: false,
    placeholder: '选择小组',
    size: 'md',
    variant: 'topbar',
    disabled: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
}>()

const selectedGroup = computed(() =>
  props.groups.find((g) => g.id === props.modelValue) ?? null,
)

function onChange(value: number | null | undefined) {
  if (value === undefined || value === '') {
    emit('update:modelValue', null)
    return
  }
  emit('update:modelValue', value as number)
}
</script>

<style lang="scss" scoped>
.group-select {
  width: min(320px, 42vw);

  :deep(.el-select__wrapper) {
    min-height: 36px;
    padding: 0 var(--space-3) 0 var(--space-2);
    background: var(--bg-soft) !important;
    border-radius: var(--control-radius-line) !important;
    box-shadow: none !important;
    transition: background 120ms ease, box-shadow 120ms ease;

    &:hover {
      background: var(--bg-overlay) !important;
      box-shadow: none !important;
    }

    &.is-focused,
    &.is-focus,
    &:focus-within {
      background: var(--bg-card) !important;
      box-shadow: 0 0 0 1px var(--color-primary) inset !important;
    }
  }

  :deep(.el-select__selection) {
    min-width: 0;
  }

  :deep(.el-select__selected-item) {
    overflow: hidden;
  }

  :deep(.el-select__caret) {
    color: var(--text-tertiary);
  }

  &--sm {
    width: min(280px, 100%);

    :deep(.el-select__wrapper) {
      min-height: 32px;
      font-size: var(--fs-sm);
    }
  }

  /* Dashboard todo filter — no filled box, pill outline on interaction */
  &--dash {
    width: fit-content;
    max-width: min(320px, 56vw);

    :deep(.el-select__wrapper) {
      display: inline-flex;
      align-items: center;
      gap: var(--space-2);
      min-height: 30px;
      padding: var(--space-1) 10px var(--space-1) 10px;
      font-size: var(--fs-sm);
      background: transparent !important;
      border: 1px solid transparent;
      border-radius: var(--radius-full) !important;
      box-shadow: none !important;

      &:hover {
        background: var(--bg-soft) !important;
        border-color: var(--border-subtle);
      }

      &.is-focused,
      &.is-focus,
      &:focus-within {
        background: var(--bg-soft) !important;
        border-color: var(--border-color);
        box-shadow: none !important;
      }
    }

    :deep(.el-select__prefix) {
      margin: 0;
      padding: 0;
    }

    :deep(.el-select__selection) {
      position: static;
      flex: 0 1 auto;
      min-width: 0;
      margin: 0;
      padding: 0;
      overflow: visible;
    }

    /* EP renders #label inside .el-select__placeholder (absolute, z-index: -1) — breaks on transparent bg */
    :deep(.el-select__placeholder) {
      position: static !important;
      top: auto !important;
      z-index: auto !important;
      transform: none !important;
      display: inline-flex !important;
      align-items: center;
      width: auto !important;
      max-width: 100%;
      padding: 0;
      color: var(--color-primary);
      font-weight: 500;
      opacity: 1;
      user-select: none;

      &.is-transparent {
        color: var(--text-primary);
        font-weight: 500;
      }
    }

    :deep(.el-select__selected-item) {
      overflow: visible;
      max-width: 100%;
      padding: 0;
    }

    :deep(.el-select__suffix) {
      display: inline-flex;
      align-items: center;
      gap: var(--space-1);
      margin: 0;
      padding: 0;
    }

    :deep(.el-select__clear) {
      margin: 0;
    }

    :deep(.el-select__caret) {
      margin: 0;
      color: var(--text-tertiary);
      flex-shrink: 0;
    }

    .group-select-icon {
      font-size: 15px;
    }

    .group-select-value {
      gap: 6px;
      min-width: 0;
      max-width: 100%;
    }

    .group-select-name {
      flex: 1 1 auto;
      min-width: 2.5em;
      font-size: var(--fs-sm);
      line-height: 1.35;
    }

    .group-select-role {
      padding: 1px 7px;
      line-height: 1.35;
    }
  }
}

.group-select-icon {
  color: var(--color-primary);
  font-size: 16px;
}

.group-select-value {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
  max-width: 100%;
}

.group-select-course {
  flex-shrink: 0;
  font-size: var(--fs-sm);
  color: var(--text-secondary);
}

.group-select-name {
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.group-select-role {
  flex-shrink: 0;
  font-size: var(--fs-xs);
  font-weight: 500;
  line-height: 1.4;
  padding: 1px var(--space-2);
  border-radius: var(--radius-full);
  background: var(--bg-card);
  color: var(--text-tertiary);

  &.leader {
    background: rgba(245, 158, 11, 0.14);
    color: #b45309;
  }
}

.group-opt {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-1) 0;
}

.group-opt-text {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
  min-width: 0;
}

.group-opt-course {
  flex-shrink: 0;
  font-size: var(--fs-sm);
  color: var(--text-secondary);
}

.group-opt-name {
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.group-opt-role {
  flex-shrink: 0;
  font-size: var(--fs-xs);
  font-weight: 500;
  padding: 1px var(--space-2);
  border-radius: var(--radius-full);
  background: var(--bg-soft);
  color: var(--text-tertiary);

  &.leader {
    background: rgba(245, 158, 11, 0.14);
    color: #b45309;
  }
}
</style>
