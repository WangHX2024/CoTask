<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DocumentCopy } from '@element-plus/icons-vue'
import { Api, type TaskNode } from '@/api'
import { useGroupsStore } from '@/stores/groups'
import SegmentedControl from '@/components/common/SegmentedControl.vue'
import TemplatePreviewTree from '@/components/inspiration/TemplatePreviewTree.vue'
import { previewTreeStats } from '@/components/inspiration/templatePreviewTree'
import {
  buildImportPreviewNodes,
  importPreviewHint,
} from '@/components/inspiration/importPreview'

const props = defineProps<{
  modelValue: boolean
  postId: number
  templateNodes: TaskNode[]
}>()

const emit = defineEmits<{
  'update:modelValue': [open: boolean]
  imported: []
}>()

const router = useRouter()
const groupsStore = useGroupsStore()

const importGid = ref(0)
const importMode = ref<'replace' | 'append'>('replace')
const importBusy = ref(false)
const groupPreviewLoading = ref(false)
const groupPreviewNodes = ref<TaskNode[]>([])

const importModeOptions = [
  { label: '替换', value: 'replace' },
  { label: '追加', value: 'append' },
]

const leaderGroups = computed(() =>
  groupsStore.list.filter((g) => g.role === 'leader'),
)

const importPreviewNodes = computed(() => {
  if (!importGid.value) return []
  return buildImportPreviewNodes(
    groupPreviewNodes.value,
    props.templateNodes,
    importMode.value,
  )
})

const importPreviewStats = computed(() => previewTreeStats(importPreviewNodes.value))

const importPreviewHintText = computed(() => {
  if (!importGid.value) return ''
  return importPreviewHint(
    groupPreviewNodes.value,
    props.templateNodes,
    importMode.value,
  )
})

async function loadGroupPreview(groupId: number) {
  groupPreviewNodes.value = []
  if (!groupId) return
  groupPreviewLoading.value = true
  try {
    const tree = await Api.getTree(groupId)
    groupPreviewNodes.value = tree.nodes
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载小组结构失败')
  } finally {
    groupPreviewLoading.value = false
  }
}

function ensureDefaultGroup() {
  if (!leaderGroups.value.length) return
  if (!importGid.value || !leaderGroups.value.some((g) => g.id === importGid.value)) {
    importGid.value = leaderGroups.value[0].id
  }
}

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    ensureDefaultGroup()
    if (importGid.value) void loadGroupPreview(importGid.value)
  },
)

watch(importGid, (gid) => {
  if (props.modelValue && gid) void loadGroupPreview(gid)
})

async function confirmImport() {
  if (!importGid.value) return
  importBusy.value = true
  try {
    await Api.importTemplate(props.postId, importGid.value, importMode.value)
    ElMessage.success('已导入到小组')
    emit('imported')
    emit('update:modelValue', false)
    const target = leaderGroups.value.find((g) => g.id === importGid.value)
    if (target) {
      try {
        await ElMessageBox.confirm('是否立即查看导入后的项目树？', '导入成功', {
          confirmButtonText: '前往',
          cancelButtonText: '留在此页',
        })
        router.push(`/groups/${target.id}/tree`)
      } catch {
        /* stay */
      }
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '导入失败')
  } finally {
    importBusy.value = false
  }
}

function close() {
  emit('update:modelValue', false)
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    width="min(720px, 92vw)"
    class="template-import-dialog"
    destroy-on-close
    @update:model-value="emit('update:modelValue', $event)"
  >
    <template #header>
      <div class="import-dialog__head">
        <el-icon class="import-dialog__icon"><DocumentCopy /></el-icon>
        <div>
          <div class="import-dialog__title">导入到我的小组</div>
          <div class="muted tiny">预览导入后的项目树，确认后再写入小组</div>
        </div>
      </div>
    </template>

    <div v-if="!leaderGroups.length" class="muted">
      你目前不是任何小组的组长，无法导入模板。
    </div>

    <template v-else>
      <label class="import-dialog__lbl">选择小组</label>
      <el-select
        v-model="importGid"
        class="insp-capsule-select import-dialog__select"
        popper-class="insp-select-popper"
        placeholder="选择一个你管理的小组"
      >
        <el-option
          v-for="g in leaderGroups"
          :key="g.id"
          :value="g.id"
          :label="`[${g.course_name}] ${g.name}`"
        />
      </el-select>

      <label class="import-dialog__lbl import-dialog__lbl--spaced">导入模式</label>
      <SegmentedControl
        v-model="importMode"
        size="sm"
        class="import-dialog__mode"
        :options="importModeOptions"
      />

      <div class="import-dialog__preview" v-loading="groupPreviewLoading">
        <div class="template-preview__bar">
          <span class="template-preview__label">导入后项目树预览</span>
          <span v-if="importPreviewStats" class="template-preview__stats muted tiny">
            {{ importPreviewStats }}
          </span>
        </div>
        <p v-if="importPreviewHintText" class="muted tiny template-preview__hint">
          {{ importPreviewHintText }}
        </p>
        <div v-if="importPreviewNodes.length" class="import-dialog__tree">
          <TemplatePreviewTree :nodes="importPreviewNodes" />
        </div>
        <p v-else-if="!groupPreviewLoading" class="muted tiny template-preview__empty">
          {{ templateNodes.length ? '加载小组结构后即可预览' : '模板暂无节点' }}
        </p>
      </div>
    </template>

    <template #footer>
      <div class="import-dialog__footer">
        <button type="button" class="insp-capsule-btn" @click="close">取消</button>
        <button
          type="button"
          class="insp-capsule-btn insp-capsule-btn--primary"
          :disabled="!importGid || !leaderGroups.length || importBusy"
          @click="confirmImport"
        >
          {{ importBusy ? '导入中…' : '确认导入' }}
        </button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped lang="scss">
.import-dialog__head {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
}

.import-dialog__icon {
  font-size: 22px;
  color: var(--color-primary);
  background: var(--color-primary-light);
  padding: var(--space-2);
  border-radius: var(--radius-md);
}

.import-dialog__title {
  font-size: var(--fs-lg);
  font-weight: 600;
  color: var(--text-primary);
}

.import-dialog__lbl {
  display: block;
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: var(--space-2);

  &--spaced {
    margin-top: var(--space-4);
  }
}

.import-dialog__select {
  width: 100%;
}

.import-dialog__mode {
  width: fit-content;
  margin-bottom: var(--space-4);
}

.import-dialog__preview {
  min-height: 120px;
  padding-top: var(--space-3);
  border-top: 1px solid var(--border-subtle);
}

.import-dialog__tree {
  max-height: min(52vh, 420px);
  overflow-y: auto;
  padding: var(--space-1) 0;
}

.import-dialog__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  flex-wrap: wrap;
}
</style>
