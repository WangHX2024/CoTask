<template>
  <div class="files-page page insp-sub-page">
    <!-- Page header -->
    <header class="page-header">
      <div class="page-header-text">
        <h1 class="page-title">文件库</h1>
        <p class="page-desc">{{ groups.current?.course_name }} · {{ groups.current?.name || '小组' }}</p>
      </div>
      <div class="page-header-actions">
        <SegmentedControl
          v-model="viewMode"
          size="md"
          :options="viewModeOptions"
        />
      </div>
    </header>

    <div class="files-layout">
      <!-- Mobile dropdown selector -->
      <div class="mobile-picker">
        <el-select
          v-model="selectedFolderId"
          placeholder="上传目标文件夹"
          class="mobile-select"
          @change="onPickFolder"
        >
          <el-option label="根目录" :value="0" />
          <el-option
            v-for="f in folders"
            :key="f.id"
            :label="folderLabel(f)"
            :value="f.id"
          />
        </el-select>
        <el-select
          v-if="viewMode === 'tag'"
          :model-value="tagFilterUncategorized ? '__uncat__' : selectedTagTaskId"
          placeholder="任务归属筛选"
          class="mobile-select"
          clearable
          @change="onMobileTagChange"
        >
          <el-option label="未分类" value="__uncat__" />
          <el-option
            v-for="opt in tagSelectOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
      </div>

      <div ref="filesSplitRef" class="files-split">
      <!-- LEFT panel -->
      <aside class="left-panel" :style="sidebarStyle">
        <div class="panel-head">
          <span class="panel-title">{{ viewMode === 'folder' ? '文件夹' : '任务归属' }}</span>
          <el-button
            v-if="viewMode === 'folder'"
            text
            size="small"
            class="panel-head-btn"
            title="新建根文件夹"
            @click="openNewFolderDialog(null)"
          >
            <el-icon><Plus /></el-icon>
          </el-button>
        </div>

        <!-- Folder tree (upload target + folder browse) -->
        <div v-if="viewMode === 'folder'" v-loading="folderLoading" class="panel-body">
          <div
            class="list-row"
            :class="{ 'is-active': selectedFolderId === 0 }"
            @click="onPickFolder(0)"
          >
            <el-icon class="list-row__icon"><Folder /></el-icon>
            <span class="list-row__text">根目录</span>
          </div>
          <FolderRow
            v-for="node in folderTree"
            :key="node.id"
            :node="node"
            :selected-id="selectedFolderId"
            @pick="onPickFolder"
            @add-child="openNewFolderDialog"
            @delete="onDeleteFolder"
            @rename="openRenameFolderDialog"
          />
          <div v-if="!folderLoading && folders.length === 0" class="empty-tip">
            可直接在根目录上传；需要分类时点击上方 + 新建文件夹
          </div>
        </div>

        <!-- Task tag tree -->
        <div v-else v-loading="treeLoading" class="panel-body">
          <div
            class="list-row"
            :class="{ 'is-active': tagFilterUncategorized }"
            @click="onPickTagUncategorized"
          >
            <el-icon><Memo /></el-icon>
            <span class="list-row__text">未分类</span>
          </div>
          <TaskTagRow
            v-for="node in taskTree"
            :key="node.id"
            :node="node"
            :selected-id="tagFilterUncategorized ? 0 : (selectedTagTaskId ?? 0)"
            @pick="onPickTagTask"
          />
          <div v-if="!treeLoading && !taskTree.length" class="empty-tip">
            暂无任务节点
          </div>
        </div>

        <div v-if="viewMode === 'tag'" class="panel-foot tiny muted">
          上传时可在弹窗中指定文件夹与任务归属
        </div>
      </aside>

      <ResizeHandle
        v-model="sidebarWidth"
        class="files-split__handle"
        :min="sidebarMin"
        :max="sidebarMax"
        storage-key="cotask.files.sidebar"
      />

      <!-- RIGHT panel -->
      <section class="right-panel">
        <!-- Upload area -->
        <div class="upload-bar">
          <el-upload
            ref="uploadRef"
            drag
            multiple
            :auto-upload="false"
            :show-file-list="false"
            :on-change="onFilePicked"
            class="upload-zone"
            :disabled="!gid"
          >
            <el-icon class="up-icon"><UploadFilled /></el-icon>
            <div class="up-text">
              拖拽文件到此处，或<em>点击选择</em>
            </div>
            <template #tip>
              <div class="tiny muted upload-tip">
                <span>支持任意格式，单文件不超过 {{ uploadMaxMb }}MB</span>
              </div>
            </template>
          </el-upload>

          <div v-if="uploadingItems.length" class="upload-progress">
            <div
              v-for="(item, i) in uploadingItems"
              :key="i"
              class="up-item"
            >
              <div class="up-row">
                <el-icon class="up-row-icon"><Document /></el-icon>
                <span class="up-name">{{ item.name }}</span>
                <el-tag
                  size="small"
                  :type="item.status === 'error' ? 'danger' : item.status === 'done' ? 'success' : 'info'"
                >
                  {{ statusLabel(item.status) }}
                </el-tag>
              </div>
              <p v-if="item.status === 'error' && item.errorMsg" class="up-error tiny">
                {{ item.errorMsg }}
              </p>
              <el-progress
                :percentage="item.percent"
                :status="item.status === 'error' ? 'exception' : item.status === 'done' ? 'success' : undefined"
                :stroke-width="6"
                :show-text="false"
              />
            </div>
          </div>
        </div>

        <p class="list-scope-hint tiny muted">{{ listScopeHint }}</p>

        <!-- File list -->
        <div class="file-table card" v-loading="fileLoading">
          <div v-if="!files.length && !fileLoading" class="ft-empty">
            <el-icon><FolderOpened /></el-icon>
            <span>暂无文件</span>
          </div>
          <table v-else class="ft-table" :style="{ minWidth: `${tableMinWidth}px` }">
            <colgroup>
              <col
                v-for="col in FILE_TABLE_COLUMNS"
                :key="col.id"
                :style="fileTableCols.colStyle(col.id)"
              />
            </colgroup>
            <thead>
              <tr class="ft-toolbar-row">
                <td class="col-check" />
                <td colspan="6" class="ft-toolbar__cell">
                  <div class="ft-toolbar__bar">
                    <span
                      class="ft-toolbar__hint"
                      :class="{ 'is-empty': selectedCount === 0 }"
                    >
                      {{ selectedCount > 0 ? `已选 ${selectedCount} 项` : '勾选文件后可批量操作' }}
                    </span>
                    <div class="ft-toolbar__actions">
                      <button
                        type="button"
                        class="ft-batch-btn"
                        :disabled="selectedCount === 0"
                        @click="openMoveDialog()"
                      >
                        <el-icon><Folder /></el-icon>
                        <span>移动</span>
                      </button>
                      <button
                        type="button"
                        class="ft-batch-btn"
                        :disabled="selectedCount === 0"
                        @click="openTagDialog()"
                      >
                        <el-icon><CollectionTag /></el-icon>
                        <span>归属</span>
                      </button>
                      <button
                        type="button"
                        class="ft-batch-btn"
                        :class="{ 'ft-batch-btn--primary': selectedCount > 0 }"
                        :disabled="selectedCount === 0"
                        @click="onBulkDownload"
                      >
                        <el-icon><Download /></el-icon>
                        <span>下载</span>
                      </button>
                      <button
                        type="button"
                        class="ft-batch-btn ft-batch-btn--danger"
                        :disabled="deletableSelectedCount === 0"
                        @click="onBulkDelete"
                      >
                        <el-icon><Delete /></el-icon>
                        <span>删除</span>
                      </button>
                    </div>
                  </div>
                </td>
              </tr>
              <tr class="ft-head-row">
                <th scope="col" class="col-check">
                  <el-checkbox
                    class="file-check"
                    :model-value="isAllSelected"
                    :indeterminate="isIndeterminate"
                    :disabled="!files.length"
                    aria-label="全选"
                    @change="toggleSelectAll"
                  />
                </th>
                <th scope="col" class="col-name th-resizable">
                  <span class="th-text">文件名</span>
                  <span
                    v-if="fileTableCols.isResizable('name')"
                    class="col-resize-grip"
                    @pointerdown="fileTableCols.onColumnResize('name', $event)"
                  />
                </th>
                <th scope="col" class="col-tag th-resizable">
                  <span class="th-text">任务归属</span>
                  <span
                    v-if="fileTableCols.isResizable('tag')"
                    class="col-resize-grip"
                    @pointerdown="fileTableCols.onColumnResize('tag', $event)"
                  />
                </th>
                <th scope="col" class="col-size th-resizable">
                  <span class="th-text">大小</span>
                  <span
                    v-if="fileTableCols.isResizable('size')"
                    class="col-resize-grip"
                    @pointerdown="fileTableCols.onColumnResize('size', $event)"
                  />
                </th>
                <th scope="col" class="col-user th-resizable">
                  <span class="th-text">上传者</span>
                  <span
                    v-if="fileTableCols.isResizable('user')"
                    class="col-resize-grip"
                    @pointerdown="fileTableCols.onColumnResize('user', $event)"
                  />
                </th>
                <th scope="col" class="col-time th-resizable">
                  <span class="th-text">上传时间</span>
                  <span
                    v-if="fileTableCols.isResizable('time')"
                    class="col-resize-grip"
                    @pointerdown="fileTableCols.onColumnResize('time', $event)"
                  />
                </th>
                <th scope="col" class="col-actions">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="f in files"
                :key="f.id"
                class="ft-row"
                :class="{ 'is-selected': selectedIds.has(f.id) }"
                @click="onRowSelectClick(f, $event)"
              >
                <td class="col-check" @click.stop>
                  <el-checkbox
                    class="file-check"
                    :model-value="selectedIds.has(f.id)"
                    :aria-label="`选择 ${f.filename}`"
                    @change="(v: boolean) => toggleFile(f.id, v)"
                  />
                </td>
                <td class="col-name">
                  <div class="col-name__inner">
                    <el-icon class="mime-icon" :style="{ color: mimeColor(f.mime) }">
                      <component :is="mimeIcon(f.mime)" />
                    </el-icon>
                    <span class="filename" :title="f.filename">{{ f.filename }}</span>
                  </div>
                </td>
                <td class="col-tag">
                  <span class="tag-label" :title="displayTagLabel(f)">{{ displayTagLabel(f) }}</span>
                </td>
                <td class="col-size">{{ humanSize(f.size) }}</td>
                <td class="col-user">{{ f.uploader_name || '—' }}</td>
                <td class="col-time">{{ relativeTime(f.created_at) }}</td>
                <td class="col-actions" @click.stop>
                  <div class="col-actions__inner">
                    <button
                      type="button"
                      class="ft-icon-btn"
                      title="移动"
                      aria-label="移动"
                      @click="openMoveDialog([f])"
                    >
                      <el-icon><Folder /></el-icon>
                    </button>
                    <button
                      type="button"
                      class="ft-icon-btn"
                      title="任务归属"
                      aria-label="任务归属"
                      @click="openTagDialog([f])"
                    >
                      <el-icon><CollectionTag /></el-icon>
                    </button>
                    <button
                      type="button"
                      class="ft-icon-btn"
                      title="下载"
                      aria-label="下载"
                      @click="onDownload(f)"
                    >
                      <el-icon><Download /></el-icon>
                    </button>
                    <el-popconfirm
                      title="确定删除该文件？"
                      @confirm="() => onDelete(f)"
                    >
                      <template #reference>
                        <button
                          type="button"
                          class="ft-icon-btn ft-icon-btn--danger"
                          title="删除"
                          aria-label="删除"
                        >
                          <el-icon><Delete /></el-icon>
                        </button>
                      </template>
                    </el-popconfirm>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
      </div>
    </div>

    <!-- Upload confirm dialog -->
    <el-dialog
      v-model="uploadDialogOpen"
      title="确认上传"
      width="520px"
      :close-on-click-modal="!uploadConfirmBusy"
      @closed="onUploadDialogClosed"
    >
      <p class="tiny muted upload-dialog-summary">
        共 {{ pendingUploadFiles.length }} 个文件，请指定存放位置与任务归属
      </p>
      <ul v-if="pendingUploadFiles.length" class="upload-pending-list">
        <li v-for="(f, i) in pendingUploadFiles" :key="`${f.name}-${i}`">
          <el-icon class="upload-pending-icon"><Document /></el-icon>
          <span class="upload-pending-name" :title="f.name">{{ f.name }}</span>
          <span class="upload-pending-size tiny muted">{{ humanSize(f.size) }}</span>
        </li>
      </ul>
      <el-form label-position="top" class="upload-dialog-form">
        <el-form-item label="上传到文件夹" required>
          <el-select
            v-model="uploadDialogFolderId"
            filterable
            placeholder="选择文件夹"
            style="width: 100%"
          >
            <el-option
              v-for="opt in folderSelectOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="任务归属（可选）">
          <el-select
            v-model="uploadDialogTagId"
            clearable
            filterable
            placeholder="不选则为未分类"
            style="width: 100%"
          >
            <el-option
              v-for="opt in tagSelectOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button :disabled="uploadConfirmBusy" @click="cancelUploadDialog">取消</el-button>
        <el-button
          type="primary"
          :loading="uploadConfirmBusy"
          :disabled="!pendingUploadFiles.length"
          @click="confirmUploadDialog"
        >
          开始上传
        </el-button>
      </template>
    </el-dialog>

    <!-- Move files dialog -->
    <el-dialog v-model="moveDialogOpen" title="移动到文件夹" width="480px">
      <p class="tiny muted batch-dialog-hint">{{ batchDialogFileHint(moveTargetIds) }}</p>
      <el-form label-position="top">
        <el-form-item label="目标文件夹">
          <el-select
            v-model="moveTargetFolderId"
            filterable
            placeholder="选择目标位置"
            class="folder-target-select"
            style="width: 100%"
          >
            <el-option
              v-for="opt in folderSelectOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="moveDialogOpen = false">取消</el-button>
        <el-button type="primary" :loading="moveBusy" @click="onSaveMove">确定移动</el-button>
      </template>
    </el-dialog>

    <!-- Task assignment dialog -->
    <el-dialog v-model="tagDialogOpen" title="设置任务归属" width="480px">
      <p class="tiny muted batch-dialog-hint">{{ batchDialogFileHint(tagEditIds) }}</p>
      <el-form label-position="top">
        <el-form-item label="归属任务（可选任意层级节点）">
          <el-select
            v-model="tagEditValue"
            clearable
            filterable
            placeholder="不选则为未分类"
            class="tag-select"
            style="width: 100%"
          >
            <el-option
              v-for="opt in tagSelectOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="tagDialogOpen = false">取消</el-button>
        <el-button type="primary" :loading="savingTag" @click="onSaveFileTag">保存</el-button>
      </template>
    </el-dialog>

    <!-- Folder create / rename -->
    <el-dialog
      v-model="folderDialogOpen"
      :title="folderDialogMode === 'rename' ? '重命名文件夹' : '新建文件夹'"
      width="420px"
    >
      <el-form @submit.prevent="onSubmitFolderDialog">
        <el-form-item label="名称">
          <el-input
            v-model="folderForm.name"
            maxlength="60"
            placeholder="请输入文件夹名"
            @keyup.enter="onSubmitFolderDialog"
          />
        </el-form-item>
        <el-form-item v-if="folderDialogMode === 'create' && folderForm.parent_id" label="父文件夹">
          <span class="muted">{{ folderName(folderForm.parent_id) || '—' }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="folderDialogOpen = false">取消</el-button>
        <el-button type="primary" :loading="folderDialogBusy" @click="onSubmitFolderDialog">
          {{ folderDialogMode === 'rename' ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ElIcon } from 'element-plus'
import {
  CaretRight,
  CollectionTag,
  Delete,
  Document,
  Download,
  Edit,
  Files as FilesIcon,
  Folder,
  FolderOpened,
  Headset,
  Memo,
  Picture,
  Plus,
  Tickets,
  UploadFilled,
  VideoPlay,
} from '@element-plus/icons-vue'
import { relativeTime } from '@/utils/datetime'
import { Api, type FileInfo, type FolderInfo, type TaskNode } from '@/api'
import { useGroupsStore } from '@/stores/groups'
import SegmentedControl from '@/components/common/SegmentedControl.vue'
import ResizeHandle from '@/components/common/ResizeHandle.vue'
import { useResizableWidth } from '@/composables/useResizableWidth'
import { useResizableColumns, type TableColumnDef } from '@/composables/useResizableColumns'

const FILE_TABLE_COLUMNS: TableColumnDef[] = [
  { id: 'check', defaultWidth: 44, minWidth: 44, maxWidth: 44, resizable: false },
  { id: 'name', defaultWidth: 280, minWidth: 120, maxWidth: 640 },
  { id: 'tag', defaultWidth: 160, minWidth: 80, maxWidth: 360 },
  { id: 'size', defaultWidth: 88, minWidth: 64, maxWidth: 140 },
  { id: 'user', defaultWidth: 100, minWidth: 72, maxWidth: 180 },
  { id: 'time', defaultWidth: 140, minWidth: 100, maxWidth: 220 },
  { id: 'actions', defaultWidth: 120, minWidth: 108, maxWidth: 140, resizable: false },
]

const filesSplitRef = ref<HTMLElement | null>(null)

const {
  width: sidebarWidth,
  style: sidebarStyle,
  minWidth: sidebarMin,
  maxWidth: sidebarMax,
  bindSplitContainer,
} = useResizableWidth({
  defaultWidth: 220,
  minWidth: 140,
  maxWidth: 560,
  mainMinWidth: 220,
})

bindSplitContainer(filesSplitRef)

const fileTableCols = useResizableColumns(FILE_TABLE_COLUMNS, 'cotask.files.tableCols')

const tableMinWidth = computed(() =>
  FILE_TABLE_COLUMNS.reduce((sum, c) => sum + fileTableCols.widths[c.id], 0),
)

const viewModeOptions = [
  { label: '任务归属', value: 'tag' as const },
  { label: '文件夹', value: 'folder' as const },
]

const TREE_INDENT = 12

function treeIndentStyle(depth: number) {
  return { paddingLeft: `${12 + depth * TREE_INDENT}px` }
}

function hTreeActionBtn(
  icon: typeof Edit,
  className: string,
  title: string,
  onClick: (ev: Event) => void,
) {
  return h(
    'button',
    {
      type: 'button',
      class: ['tree-action-btn', className],
      title,
      onClick,
    },
    [h(ElIcon, { size: 14 }, () => h(icon))],
  )
}

function hTreeCaret(hasChildren: boolean, expanded: boolean, onToggle: (ev: Event) => void) {
  if (!hasChildren) {
    return h('span', { class: 'tree-caret-slot tree-caret-slot--empty', 'aria-hidden': 'true' })
  }
  return h(
    'span',
    { class: 'tree-caret-slot', onClick: onToggle },
    [
      h(ElIcon, { class: ['tree-caret', expanded ? 'is-expanded' : ''] }, () => h(CaretRight)),
    ],
  )
}

// ---------- folder row component (inline definition) ----------
const FolderRow = {
  name: 'FolderRow',
  props: {
    node: { type: Object, required: true },
    selectedId: { type: Number, default: 0 },
    depth: { type: Number, default: 0 },
  },
  emits: ['pick', 'add-child', 'rename', 'delete'],
  setup(props: any, { emit }: any) {
    const expanded = ref(true)
    return () => {
      const hasChildren = props.node.children?.length > 0
      const rowClass = ['list-row']
      if (props.selectedId === props.node.id) rowClass.push('is-active')
      const handle = (ev: Event) => {
        ev.stopPropagation()
        emit('pick', props.node.id)
      }
      const toggle = (ev: Event) => {
        ev.stopPropagation()
        expanded.value = !expanded.value
      }
      const addChild = (ev: Event) => {
        ev.stopPropagation()
        emit('add-child', props.node.id)
      }
      const renameFolder = (ev: Event) => {
        ev.stopPropagation()
        emit('rename', props.node.id)
      }
      const removeFolder = (ev: Event) => {
        ev.stopPropagation()
        emit('delete', props.node.id)
      }
      const folderIcon = hasChildren && expanded.value ? FolderOpened : Folder
      return h('div', { class: 'tree-row-wrap' }, [
        h(
          'div',
          {
            class: [...rowClass, 'tree-row'],
            style: treeIndentStyle(props.depth),
            onClick: handle,
          },
          [
            hTreeCaret(hasChildren, expanded.value, toggle),
            h(ElIcon, { class: 'list-row__icon' }, () => h(folderIcon)),
            h('span', { class: 'list-row__text' }, props.node.name),
            h('span', { class: 'tree-row-actions' }, [
              hTreeActionBtn(Edit, '', '重命名', renameFolder),
              hTreeActionBtn(Plus, '', '新建子文件夹', addChild),
              hTreeActionBtn(Delete, 'tree-action-btn--danger', '删除文件夹及其中全部文件', removeFolder),
            ]),
          ],
        ),
        hasChildren && expanded.value
          ? h(
              'div',
              {},
              props.node.children.map((c: any) =>
                h(FolderRow as any, {
                  node: c,
                  selectedId: props.selectedId,
                  depth: props.depth + 1,
                  onPick: (id: number) => emit('pick', id),
                  'onAdd-child': (id: number) => emit('add-child', id),
                  onRename: (id: number) => emit('rename', id),
                  onDelete: (id: number) => emit('delete', id),
                }),
              ),
            )
          : null,
      ])
    }
  },
}

// ---------- task tag row (any tree depth) ----------
interface TaskTreeNode extends TaskNode {
  children: TaskTreeNode[]
}

const TaskTagRow = {
  name: 'TaskTagRow',
  props: {
    node: { type: Object, required: true },
    selectedId: { type: Number, default: 0 },
    depth: { type: Number, default: 0 },
  },
  emits: ['pick'],
  setup(props: any, { emit }: any) {
    const expanded = ref(true)
    return () => {
      const hasChildren = props.node.children?.length > 0
      const rowClass = ['list-row']
      if (props.selectedId === props.node.id) rowClass.push('is-active')
      const handle = (ev: Event) => {
        ev.stopPropagation()
        emit('pick', props.node.id)
      }
      const toggle = (ev: Event) => {
        ev.stopPropagation()
        expanded.value = !expanded.value
      }
      return h('div', { class: 'tree-row-wrap' }, [
        h(
          'div',
          {
            class: [...rowClass, 'tree-row'],
            style: treeIndentStyle(props.depth),
            onClick: handle,
          },
          [
            hTreeCaret(hasChildren, expanded.value, toggle),
            h(ElIcon, { class: 'list-row__icon' }, () => h(CollectionTag)),
            h('span', { class: 'list-row__text' }, props.node.title),
          ],
        ),
        hasChildren && expanded.value
          ? h(
              'div',
              {},
              props.node.children.map((c: TaskTreeNode) =>
                h(TaskTagRow as any, {
                  node: c,
                  selectedId: props.selectedId,
                  depth: props.depth + 1,
                  onPick: (id: number) => emit('pick', id),
                }),
              ),
            )
          : null,
      ])
    }
  },
}

// ---------- store / route ----------
const route = useRoute()
const groups = useGroupsStore()

const gid = computed(() => Number(route.params.gid))

// ---------- state ----------
const viewMode = ref<'folder' | 'tag'>('tag')

const treeLoading = ref(false)
const folderLoading = ref(false)
const fileLoading = ref(false)

const tasks = ref<TaskNode[]>([])
const folders = ref<FolderInfo[]>([])
const files = ref<FileInfo[]>([])

const selectedIds = ref<Set<number>>(new Set())

const selectedFolderId = ref<number>(0)
const selectedTagTaskId = ref<number | null>(null)
const tagFilterUncategorized = ref(false)

const tagDialogOpen = ref(false)
const tagEditIds = ref<number[]>([])
const tagEditValue = ref<number | null>(null)
const savingTag = ref(false)

const moveDialogOpen = ref(false)
const moveTargetIds = ref<number[]>([])
const moveTargetFolderId = ref<number>(0)
const moveBusy = ref(false)

const uploadDialogOpen = ref(false)
const pendingUploadFiles = ref<File[]>([])
const uploadDialogFolderId = ref(0)
const uploadDialogTagId = ref<number | null>(null)
const uploadConfirmBusy = ref(false)

// upload progress
const UPLOAD_MAX_BYTES = 100 * 1024 * 1024
const uploadMaxMb = UPLOAD_MAX_BYTES / (1024 * 1024)
/** Skip full-file SHA-256 above this to avoid browser OOM on large Office archives */
const HASH_FULL_MAX_BYTES = 32 * 1024 * 1024

interface UpItem {
  name: string
  size: number
  percent: number
  status: 'pending' | 'uploading' | 'finalizing' | 'done' | 'error'
  errorMsg?: string
}
const uploadingItems = ref<UpItem[]>([])
const uploadRef = ref<any>(null)

// folder create / rename dialog
const folderDialogOpen = ref(false)
const folderDialogMode = ref<'create' | 'rename'>('create')
const folderForm = reactive<{ id: number; name: string; parent_id: number | null }>({
  id: 0,
  name: '',
  parent_id: null,
})
const folderDialogBusy = ref(false)

// ---------- derived ----------
interface FolderTreeNode extends FolderInfo {
  children: FolderTreeNode[]
}
const folderTree = computed<FolderTreeNode[]>(() => {
  const map = new Map<number, FolderTreeNode>()
  folders.value.forEach((f) =>
    map.set(f.id, { ...f, children: [] } as FolderTreeNode),
  )
  const roots: FolderTreeNode[] = []
  map.forEach((node) => {
    if (node.parent_id && map.has(node.parent_id)) {
      map.get(node.parent_id)!.children.push(node)
    } else {
      roots.push(node)
    }
  })
  return roots
})

const taskTree = computed<TaskTreeNode[]>(() => {
  const map = new Map<number, TaskTreeNode>()
  tasks.value.forEach((t) =>
    map.set(t.id, { ...t, children: [] } as TaskTreeNode),
  )
  const roots: TaskTreeNode[] = []
  map.forEach((node) => {
    if (node.parent_id && map.has(node.parent_id)) {
      map.get(node.parent_id)!.children.push(node)
    } else {
      roots.push(node)
    }
  })
  const sortNodes = (list: TaskTreeNode[]) => {
    list.sort((a, b) => a.position - b.position)
    list.forEach((n) => sortNodes(n.children))
  }
  sortNodes(roots)
  return roots
})

const tagSelectOptions = computed(() =>
  tasks.value
    .slice()
    .sort((a, b) => a.path.localeCompare(b.path) || a.position - b.position)
    .map((t) => ({
      value: t.id,
      label: `${'　'.repeat(t.depth)}${t.title}`,
    })),
)

const folderSelectOptions = computed(() => {
  const opts: { value: number; label: string }[] = [{ value: 0, label: '根目录' }]
  const sorted = folders.value.slice().sort((a, b) => a.path.localeCompare(b.path))
  for (const f of sorted) {
    const depth = Math.max(0, f.path.split('/').filter(Boolean).length - 1)
    opts.push({
      value: f.id,
      label: `${'　'.repeat(depth)}${f.name}`,
    })
  }
  return opts
})

const selectedFiles = computed(() =>
  files.value.filter((f) => selectedIds.value.has(f.id)),
)
const selectedCount = computed(() => selectedIds.value.size)
const deletableSelectedCount = computed(() =>
  selectedFiles.value.filter((f) => canDelete(f)).length,
)
const isAllSelected = computed(
  () => files.value.length > 0 && files.value.every((f) => selectedIds.value.has(f.id)),
)
const isIndeterminate = computed(
  () => selectedCount.value > 0 && !isAllSelected.value,
)

const listScopeHint = computed(() => {
  if (viewMode.value === 'folder') {
    return selectedFolderId.value === 0
      ? '当前位置：根目录'
      : selectedFolderId.value > 0
        ? `当前文件夹：${folderName(selectedFolderId.value)}`
        : '请选择根目录或文件夹'
  }
  if (tagFilterUncategorized.value) return '任务归属：未分类'
  if (selectedTagTaskId.value) {
    const t = tasks.value.find((x) => x.id === selectedTagTaskId.value)
    return t ? `任务归属：${t.title}（含子任务）` : '任务归属（含子任务）'
  }
  return '请选择任务归属或「未分类」'
})

// ---------- load ----------
async function loadTree() {
  if (!gid.value) return
  treeLoading.value = true
  try {
    const tree = await Api.getTree(gid.value)
    tasks.value = tree.nodes
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载任务树失败')
  } finally {
    treeLoading.value = false
  }
}

async function loadFolders() {
  if (!gid.value) return
  folderLoading.value = true
  try {
    folders.value = await Api.listFolders(gid.value)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载文件夹失败')
  } finally {
    folderLoading.value = false
  }
}

async function loadFiles() {
  if (!gid.value) return
  fileLoading.value = true
  try {
    const params: Record<string, unknown> = {}
    if (viewMode.value === 'folder') {
      if (selectedFolderId.value === 0) {
        params.folder_root = true
      } else {
        params.folder_id = selectedFolderId.value
      }
    } else if (tagFilterUncategorized.value) {
      params.tag_uncategorized = true
    } else if (selectedTagTaskId.value) {
      params.tag_task_id = selectedTagTaskId.value
    } else {
      files.value = []
      return
    }
    const list = await Api.listFiles(gid.value, params)
    files.value = Array.isArray(list) ? [...list] : []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载文件失败')
  } finally {
    fileLoading.value = false
  }
}

function removeFilesFromList(ids: number[]) {
  if (!ids.length) return
  const idSet = new Set(ids)
  files.value = files.value.filter((f) => !idSet.has(f.id))
  const next = new Set(selectedIds.value)
  for (const id of ids) next.delete(id)
  selectedIds.value = next
}

// ---------- pickers ----------
function onPickFolder(id: number) {
  if (id < 0) return
  clearSelection()
  selectedFolderId.value = id
  if (viewMode.value === 'folder') void loadFiles()
}

function onPickTagTask(id: number) {
  clearSelection()
  tagFilterUncategorized.value = false
  selectedTagTaskId.value = id
  void loadFiles()
}

function onPickTagUncategorized() {
  clearSelection()
  selectedTagTaskId.value = null
  tagFilterUncategorized.value = true
  void loadFiles()
}

function onMobileTagChange(val: number | string | null) {
  if (val === '__uncat__' || val == null) {
    onPickTagUncategorized()
    return
  }
  onPickTagTask(Number(val))
}

watch(viewMode, () => {
  clearSelection()
  if (viewMode.value === 'tag') {
    ensureDefaultTagSelection()
  }
  void loadFiles()
})

// ---------- folder ops ----------
function openNewFolderDialog(parentId: number | null) {
  folderDialogMode.value = 'create'
  folderForm.id = 0
  folderForm.name = ''
  folderForm.parent_id = parentId
  folderDialogOpen.value = true
}

function openRenameFolderDialog(folderId: number) {
  folderDialogMode.value = 'rename'
  folderForm.id = folderId
  folderForm.name = folderName(folderId)
  folderForm.parent_id = null
  folderDialogOpen.value = true
}

function folderSubtreeIds(rootId: number): number[] {
  const ids = [rootId]
  const stack = [rootId]
  while (stack.length) {
    const pid = stack.pop()!
    for (const f of folders.value) {
      if (f.parent_id === pid) {
        ids.push(f.id)
        stack.push(f.id)
      }
    }
  }
  return ids
}

async function onSubmitFolderDialog() {
  const name = folderForm.name.trim()
  if (!name) {
    ElMessage.warning('请输入文件夹名')
    return
  }
  folderDialogBusy.value = true
  try {
    if (folderDialogMode.value === 'rename') {
      await Api.renameFolder(gid.value, folderForm.id, name)
      folderDialogOpen.value = false
      ElMessage.success('已重命名')
      await loadFolders()
    } else {
      const created = await Api.createFolder(gid.value, {
        name,
        parent_id: folderForm.parent_id || undefined,
      })
      folderDialogOpen.value = false
      ElMessage.success('文件夹已创建')
      await loadFolders()
      selectedFolderId.value = created.id
      if (viewMode.value === 'folder') void loadFiles()
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  } finally {
    folderDialogBusy.value = false
  }
}

async function onDeleteFolder(folderId: number) {
  const label = folderName(folderId) || '该文件夹'
  try {
    await ElMessageBox.confirm(
      `将删除「${label}」及其所有子文件夹，并永久删除其中的全部文件。此操作不可恢复。`,
      '删除文件夹',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  const removedIds = new Set(folderSubtreeIds(folderId))
  try {
    const res = await Api.deleteFolder(gid.value, folderId)
    const parts: string[] = []
    if (res.deleted_folders > 0) parts.push(`${res.deleted_folders} 个文件夹`)
    if (res.deleted_files > 0) parts.push(`${res.deleted_files} 个文件`)
    ElMessage.success(parts.length ? `已删除 ${parts.join('、')}` : '已删除')
    if (removedIds.has(selectedFolderId.value)) {
      selectedFolderId.value = 0
    }
    clearSelection()
    await loadFolders()
    void loadFiles()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '删除失败')
  }
}

function batchDialogFileHint(ids: number[]): string {
  if (!ids.length) return ''
  const names = files.value.filter((f) => ids.includes(f.id)).map((f) => f.filename)
  if (names.length === 1) return `文件：${names[0]}`
  const preview = names.slice(0, 3).join('、')
  const more = names.length > 3 ? ` 等 ${names.length} 个文件` : `（共 ${names.length} 个）`
  return `已选：${preview}${more}`
}

function mergeFileUpdates(items: FileInfo[]) {
  if (!items.length) return
  const byId = new Map(items.map((f) => [f.id, f]))
  files.value = files.value.map((f) => byId.get(f.id) ?? f)
}

function resolveTagTargets(targets?: FileInfo[]): FileInfo[] {
  const list = targets?.length ? targets : selectedFiles.value
  return list
}

function openTagDialog(targets?: FileInfo[]) {
  const list = resolveTagTargets(targets)
  if (!list.length) {
    ElMessage.warning('请先勾选文件')
    return
  }
  tagEditIds.value = list.map((f) => f.id)
  const tags = list.map((f) => f.tag_task_id ?? f.task_id ?? null)
  const first = tags[0] ?? null
  tagEditValue.value = tags.every((t) => t === first) ? first : null
  tagDialogOpen.value = true
}

function openMoveDialog(targets?: FileInfo[]) {
  const list = resolveTagTargets(targets)
  if (!list.length) {
    ElMessage.warning('请先勾选文件')
    return
  }
  moveTargetIds.value = list.map((f) => f.id)
  if (list.length === 1) {
    moveTargetFolderId.value = list[0].folder_id ?? 0
  } else {
    moveTargetFolderId.value = selectedFolderId.value
  }
  moveDialogOpen.value = true
}

async function onSaveFileTag() {
  if (!tagEditIds.value.length) return
  savingTag.value = true
  try {
    const res = await Api.bulkUpdateFileTags(gid.value, {
      file_ids: tagEditIds.value,
      tag_task_id: tagEditValue.value,
    })
    mergeFileUpdates(res.items)
    tagDialogOpen.value = false
    ElMessage.success(`已更新 ${res.updated} 个文件的任务归属`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
  } finally {
    savingTag.value = false
  }
}

async function onSaveMove() {
  if (!moveTargetIds.value.length) return
  moveBusy.value = true
  try {
    const res = await Api.moveFiles(gid.value, {
      file_ids: moveTargetIds.value,
      folder_id: moveTargetFolderId.value,
    })
    moveDialogOpen.value = false
    clearSelection()
    await loadFiles()
    ElMessage.success(`已移动 ${res.updated} 个文件到「${folderName(moveTargetFolderId.value)}」`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '移动失败')
  } finally {
    moveBusy.value = false
  }
}

function displayTagLabel(f: FileInfo): string {
  return f.tag_label || (f.tag_task_id || f.task_id ? '—' : '未分类')
}

// ---------- upload ----------
let uploadBatchTimer: ReturnType<typeof setTimeout> | null = null
let uploadBatchRunning = false

function onFilePicked(_file: unknown, uploadFiles: { raw?: File }[]) {
  // `:on-change` fires once per file; debounce so multi-select runs as one batch
  if (uploadBatchTimer) clearTimeout(uploadBatchTimer)
  uploadBatchTimer = setTimeout(() => {
    uploadBatchTimer = null
    const raws = uploadFiles.map((f) => f.raw).filter((f): f is File => !!f)
    if (!raws.length) return
    openUploadDialog(raws)
  }, 80)
}

function openUploadDialog(raws: File[]) {
  pendingUploadFiles.value = raws
  uploadDialogFolderId.value = selectedFolderId.value
  if (
    viewMode.value === 'tag' &&
    !tagFilterUncategorized.value &&
    selectedTagTaskId.value
  ) {
    uploadDialogTagId.value = selectedTagTaskId.value
  } else {
    uploadDialogTagId.value = null
  }
  uploadDialogOpen.value = true
}

function cancelUploadDialog() {
  uploadDialogOpen.value = false
}

function onUploadDialogClosed() {
  if (!uploadConfirmBusy.value) {
    pendingUploadFiles.value = []
    uploadRef.value?.clearFiles?.()
  }
}

async function confirmUploadDialog() {
  const raws = [...pendingUploadFiles.value]
  if (!raws.length || !gid.value) return
  uploadConfirmBusy.value = true
  uploadDialogOpen.value = false
  const folderId = uploadDialogFolderId.value
  const tagTaskId = uploadDialogTagId.value
  try {
    await processUploadBatch(raws, { folderId, tagTaskId })
    if (viewMode.value === 'folder' && selectedFolderId.value !== folderId) {
      selectedFolderId.value = folderId
    }
    await loadFiles()
  } finally {
    uploadConfirmBusy.value = false
    pendingUploadFiles.value = []
    uploadRef.value?.clearFiles?.()
  }
}

interface UploadBatchOptions {
  folderId: number
  tagTaskId: number | null
}

async function processUploadBatch(files: File[], opts: UploadBatchOptions) {
  if (uploadBatchRunning) return
  if (!gid.value) {
    ElMessage.warning('未选择小组')
    uploadRef.value?.clearFiles?.()
    return
  }

  uploadBatchRunning = true
  const items: UpItem[] = files.map((raw) => ({
    name: raw.name,
    size: raw.size,
    percent: 0,
    status: 'pending' as const,
  }))
  uploadingItems.value = items

  let uploaded = 0
  let deduped = 0
  let failed = 0

  for (let i = 0; i < files.length; i++) {
    try {
      const result = await uploadOne(files[i], items[i], opts)
      if (result.deduped) deduped++
      else uploaded++
    } catch (e: any) {
      items[i].status = 'error'
      items[i].errorMsg = uploadErrorMessage(e)
      failed++
    }
  }

  uploadRef.value?.clearFiles?.()
  showUploadSummary(uploaded, deduped, failed)
  uploadBatchRunning = false

  if (failed === 0) {
    window.setTimeout(() => {
      if (!uploadBatchRunning) uploadingItems.value = []
    }, 4000)
  }
}

function showUploadSummary(uploaded: number, deduped: number, failed: number) {
  const ok = uploaded + deduped
  if (ok === 0 && failed > 0) {
    ElMessage.error(failed === 1 ? '上传失败' : `${failed} 个文件上传失败`)
    return
  }
  if (failed > 0) {
    ElMessage.warning(`${ok} 个成功，${failed} 个失败`)
    return
  }
  if (ok === 0) return
  if (ok === 1) {
    ElMessage.success(deduped === 1 ? '秒传成功' : '上传完成')
    return
  }
  const parts: string[] = []
  if (uploaded > 0) parts.push(`${uploaded} 个已上传`)
  if (deduped > 0) parts.push(`${deduped} 个秒传`)
  ElMessage.success(`已完成 ${ok} 个文件（${parts.join('，')}）`)
}

function uploadErrorMessage(e: any): string {
  const msg = e?.response?.data?.message || e?.message
  if (msg) return String(msg)
  return '上传失败'
}

async function uploadOne(
  raw: File,
  item: UpItem,
  opts: UploadBatchOptions,
): Promise<{ deduped: boolean }> {
  if (raw.size > UPLOAD_MAX_BYTES) {
    throw new Error(`文件超过 ${uploadMaxMb}MB 上限`)
  }

  item.status = 'uploading'
  // 1. compute hash (SHA-256 hex used as md5 stand-in for v1)
  const md5 = await computeHash(raw)

  // 2. sign
  const signParams: any = {
    filename: raw.name,
    size: raw.size,
    md5,
    mime: raw.type || 'application/octet-stream',
    group_id: gid.value,
    visibility: 'group',
  }
  signParams.folder_id = opts.folderId
  if (opts.tagTaskId != null) {
    signParams.tag_task_id = opts.tagTaskId
  }

  const signResp: any = await Api.signUpload(signParams)
  const fileId: number = signResp.file_id ?? signResp.id

  // 3. dedup
  if (signResp.deduped) {
    item.percent = 100
    item.status = 'finalizing'
    await Api.finalizeFile(fileId)
    item.status = 'done'
    return { deduped: true }
  }

  // 4. upload
  if (signResp.upload_url) {
    await putWithProgress(signResp.upload_url, raw, (p) => {
      item.percent = Math.round(p * 100)
    })
  }
  item.percent = 100
  item.status = 'finalizing'

  // 5. finalize
  await Api.finalizeFile(fileId)
  item.status = 'done'
  return { deduped: false }
}

function putWithProgress(
  url: string,
  raw: File,
  onProgress: (p: number) => void,
) {
  return new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('PUT', url)
    // Do not set Content-Type: it must match the presigned signature (minio 7.x presign has no CT binding)
    xhr.upload.onprogress = (ev: ProgressEvent) => {
      if (ev.lengthComputable) onProgress(ev.loaded / ev.total)
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve()
      else reject(new Error(`上传失败 (HTTP ${xhr.status})`))
    }
    xhr.onerror = () => {
      reject(new Error('无法连接对象存储，请确认 MinIO 已启动且 MINIO_PUBLIC_ENDPOINT 可从浏览器访问'))
    }
    xhr.send(raw)
  })
}

async function computeHash(file: File): Promise<string> {
  if (file.size > HASH_FULL_MAX_BYTES) {
    return fallbackFileHash(file)
  }
  try {
    const buf = await file.arrayBuffer()
    const hash = await crypto.subtle.digest('SHA-256', buf)
    const bytes = new Uint8Array(hash)
    let hex = ''
    for (let i = 0; i < bytes.length; i++) {
      hex += bytes[i].toString(16).padStart(2, '0')
    }
    return hex
  } catch {
    return fallbackFileHash(file)
  }
}

function fallbackFileHash(file: File): string {
  return `${file.name}-${file.size}-${file.lastModified}`.slice(0, 64)
}

// ---------- selection ----------
function clearSelection() {
  selectedIds.value = new Set()
}

function toggleFile(id: number, checked: boolean) {
  const next = new Set(selectedIds.value)
  if (checked) next.add(id)
  else next.delete(id)
  selectedIds.value = next
}

function toggleSelectAll(checked: boolean | string | number) {
  const on = checked === true
  selectedIds.value = on ? new Set(files.value.map((f) => f.id)) : new Set()
}

function onRowSelectClick(f: FileInfo, ev: MouseEvent) {
  const target = ev.target as HTMLElement
  if (target.closest('.el-checkbox')) return
  toggleFile(f.id, !selectedIds.value.has(f.id))
}

// ---------- file actions ----------
function triggerDownload(f: FileInfo) {
  if (!f.download_url) return false
  const a = document.createElement('a')
  a.href = f.download_url
  a.download = f.filename
  a.rel = 'noopener'
  a.target = '_blank'
  document.body.appendChild(a)
  a.click()
  a.remove()
  return true
}

function onDownload(f: FileInfo) {
  if (!triggerDownload(f)) {
    ElMessage.warning('下载链接不可用')
  }
}

function canDelete(_f: FileInfo): boolean {
  return true
}

async function onBulkDownload() {
  const list = selectedFiles.value.filter((f) => f.download_url)
  if (!list.length) {
    ElMessage.warning('所选文件暂无下载链接')
    return
  }
  for (let i = 0; i < list.length; i++) {
    triggerDownload(list[i])
    if (i < list.length - 1) {
      await new Promise((r) => window.setTimeout(r, 400))
    }
  }
  ElMessage.success(
    list.length === 1 ? '已开始下载' : `已开始下载 ${list.length} 个文件`,
  )
}

async function onBulkDelete() {
  const deletable = selectedFiles.value.filter((f) => canDelete(f))
  const skipped = selectedCount.value - deletable.length
  if (!deletable.length) {
    ElMessage.warning('所选文件均无权删除')
    return
  }
  const hint =
    skipped > 0 ? `（${skipped} 个无权限的将跳过）` : ''
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${deletable.length} 个文件？${hint}`,
      '批量删除',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }

  let ok = 0
  let fail = 0
  const removedIds: number[] = []
  for (const f of deletable) {
    try {
      await Api.deleteFile(f.id)
      ok++
      removedIds.push(f.id)
    } catch {
      fail++
    }
  }
  removeFilesFromList(removedIds)
  clearSelection()
  await loadFiles()
  if (fail === 0) {
    ElMessage.success(ok === 1 ? '已删除' : `已删除 ${ok} 个文件`)
  } else {
    ElMessage.warning(`${ok} 个已删除，${fail} 个失败`)
  }
}

async function onDelete(f: FileInfo) {
  try {
    await Api.deleteFile(f.id)
    removeFilesFromList([f.id])
    ElMessage.success('已删除')
    await loadFiles()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '删除失败')
  }
}

// ---------- helpers ----------
function humanSize(n: number) {
  if (n == null) return '—'
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  if (n < 1024 * 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MB`
  return `${(n / 1024 / 1024 / 1024).toFixed(2)} GB`
}
function statusLabel(s: string): string {
  return ({
    pending: '等待',
    uploading: '上传中',
    finalizing: '处理中',
    done: '完成',
    error: '失败',
  } as Record<string, string>)[s] || s
}

function mimeIcon(mime?: string) {
  const m = mime || ''
  if (m.startsWith('image/')) return Picture
  if (m.startsWith('video/')) return VideoPlay
  if (m.startsWith('audio/')) return Headset
  if (m.includes('pdf')) return Tickets
  if (m.includes('word') || m.includes('msword') || m.includes('officedocument.wordprocessing')) return Document
  if (m.includes('zip') || m.includes('rar') || m.includes('compressed') || m.includes('tar')) return FilesIcon
  if (m.startsWith('text/') || m.includes('json') || m.includes('xml')) return Memo
  return Document
}
function mimeColor(mime?: string): string {
  const m = mime || ''
  if (m.startsWith('image/')) return 'var(--color-success)'
  if (m.startsWith('video/')) return 'var(--color-danger)'
  if (m.startsWith('audio/')) return 'var(--color-warning)'
  if (m.includes('pdf')) return 'var(--color-danger)'
  if (m.startsWith('text/')) return 'var(--color-info)'
  return 'var(--color-primary)'
}

function folderName(id: number): string {
  if (id === 0) return '根目录'
  return folders.value.find((x) => x.id === id)?.name || ''
}
function folderLabel(f: FolderInfo): string {
  if (!f.path) return f.name
  return f.path
}

function applyRouteQuery() {
  const q = route.query
  if (q.view === 'tag') {
    viewMode.value = 'tag'
    tagFilterUncategorized.value = false
    const tid = Number(q.tag_task_id)
    if (tid > 0) selectedTagTaskId.value = tid
  } else if (q.view === 'folder') {
    viewMode.value = 'folder'
  }
}

/** Default tag view: pick first root task, or「未分类」when tree is empty. */
function ensureDefaultTagSelection() {
  if (viewMode.value !== 'tag') return
  const q = route.query
  if (q.view === 'tag' && Number(q.tag_task_id) > 0) return
  if (tagFilterUncategorized.value || selectedTagTaskId.value != null) return

  const roots = taskTree.value
  if (roots.length > 0) {
    tagFilterUncategorized.value = false
    selectedTagTaskId.value = roots[0].id
  } else {
    tagFilterUncategorized.value = true
    selectedTagTaskId.value = null
  }
}

// ---------- mount ----------
onMounted(async () => {
  await Promise.all([loadTree(), loadFolders()])
  applyRouteQuery()
  ensureDefaultTagSelection()
  void loadFiles()
})

// react to gid change (group switch)
watch(gid, async () => {
  clearSelection()
  selectedFolderId.value = 0
  selectedTagTaskId.value = null
  tagFilterUncategorized.value = false
  files.value = []
  await Promise.all([loadTree(), loadFolders()])
  applyRouteQuery()
  ensureDefaultTagSelection()
  void loadFiles()
})

watch(
  () => route.query.tag_task_id,
  () => {
    applyRouteQuery()
    void loadFiles()
  },
)
</script>

<style lang="scss">
@use '@/styles/inspiration-pages.scss';
</style>

<style lang="scss" scoped>
.files-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  flex: 1;
  min-height: 0;
  padding: var(--space-6);
  box-sizing: border-box;
}

.files-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  min-width: 0;
  gap: var(--space-4);
  align-items: stretch;
}

.files-split {
  display: flex;
  flex: 1;
  min-height: 0;
  min-width: 0;
  gap: var(--space-4);
  align-items: stretch;
}

.files-split__handle {
  flex-shrink: 0;
  margin: 0 calc(var(--space-2) * -1);
}

.left-panel {
  flex-shrink: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: var(--shadow-xs);
}

.panel-head {
  height: 48px;
  padding: 0 var(--space-4);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;

  .panel-title {
    font-weight: 600;
    font-size: var(--fs-sm);
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .panel-head-btn {
    color: var(--text-tertiary);
    &:hover {
      color: var(--color-primary);
    }
  }
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2);
}

/* File / folder rows use global .list-row */
.empty-tip {
  padding: var(--space-4);
  text-align: center;
  color: var(--text-tertiary);
  font-size: var(--fs-sm);
}

/* Tree rows (folders + task tags) — aligned with global .list-row / Discussion channels */
.tree-row-wrap :deep(.tree-row) {
  padding-right: var(--space-1);

  &:hover .tree-row-actions,
  &.is-active .tree-row-actions {
    opacity: 1;
  }
}

.tree-row-wrap :deep(.tree-caret-slot) {
  width: 16px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-tertiary);
}

.tree-row-wrap :deep(.tree-caret-slot--empty) {
  cursor: default;
  pointer-events: none;
}

.tree-row-wrap :deep(.tree-caret) {
  font-size: 12px;
  transition: transform 150ms ease;

  &.is-expanded {
    transform: rotate(90deg);
  }
}

.tree-row-wrap :deep(.tree-row-actions) {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 0;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 120ms ease;
}

.tree-row-wrap :deep(.tree-action-btn) {
  appearance: none;
  -webkit-appearance: none;
  border: none;
  background: transparent;
  width: 26px;
  height: 26px;
  border-radius: var(--radius-sm);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 0;
  font-family: inherit;
  transition:
    background 120ms ease,
    color 120ms ease;

  .el-icon {
    font-size: 14px;
    color: inherit;
  }

  &:hover {
    background: var(--bg-soft);
    color: var(--text-primary);
  }

  &.tree-action-btn--danger:hover {
    background: color-mix(in srgb, var(--color-danger) 12%, transparent);
    color: var(--color-danger);
  }
}

.right-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  overflow: auto;
}

.upload-bar {
  position: sticky;
  top: 0;
  z-index: 2;
  background: var(--bg-page);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.upload-zone {
  width: 100%;
  :deep(.el-upload-dragger) {
    padding: var(--space-4);
    border-radius: var(--radius-md);
    border-style: dashed;
    border-color: var(--border-color);
    background: var(--bg-card);
  }
}

.up-icon { font-size: 32px; color: var(--color-primary); }

.up-text {
  margin-top: var(--space-1);
  font-size: var(--fs-sm);
  color: var(--text-secondary);
  em { color: var(--color-primary); font-style: normal; }
}

.up-error {
  margin: var(--space-1) 0 0;
  color: var(--color-danger);
  word-break: break-word;
}

.upload-tip {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
}

.upload-dialog-summary {
  margin: 0 0 var(--space-3);
}

.upload-pending-list {
  list-style: none;
  margin: 0 0 var(--space-4);
  padding: var(--space-2) var(--space-3);
  max-height: 140px;
  overflow-y: auto;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--bg-soft);

  li {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-1) 0;
    font-size: var(--fs-sm);
    min-width: 0;
  }

  .upload-pending-icon {
    flex-shrink: 0;
    color: var(--text-tertiary);
  }

  .upload-pending-name {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .upload-pending-size {
    flex-shrink: 0;
  }
}

.upload-dialog-form {
  margin-top: 0;
}

.upload-progress {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.up-item {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
}

.up-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-1);
  font-size: var(--fs-sm);

  .up-row-icon { color: var(--text-secondary); }
  .up-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.file-table {
  padding: 0;
  overflow-x: auto;
}

.ft-table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  border-spacing: 0;
}

.ft-head-row th.th-resizable {
  position: relative;
  padding-right: 12px !important;
}

.th-text {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.col-resize-grip {
  position: absolute;
  top: 0;
  right: -4px;
  width: 12px;
  height: 100%;
  cursor: col-resize;
  touch-action: none;
  z-index: 2;

  &::after {
    content: '';
    position: absolute;
    right: 5px;
    top: 18%;
    bottom: 18%;
    width: 2px;
    border-radius: 1px;
    background: var(--border-subtle);
    transition: background 0.12s ease;
    pointer-events: none;
  }

  &:hover::after,
  &:active::after {
    background: var(--color-primary);
  }
}

.ft-toolbar-row {
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-subtle);

  .ft-toolbar__cell {
    padding-top: var(--space-2);
    padding-bottom: var(--space-2);
  }

  .ft-toolbar__bar {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    min-width: 0;
  }

  .ft-toolbar__hint {
    flex: 1;
    min-width: 0;
    font-size: var(--fs-sm);
    color: var(--text-secondary);

    &.is-empty {
      color: var(--text-tertiary);
    }
  }

  .ft-toolbar__actions {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: var(--space-2);
    flex-shrink: 0;
    /* Align with the narrow action icon column below */
    min-width: 50px;
  }
}

.ft-batch-btn {
  appearance: none;
  -webkit-appearance: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 30px;
  padding: 0 var(--space-3);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: var(--fs-sm);
  font-weight: 500;
  font-family: inherit;
  white-space: nowrap;
  cursor: pointer;
  transition:
    background 120ms ease,
    color 120ms ease,
    border-color 120ms ease;

  .el-icon {
    font-size: 14px;
  }

  &:hover:not(:disabled) {
    color: var(--text-primary);
    border-color: var(--text-tertiary);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &--primary {
    color: var(--color-primary);
    border-color: color-mix(in srgb, var(--color-primary) 35%, var(--border-color));
    background: var(--color-primary-light);
  }

  &--danger {
    color: var(--color-danger);
    border-color: color-mix(in srgb, var(--color-danger) 35%, var(--border-color));

    &:hover:not(:disabled) {
      background: color-mix(in srgb, var(--color-danger) 8%, var(--bg-card));
    }
  }
}

.list-scope-hint {
  margin: 0;
}

.upload-folder-pick {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;

  .upload-folder-select {
    min-width: 200px;
    flex: 1;
    max-width: 320px;
  }
}

.panel-foot {
  padding: var(--space-2) var(--space-3);
  border-top: 1px solid var(--border-subtle);
  line-height: 1.4;
}

.col-tag {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  min-width: 0;

  .tag-label {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--text-secondary);
    font-size: var(--fs-sm);
  }
}

.ft-table th,
.ft-table td {
  padding: var(--space-3) var(--space-2);
  font-size: var(--fs-sm);
  text-align: left;
  vertical-align: middle;
}

.ft-table th:first-child,
.ft-table td:first-child {
  padding-left: var(--space-4);
}

.ft-table th:last-child,
.ft-table td:last-child {
  padding-right: var(--space-4);
}

.ft-row {
  cursor: pointer;
}

.col-check {
  width: 20px;
  text-align: center;
}

.file-table :deep(.file-check.el-checkbox) {
  --el-checkbox-input-width: 18px;
  --el-checkbox-input-height: 18px;
  height: auto;
  margin: 0;

  .el-checkbox__label {
    display: none;
  }

  .el-checkbox__inner {
    width: var(--el-checkbox-input-width);
    height: var(--el-checkbox-input-height);
    border-radius: var(--radius-sm);
    border: 1.5px solid var(--border-color);
    background: var(--bg-card);
    transition:
      border-color 120ms ease,
      background 120ms ease;
  }

  .el-checkbox__input.is-checked .el-checkbox__inner,
  .el-checkbox__input.is-indeterminate .el-checkbox__inner {
    background: var(--color-primary);
    border-color: var(--color-primary);
  }

  .el-checkbox__input.is-indeterminate .el-checkbox__inner::before {
    content: '';
    display: block;
    position: absolute;
    top: 50%;
    left: 50%;
    right: auto;
    width: 8px;
    height: 2px;
    background: #fff;
    border: none;
    border-radius: 1px;
    transform: translate(-50%, -50%) scale(1);
  }

  .el-checkbox__input.is-indeterminate .el-checkbox__inner::after {
    display: none;
  }

  .el-checkbox__input.is-checked .el-checkbox__inner::after {
    border-color: #fff;
    transform: translate(-45%, -60%) rotate(45deg) scaleY(1);
  }

  &:hover .el-checkbox__inner {
    border-color: var(--color-primary);
  }

  .el-checkbox__input.is-disabled .el-checkbox__inner {
    opacity: 0.45;
    cursor: not-allowed;
  }
}

.ft-head-row {
  background: var(--bg-soft);
  color: var(--text-secondary);
  font-weight: 600;
  border-bottom: 1px solid var(--border-color);

  th {
    font-weight: 600;
  }

  .col-actions {
    text-align: right;
  }
}

.ft-row {
  border-bottom: 1px solid var(--border-subtle);
  color: var(--text-primary);

  &:hover { background: var(--bg-soft); }
  &:last-child { border-bottom: none; }

  &.is-selected {
    background: var(--color-primary-light);
  }
}

.col-name__inner {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;

  .mime-icon { font-size: 18px; flex-shrink: 0; }
  .filename {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.col-size,
.col-user,
.col-time {
  color: var(--text-secondary);
  white-space: nowrap;
}

.col-actions {
  text-align: right;

  &__inner {
    display: flex;
    width: 100%;
    flex-wrap: nowrap;
    justify-content: flex-end;
    align-items: center;
    gap: 2px;
  }
}

.ft-icon-btn {
  appearance: none;
  -webkit-appearance: none;
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  padding: 0;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-tertiary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-family: inherit;
  transition:
    color 120ms ease,
    background 120ms ease;

  .el-icon {
    font-size: 16px;
  }

  &:hover:not(:disabled) {
    color: var(--color-primary);
    background: var(--bg-soft);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  &--danger {
    color: var(--color-danger);

    &:hover:not(:disabled) {
      color: var(--color-danger);
      background: color-mix(in srgb, var(--color-danger) 10%, transparent);
    }
  }
}

.batch-dialog-hint {
  margin: 0 0 var(--space-3);
  line-height: 1.5;
}

.ft-empty {
  padding: var(--space-10) var(--space-4);
  text-align: center;
  color: var(--text-tertiary);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);

  .el-icon { font-size: 28px; }
}

.mobile-picker {
  display: none;
}
.mobile-select { width: 100%; }

@media (max-width: 768px) {
  .files-layout {
    flex-direction: column;
    align-items: stretch;
  }

  .files-split {
    flex-direction: column;
    gap: 0;
  }

  .left-panel,
  .files-split__handle { display: none; }
  .mobile-picker {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    width: 100%;
  }

  .col-user,
  .col-time {
    display: none;
    padding: 0;
    border: none;
  }
}
</style>
