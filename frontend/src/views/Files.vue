<template>
  <div class="files-page">
    <!-- Header -->
    <div class="page-head">
      <div class="head-left">
        <el-icon class="head-icon"><FolderOpened /></el-icon>
        <h2 class="head-title">
          文件库
          <span class="muted dot-sep">·</span>
          <span class="group-name">{{ groups.current?.name || '小组' }}</span>
        </h2>
      </div>
      <div class="head-right">
        <el-radio-group v-model="viewMode" size="default">
          <el-radio-button label="task">按任务</el-radio-button>
          <el-radio-button label="folder">按文件夹</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div class="files-layout">
      <!-- Mobile dropdown selector -->
      <div class="mobile-picker">
        <el-select
          v-if="viewMode === 'task'"
          v-model="selectedTaskId"
          placeholder="选择任务"
          @change="loadFiles"
          filterable
          clearable
          class="mobile-select"
        >
          <el-option
            v-for="t in leafTasks"
            :key="t.id"
            :label="t.title"
            :value="t.id"
          />
        </el-select>
        <el-select
          v-else
          v-model="selectedFolderId"
          placeholder="选择文件夹"
          @change="loadFiles"
          clearable
          class="mobile-select"
        >
          <el-option label="(根目录)" :value="0" />
          <el-option
            v-for="f in folders"
            :key="f.id"
            :label="folderLabel(f)"
            :value="f.id"
          />
        </el-select>
      </div>

      <!-- LEFT panel -->
      <aside class="left-panel">
        <!-- Task list -->
        <template v-if="viewMode === 'task'">
          <div class="panel-head">
            <span>任务列表</span>
            <span class="tiny muted">{{ leafTasks.length }} 个</span>
          </div>
          <div v-loading="treeLoading" class="panel-body">
            <div
              v-for="t in leafTasks"
              :key="t.id"
              class="list-item"
              :class="{ active: selectedTaskId === t.id }"
              @click="onPickTask(t.id)"
            >
              <el-icon class="li-icon"><Memo /></el-icon>
              <span class="li-text">{{ t.title }}</span>
            </div>
            <div v-if="!treeLoading && leafTasks.length === 0" class="empty-tip">
              暂无任务
            </div>
          </div>
        </template>

        <!-- Folder tree -->
        <template v-else>
          <div class="panel-head">
            <span>文件夹</span>
            <el-button
              v-if="isLeader"
              text
              size="small"
              @click="openNewFolderDialog(null)"
              title="新建根文件夹"
            >
              <el-icon><Plus /></el-icon>
            </el-button>
          </div>
          <div v-loading="folderLoading" class="panel-body">
            <div
              class="list-item"
              :class="{ active: selectedFolderId === 0 }"
              @click="onPickFolder(0)"
            >
              <el-icon class="li-icon"><FolderOpened /></el-icon>
              <span class="li-text">(根目录)</span>
            </div>
            <FolderRow
              v-for="node in folderTree"
              :key="node.id"
              :node="node"
              :selected-id="selectedFolderId"
              :is-leader="isLeader"
              @pick="onPickFolder"
              @add-child="openNewFolderDialog"
            />
            <div v-if="!folderLoading && folders.length === 0" class="empty-tip">
              暂无文件夹
            </div>
          </div>
        </template>
      </aside>

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
            :disabled="!canUpload"
          >
            <el-icon class="up-icon"><UploadFilled /></el-icon>
            <div class="up-text">
              拖拽文件到此处，或<em>点击选择</em>
            </div>
            <template #tip>
              <div class="tiny muted">
                {{ uploadTarget }}
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
              <el-progress
                :percentage="item.percent"
                :status="item.status === 'error' ? 'exception' : item.status === 'done' ? 'success' : undefined"
                :stroke-width="6"
                :show-text="false"
              />
            </div>
          </div>
        </div>

        <!-- File list -->
        <div class="file-table card" v-loading="fileLoading">
          <div class="ft-head">
            <span class="col-name">文件名</span>
            <span class="col-size">大小</span>
            <span class="col-user">上传者</span>
            <span class="col-time">上传时间</span>
            <span class="col-actions">操作</span>
          </div>
          <div v-if="!files.length && !fileLoading" class="ft-empty">
            <el-icon><FolderOpened /></el-icon>
            <span>暂无文件</span>
          </div>
          <div
            v-for="f in files"
            :key="f.id"
            class="ft-row"
          >
            <span class="col-name">
              <el-icon class="mime-icon" :style="{ color: mimeColor(f.mime) }">
                <component :is="mimeIcon(f.mime)" />
              </el-icon>
              <span class="filename" :title="f.filename">{{ f.filename }}</span>
            </span>
            <span class="col-size">{{ humanSize(f.size) }}</span>
            <span class="col-user">{{ f.uploader_name || '—' }}</span>
            <span class="col-time">{{ relativeTime(f.created_at) }}</span>
            <span class="col-actions">
              <el-button text size="small" @click="onDownload(f)">
                <el-icon><Download /></el-icon>&nbsp;下载
              </el-button>
              <el-popconfirm
                v-if="canDelete(f)"
                title="确定删除该文件？"
                @confirm="onDelete(f)"
              >
                <template #reference>
                  <el-button text size="small" type="danger">
                    <el-icon><Delete /></el-icon>&nbsp;删除
                  </el-button>
                </template>
              </el-popconfirm>
            </span>
          </div>
        </div>
      </section>
    </div>

    <!-- New folder dialog -->
    <el-dialog v-model="folderDialogOpen" title="新建文件夹" width="420px">
      <el-form @submit.prevent>
        <el-form-item label="名称">
          <el-input v-model="folderForm.name" maxlength="60" placeholder="请输入文件夹名" />
        </el-form-item>
        <el-form-item v-if="folderForm.parent_id" label="父文件夹">
          <span class="muted">{{ folderName(folderForm.parent_id) || '—' }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="folderDialogOpen = false">取消</el-button>
        <el-button type="primary" :loading="creatingFolder" @click="onCreateFolder">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  FolderOpened, Plus, Memo, UploadFilled, Document, Picture, VideoPlay,
  Headset, Tickets, Files as FilesIcon, Download, Delete,
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { Api, type FileInfo, type FolderInfo, type TaskNode } from '@/api'
import { useGroupsStore } from '@/stores/groups'
import { useAuthStore } from '@/stores/auth'

// ---------- folder row component (inline definition) ----------
const FolderRow = {
  name: 'FolderRow',
  props: {
    node: { type: Object, required: true },
    selectedId: { type: Number, default: 0 },
    isLeader: { type: Boolean, default: false },
    depth: { type: Number, default: 0 },
  },
  emits: ['pick', 'add-child'],
  setup(props: any, { emit }: any) {
    const expanded = ref(true)
    return () => {
      const hasChildren = props.node.children?.length > 0
      const rowClass = ['list-item']
      if (props.selectedId === props.node.id) rowClass.push('active')
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
      return h('div', { class: 'folder-row-wrap' }, [
        h('div',
          {
            class: rowClass.join(' '),
            style: { paddingLeft: `${8 + props.depth * 14}px` },
            onClick: handle,
          },
          [
            hasChildren
              ? h('span', { class: 'tw-caret', onClick: toggle }, expanded.value ? '▾' : '▸')
              : h('span', { class: 'tw-caret tw-empty' }, ''),
            h('span', { class: 'li-icon-wrap' }, '📁'),
            h('span', { class: 'li-text' }, props.node.name),
            props.isLeader
              ? h(
                  'span',
                  {
                    class: 'tw-add',
                    onClick: addChild,
                    title: '新建子文件夹',
                  },
                  '+',
                )
              : null,
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
                  isLeader: props.isLeader,
                  depth: props.depth + 1,
                  onPick: (id: number) => emit('pick', id),
                  'onAdd-child': (id: number) => emit('add-child', id),
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
const auth = useAuthStore()

const gid = computed(() => Number(route.params.gid))
const isLeader = computed(() => groups.currentRole === 'leader')

// ---------- state ----------
const viewMode = ref<'task' | 'folder'>('task')

const treeLoading = ref(false)
const folderLoading = ref(false)
const fileLoading = ref(false)

const tasks = ref<TaskNode[]>([])
const folders = ref<FolderInfo[]>([])
const files = ref<FileInfo[]>([])

const selectedTaskId = ref<number | null>(null)
const selectedFolderId = ref<number>(0) // 0 means root / unselected

// upload progress
interface UpItem {
  name: string
  size: number
  percent: number
  status: 'pending' | 'uploading' | 'finalizing' | 'done' | 'error'
}
const uploadingItems = ref<UpItem[]>([])
const uploadRef = ref<any>(null)

// new folder dialog
const folderDialogOpen = ref(false)
const folderForm = reactive<{ name: string; parent_id: number | null }>({
  name: '',
  parent_id: null,
})
const creatingFolder = ref(false)

// ---------- derived ----------
const leafTasks = computed(() =>
  tasks.value.filter((t) => t.is_leaf).sort((a, b) => a.position - b.position),
)

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

const canUpload = computed(() => {
  if (viewMode.value === 'task') return !!selectedTaskId.value
  return true
})

const uploadTarget = computed(() => {
  if (viewMode.value === 'task') {
    if (!selectedTaskId.value) return '请先选择一个任务'
    const t = tasks.value.find((x) => x.id === selectedTaskId.value)
    return `当前目标：任务「${t?.title || ''}」`
  }
  if (selectedFolderId.value) {
    return `当前目标：文件夹「${folderName(selectedFolderId.value)}」`
  }
  return '当前目标：根目录'
})

// ---------- load ----------
async function loadTree() {
  if (!gid.value) return
  treeLoading.value = true
  try {
    const tree = await Api.getTree(gid.value)
    tasks.value = tree.nodes
    if (!selectedTaskId.value && leafTasks.value.length) {
      selectedTaskId.value = leafTasks.value[0].id
      void loadFiles()
    }
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
    const params: any = {}
    if (viewMode.value === 'task') {
      if (!selectedTaskId.value) {
        files.value = []
        fileLoading.value = false
        return
      }
      params.task_id = selectedTaskId.value
    } else {
      if (selectedFolderId.value) params.folder_id = selectedFolderId.value
    }
    files.value = await Api.listFiles(gid.value, params)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载文件失败')
  } finally {
    fileLoading.value = false
  }
}

// ---------- pickers ----------
function onPickTask(id: number) {
  selectedTaskId.value = id
  void loadFiles()
}
function onPickFolder(id: number) {
  selectedFolderId.value = id
  void loadFiles()
}

watch(viewMode, () => {
  if (viewMode.value === 'task' && !selectedTaskId.value && leafTasks.value.length) {
    selectedTaskId.value = leafTasks.value[0].id
  }
  void loadFiles()
})

// ---------- folder ops ----------
function openNewFolderDialog(parentId: number | null) {
  if (!isLeader.value) {
    ElMessage.warning('只有组长可创建文件夹')
    return
  }
  folderForm.name = ''
  folderForm.parent_id = parentId
  folderDialogOpen.value = true
}
async function onCreateFolder() {
  const name = folderForm.name.trim()
  if (!name) {
    ElMessage.warning('请输入文件夹名')
    return
  }
  creatingFolder.value = true
  try {
    await Api.createFolder(gid.value, {
      name,
      parent_id: folderForm.parent_id || undefined,
    })
    folderDialogOpen.value = false
    ElMessage.success('文件夹已创建')
    await loadFolders()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '创建失败')
  } finally {
    creatingFolder.value = false
  }
}

// ---------- upload ----------
async function onFilePicked(file: any) {
  // el-upload `:on-change` fires once per selected file
  const raw: File = file.raw
  if (!raw) return
  if (!canUpload.value) {
    ElMessage.warning('请先选择一个任务')
    if (uploadRef.value) uploadRef.value.clearFiles?.()
    return
  }
  const item: UpItem = {
    name: raw.name,
    size: raw.size,
    percent: 0,
    status: 'pending',
  }
  uploadingItems.value.push(item)
  try {
    await uploadOne(raw, item)
  } catch (e: any) {
    item.status = 'error'
    ElMessage.error(`${raw.name}：${e?.message || '上传失败'}`)
  }
  if (uploadRef.value) uploadRef.value.clearFiles?.()
}

async function uploadOne(raw: File, item: UpItem) {
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
  if (viewMode.value === 'task' && selectedTaskId.value) {
    signParams.task_id = selectedTaskId.value
  } else if (viewMode.value === 'folder' && selectedFolderId.value) {
    signParams.folder_id = selectedFolderId.value
  }

  const signResp: any = await Api.signUpload(signParams)
  const fileId: number = signResp.file_id ?? signResp.id

  // 3. dedup
  if (signResp.deduped) {
    item.percent = 100
    item.status = 'finalizing'
    await Api.finalizeFile(fileId)
    item.status = 'done'
    ElMessage.success(`${raw.name}：秒传成功`)
    await loadFiles()
    return
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
  ElMessage.success(`${raw.name}：上传完成`)
  await loadFiles()
}

function putWithProgress(
  url: string,
  raw: File,
  onProgress: (p: number) => void,
) {
  return new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('PUT', url)
    if (raw.type) xhr.setRequestHeader('Content-Type', raw.type)
    xhr.upload.onprogress = (ev: ProgressEvent) => {
      if (ev.lengthComputable) onProgress(ev.loaded / ev.total)
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve()
      else reject(new Error(`HTTP ${xhr.status}`))
    }
    xhr.onerror = () => reject(new Error('网络错误'))
    xhr.send(raw)
  })
}

async function computeHash(file: File): Promise<string> {
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
    // fallback: pseudo hash (must fit files.md5 column, 64 chars max)
    return `${file.name}-${file.size}-${file.lastModified}`.slice(0, 64)
  }
}

// ---------- file actions ----------
function onDownload(f: FileInfo) {
  if (!f.download_url) {
    ElMessage.warning('下载链接不可用')
    return
  }
  window.open(f.download_url, '_blank', 'noopener')
}
function canDelete(f: FileInfo): boolean {
  return isLeader.value || f.uploader_id === auth.user?.id
}
async function onDelete(f: FileInfo) {
  try {
    await Api.deleteFile(f.id)
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
function relativeTime(iso: string): string {
  const t = dayjs(iso)
  const now = dayjs()
  const diffSec = now.diff(t, 'second')
  if (diffSec < 60) return '刚刚'
  const diffMin = now.diff(t, 'minute')
  if (diffMin < 60) return `${diffMin} 分钟前`
  const diffHr = now.diff(t, 'hour')
  if (diffHr < 24) return `${diffHr} 小时前`
  const diffDay = now.diff(t, 'day')
  if (diffDay === 1) return '昨天'
  if (diffDay < 7) return `${diffDay} 天前`
  return t.format('YYYY-MM-DD HH:mm')
}
function statusLabel(s: string): string {
  return ({
    pending: '准备中',
    uploading: '上传中',
    finalizing: '完成中',
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
  return folders.value.find((x) => x.id === id)?.name || ''
}
function folderLabel(f: FolderInfo): string {
  if (!f.path) return f.name
  return f.path
}

// ---------- mount ----------
onMounted(async () => {
  await Promise.all([loadTree(), loadFolders()])
  void loadFiles()
})

// react to gid change (group switch)
watch(gid, async () => {
  selectedTaskId.value = null
  selectedFolderId.value = 0
  files.value = []
  await Promise.all([loadTree(), loadFolders()])
  void loadFiles()
})
</script>

<style lang="scss" scoped>
.files-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}

.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;

  .head-left { display: flex; align-items: center; gap: 10px; }
  .head-icon { font-size: 22px; color: var(--color-primary); }
  .head-title {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: var(--text-primary);
  }
  .dot-sep { margin: 0 6px; color: var(--text-tertiary); }
  .group-name { color: var(--text-secondary); font-weight: 500; }
}

.files-layout {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

.left-panel {
  width: 240px;
  flex-shrink: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.panel-head {
  height: 40px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  font-weight: 600;
  color: var(--text-primary);
  font-size: 13px;
}
.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 6px;
}

.list-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--text-primary);
  font-size: 13px;
  &:hover { background: var(--bg-soft); }
  &.active {
    background: rgba(61,126,255,.10);
    color: var(--color-primary);
  }
  .li-icon { font-size: 14px; color: var(--text-secondary); }
  .li-text {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
.empty-tip {
  padding: 16px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 12px;
}

.folder-row-wrap :deep(.tw-caret) {
  width: 14px;
  text-align: center;
  font-size: 10px;
  color: var(--text-tertiary);
  user-select: none;
}
.folder-row-wrap :deep(.tw-caret.tw-empty) { visibility: hidden; }
.folder-row-wrap :deep(.tw-add) {
  margin-left: auto;
  width: 18px;
  height: 18px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  &:hover { background: var(--bg-card); color: var(--color-primary); }
}
.folder-row-wrap :deep(.li-icon-wrap) {
  display: inline-flex;
  font-size: 14px;
}

.right-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: auto;
}

.upload-bar {
  position: sticky;
  top: 0;
  z-index: 2;
  background: var(--bg-page);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.upload-zone {
  width: 100%;
  :deep(.el-upload-dragger) {
    padding: 18px;
    border-radius: var(--radius-md);
    border-style: dashed;
    border-color: var(--border-color);
    background: var(--bg-card);
  }
}
.up-icon { font-size: 32px; color: var(--color-primary); }
.up-text {
  margin-top: 4px;
  font-size: 13px;
  color: var(--text-secondary);
  em { color: var(--color-primary); font-style: normal; }
}

.upload-progress {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.up-item {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 6px 10px;
}
.up-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 13px;
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
  overflow: hidden;
}
.ft-head, .ft-row {
  display: grid;
  grid-template-columns: minmax(180px, 1.8fr) 100px 130px 150px 160px;
  align-items: center;
  padding: 10px 14px;
  gap: 8px;
  font-size: 13px;
}
.ft-head {
  background: var(--bg-soft);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  border-bottom: 1px solid var(--border-color);
}
.ft-row {
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
  &:hover {
    background: var(--bg-soft);
  }
  &:last-child { border-bottom: none; }
}
.col-name {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  .mime-icon { font-size: 18px; flex-shrink: 0; }
  .filename {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
.col-size, .col-user, .col-time {
  color: var(--text-secondary);
}
.col-actions {
  display: flex;
  gap: 4px;
  justify-content: flex-end;
}
.ft-empty {
  padding: 40px 16px;
  text-align: center;
  color: var(--text-tertiary);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  .el-icon { font-size: 28px; }
}

.mobile-picker {
  display: none;
}
.mobile-select { width: 100%; }

@media (max-width: 768px) {
  .files-layout { flex-direction: column; }
  .left-panel { display: none; }
  .mobile-picker { display: block; }
  .ft-head, .ft-row {
    grid-template-columns: minmax(120px, 1fr) 80px 100px;
  }
  .col-time, .col-user { display: none; }
}
</style>
