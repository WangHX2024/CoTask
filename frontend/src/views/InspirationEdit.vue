<template>
  <div class="edit-page insp-sub-page page">
    <header class="insp-page-header">
      <div class="insp-page-header__lead">
        <button
          type="button"
          class="insp-capsule-btn insp-back-btn"
          aria-label="返回灵感广场"
          @click="goBack"
        >
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </button>
        <div class="page-header-text">
          <h1 class="page-title">{{ isEdit ? '编辑灵感' : '发布灵感' }}</h1>
          <p class="page-desc">分享你的模板、案例、干货、话术、工具或网址给其他同学</p>
        </div>
      </div>
      <div class="insp-page-actions">
        <button type="button" class="insp-capsule-btn" @click="goBack">取消</button>
        <button
          v-if="!isEdit"
          type="button"
          class="insp-capsule-btn"
          :disabled="busy.publish"
          @click="onPublish(true)"
        >
          {{ busy.publish ? '提交中…' : '匿名发布' }}
        </button>
        <button
          type="button"
          class="insp-capsule-btn insp-capsule-btn--primary"
          :disabled="busy.publish"
          @click="isEdit ? onSave() : onPublish(false)"
        >
          {{ busy.publish ? '提交中…' : (isEdit ? '保存' : '发布') }}
        </button>
      </div>
    </header>

    <div class="insp-form-grid">
      <section class="insp-form-col">
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent
        >
          <div class="insp-panel">
            <el-form-item label="标题" prop="title">
              <el-input
                v-model="form.title"
                class="insp-capsule-input"
                placeholder="一句话总结你的灵感"
                maxlength="80"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="类别" prop="category">
              <SegmentedControl
                v-model="form.category"
                size="md"
                class="category-segment"
                :options="categoryOptions"
              />
            </el-form-item>

            <el-form-item
              v-if="form.category === 'tool' || form.category === 'link'"
              label="链接 URL"
              prop="link_url"
            >
              <el-input
                v-model="form.link_url"
                class="insp-capsule-input"
                placeholder="https://…"
                clearable
              />
            </el-form-item>

            <el-form-item label="课程名 (可选)">
              <el-input
                v-model="form.course_tag"
                class="insp-capsule-input"
                placeholder="手动填写，如：高等数学、软件工程导论"
                maxlength="64"
                clearable
              />
            </el-form-item>

            <el-form-item label="封面图 URL (可选)">
              <el-input
                v-model="form.cover_url"
                class="insp-capsule-input"
                placeholder="https://…"
                clearable
              />
              <div v-if="form.cover_url" class="cover-preview">
                <img :src="form.cover_url" alt="" @error="onCoverError" />
              </div>
            </el-form-item>

            <el-form-item
              v-if="form.category === 'template'"
              label="来源小组 (作为模板)"
            >
              <div class="template-source">
                <el-select
                  v-model="form.template_from_group_id"
                  class="insp-capsule-select"
                  popper-class="insp-select-popper"
                  placeholder="选择一个你管理的小组"
                  clearable
                  :disabled="!leaderGroups.length"
                  @change="onTemplateGroupChange"
                >
                  <el-option
                    v-for="g in leaderGroups"
                    :key="g.id"
                    :value="g.id"
                    :label="`[${g.course_name}] ${g.name}`"
                  />
                </el-select>
                <p v-if="!leaderGroups.length" class="muted tiny template-source__hint">
                  你目前不是任何小组的组长。
                </p>

                <div
                  v-else-if="form.template_from_group_id"
                  class="template-preview-inset"
                  v-loading="templatePreviewLoading"
                >
                  <div class="template-preview__bar">
                    <span class="template-preview__label">结构预览</span>
                    <span v-if="templatePreviewStats" class="template-preview__stats muted tiny">
                      {{ templatePreviewStats }}
                    </span>
                  </div>
                  <div v-if="templatePreviewNodes.length" class="template-preview__tree-wrap">
                    <TemplatePreviewTree :nodes="templatePreviewNodes" />
                  </div>
                  <p v-else-if="!templatePreviewLoading" class="muted tiny template-preview__empty">
                    该小组还没有任务节点
                  </p>
                </div>
              </div>
            </el-form-item>

            <div class="body-section">
              <div class="body-label-row">
                <span class="body-label-row__text">正文 (Markdown)</span>
                <SegmentedControl
                  v-model="editorMode"
                  size="sm"
                  :options="editorModeOptions"
                />
              </div>
              <el-form-item prop="body_md" class="body-form-item body-form-item--no-label">
                <div class="body-area">
                  <el-input
                    v-if="editorMode === 'edit'"
                    v-model="form.body_md"
                    class="insp-capsule-textarea"
                    type="textarea"
                    :rows="22"
                    placeholder="使用 Markdown 写下你的灵感… 支持标题、列表、代码块、链接、图片等"
                    resize="vertical"
                  />
                  <div v-else class="md-preview markdown-body" v-html="renderedPreview"></div>
                </div>
              </el-form-item>
            </div>
          </div>
        </el-form>
      </section>

      <aside class="insp-side-col">
        <div class="insp-panel tips-card">
          <div class="insp-side-title">写作小贴士</div>
          <ul class="tips">
            <li><b>标题</b> 简洁有力，控制在 80 字以内</li>
            <li><b>正文</b> 支持 Markdown：标题 #、列表 -、代码 ``、链接 [文字](url)</li>
            <li><b>模板</b> 类别会让其他组长可以一键导入到自己的项目</li>
            <li><b>课程名</b> 手动填写，方便同课程同学搜索到你的帖子</li>
            <li><b>匿名发布</b> 不显示你的头像与姓名</li>
          </ul>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { Api, type TaskNode } from '@/api'
import { useGroupsStore } from '@/stores/groups'
import SegmentedControl from '@/components/common/SegmentedControl.vue'
import TemplatePreviewTree from '@/components/inspiration/TemplatePreviewTree.vue'
import { previewTreeStats } from '@/components/inspiration/templatePreviewTree'

const route = useRoute()
const router = useRouter()
const groupsStore = useGroupsStore()

const editId = computed(() => {
  const v = route.params.id
  return v ? Number(v) : null
})
const isEdit = computed(() => editId.value != null)

const returnTo = computed(() => {
  const q = route.query.returnTo
  if (typeof q === 'string' && q.startsWith('/')) return q
  return null
})

const formRef = ref<FormInstance>()
const editorMode = ref<'edit' | 'preview'>('edit')

const form = reactive({
  title: '',
  category: 'tip' as 'template' | 'case' | 'tip' | 'script' | 'tool' | 'link',
  course_tag: '',
  cover_url: '',
  body_md: '',
  link_url: '',
  anon: false,
  template_from_group_id: null as number | null,
})

const rules = {
  title: [
    { required: true, message: '请输入标题', trigger: 'blur' },
    { min: 2, max: 80, message: '标题长度 2-80', trigger: 'blur' },
  ],
  category: [
    { required: true, message: '请选择类别', trigger: 'change' },
  ],
  link_url: [
    {
      validator: (_r: any, val: string, cb: any) => {
        if (form.category !== 'tool' && form.category !== 'link') return cb()
        if (!val) return cb(new Error('请填写链接 URL'))
        if (!/^https?:\/\//.test(val)) return cb(new Error('请填写有效的 http(s) 链接'))
        cb()
      },
      trigger: 'blur',
    },
  ],
  body_md: [
    {
      required: true,
      validator: (_r: any, val: string, cb: any) => {
        if (!val?.trim()) return cb(new Error('请输入正文'))
        cb()
      },
      trigger: 'blur',
    },
  ],
}

const busy = reactive({ publish: false })

const categoryOptions = [
  { label: '干货', value: 'tip' },
  { label: '模板', value: 'template' },
  { label: '案例', value: 'case' },
  { label: '话术', value: 'script' },
  { label: '工具', value: 'tool' },
  { label: '网址', value: 'link' },
]

const editorModeOptions = [
  { label: '编辑', value: 'edit' },
  { label: '预览', value: 'preview' },
]

const leaderGroups = computed(() =>
  groupsStore.list.filter((g) => g.role === 'leader'),
)

const templatePreviewLoading = ref(false)
const templatePreviewNodes = ref<TaskNode[]>([])

const templatePreviewStats = computed(() =>
  previewTreeStats(templatePreviewNodes.value),
)

async function loadTemplatePreview(groupId: number | null) {
  templatePreviewNodes.value = []
  if (!groupId) return
  templatePreviewLoading.value = true
  try {
    const tree = await Api.getTree(groupId)
    templatePreviewNodes.value = tree.nodes
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载模板预览失败')
  } finally {
    templatePreviewLoading.value = false
  }
}

function onTemplateGroupChange(gid: number | string | null | undefined) {
  const id = gid == null || gid === '' ? null : Number(gid)
  void loadTemplatePreview(Number.isFinite(id) ? id : null)
}

watch(
  () => form.category,
  (cat) => {
    if (cat !== 'template') {
      form.template_from_group_id = null
      templatePreviewNodes.value = []
    } else if (form.template_from_group_id) {
      void loadTemplatePreview(form.template_from_group_id)
    }
  },
)

marked.setOptions({ gfm: true, breaks: true })
const renderedPreview = computed(() => {
  if (!form.body_md) return '<p class="muted">还没有内容…</p>'
  const raw = marked.parse(form.body_md) as string
  return DOMPurify.sanitize(raw, { ADD_ATTR: ['target', 'rel'] })
})

function onCoverError() {
  ElMessage.warning('封面图加载失败，请检查链接')
}

function buildCreatePayload() {
  const data: Record<string, unknown> = {
    title: form.title.trim(),
    category: form.category,
    body_md: form.body_md.trim(),
    anon: form.anon,
  }
  if (form.course_tag.trim()) data.course_tag = form.course_tag.trim()
  if (form.cover_url.trim()) data.cover_url = form.cover_url.trim()
  if (form.link_url.trim()) data.link_url = form.link_url.trim()
  if (form.category === 'template' && form.template_from_group_id) {
    data.template_from_group_id = form.template_from_group_id
  }
  return data
}

function buildUpdatePayload() {
  const data: Record<string, unknown> = {
    title: form.title.trim(),
    category: form.category,
    body_md: form.body_md.trim(),
    anon: form.anon,
  }
  const course = form.course_tag.trim()
  data.course_tag = course || null
  const cover = form.cover_url.trim()
  data.cover_url = cover || null
  const link = form.link_url.trim()
  data.link_url = link || null
  return data
}

async function onSave() {
  if (!formRef.value || !editId.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  busy.publish = true
  try {
    const res = await Api.updatePost(editId.value, buildUpdatePayload())
    ElMessage.success('已保存')
    router.back()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
  } finally {
    busy.publish = false
  }
}

async function onPublish(asAnon: boolean) {
  form.anon = asAnon
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  busy.publish = true
  try {
    const res = await Api.createPost(buildCreatePayload())
    ElMessage.success(asAnon ? '已匿名发布' : '已发布')
    router.replace(`/inspiration/p/${res.id}`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '提交失败')
  } finally {
    busy.publish = false
  }
}

async function goBack() {
  if (form.title || form.body_md) {
    try {
      await ElMessageBox.confirm('内容尚未保存，确定要离开吗？', '提示', {
        type: 'warning',
        confirmButtonText: '离开',
        cancelButtonText: '继续编辑',
      })
    } catch {
      return
    }
  }
  if (returnTo.value) {
    router.replace(returnTo.value)
  } else if (window.history.length > 1) {
    router.back()
  } else {
    router.replace('/inspiration')
  }
}

async function loadForEdit() {
  if (!editId.value) return
  try {
    const p = await Api.post(editId.value)
    form.title = p.title
    form.category = (p.category as any) || 'tip'
    form.course_tag = p.course_tag || ''
    form.cover_url = p.cover_url || ''
    form.body_md = p.body_md || ''
    form.link_url = p.link_url || ''
    form.anon = p.anon
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载帖子失败')
  }
}

onMounted(async () => {
  if (!groupsStore.loaded) await groupsStore.refresh().catch(() => {})
  if (isEdit.value) await loadForEdit()
  if (form.category === 'template' && form.template_from_group_id) {
    await loadTemplatePreview(form.template_from_group_id)
  }
})
</script>

<style lang="scss">
@use '@/styles/inspiration-pages.scss';
</style>

<style lang="scss" scoped>
.category-segment {
  width: fit-content;
  max-width: 100%;
  overflow-x: auto;
}

.body-section {
  margin-top: var(--space-6);
  padding-top: var(--space-6);
  border-top: 1px solid var(--border-subtle);
}

.body-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  min-height: 32px;
  padding-bottom: var(--space-2);
  font-size: var(--el-form-label-font-size, var(--fs-base));
  line-height: 32px;
}

.body-label-row__text {
  font-weight: 600;
  color: var(--text-primary);

  &::before {
    content: '*';
    color: var(--el-color-danger);
    margin-right: 4px;
  }
}

.body-form-item {
  margin-bottom: 0;

  :deep(.el-form-item__content) {
    width: 100%;
    max-width: 100%;
  }

  &--no-label :deep(.el-form-item__label-wrap) {
    display: none;
  }
}

.body-area {
  width: 100%;
  min-height: 480px;

  :deep(.el-textarea),
  :deep(.insp-capsule-textarea) {
    width: 100%;
    display: block;
  }

  :deep(.el-textarea__inner) {
    width: 100%;
    box-sizing: border-box;
  }
}

.md-preview {
  min-height: 480px;
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: none;
  background: var(--bg-soft);
}

.markdown-body {
  line-height: 1.7;
  font-size: var(--fs-base);
  color: var(--text-primary);

  :deep(h1), :deep(h2), :deep(h3) {
    margin: 1em 0 0.4em;
    color: var(--text-primary);
    font-weight: 700;
  }
  :deep(h1) { font-size: var(--fs-xl); }
  :deep(h2) { font-size: var(--fs-lg); }
  :deep(h3) { font-size: var(--fs-md); }
  :deep(p)  { margin: 0.6em 0; }
  :deep(a)  { color: var(--color-primary); }
  :deep(ul), :deep(ol) { padding-left: 1.4em; }
  :deep(code) {
    background: var(--bg-card);
    padding: 1px var(--space-1);
    border-radius: var(--radius-sm);
    font-size: var(--fs-sm);
    color: var(--color-danger);
  }
  :deep(pre) {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    padding: var(--space-3);
    border-radius: var(--radius-md);
    overflow-x: auto;
  }
  :deep(blockquote) {
    border-left: 3px solid var(--color-primary);
    padding-left: var(--space-3);
    color: var(--text-secondary);
    margin: 0.8em 0;
  }
  :deep(img) { max-width: 100%; border-radius: var(--radius-md); }
}

.cover-preview {
  margin-top: var(--space-2);
  border-radius: var(--radius-lg);
  overflow: hidden;
  max-width: 280px;
  background: var(--bg-soft);
  img { width: 100%; display: block; max-height: 160px; object-fit: cover; }
}

.template-source {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.template-source__hint {
  margin: var(--space-2) 0 0;
}

.template-preview-inset {
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--border-subtle);
  min-height: 48px;
}

.template-preview__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.template-preview__label {
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--text-secondary);
}

.template-preview__stats {
  flex-shrink: 0;
  white-space: nowrap;
}

.template-preview__tree-wrap {
  max-height: 260px;
  overflow-y: auto;
  padding: var(--space-1) 0;
}

.template-preview__empty {
  margin: 0;
}

.tips {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);

  li {
    font-size: var(--fs-sm);
    color: var(--text-secondary);
    line-height: 1.5;
    padding-left: var(--space-4);
    position: relative;

    &::before {
      content: '•';
      position: absolute;
      left: var(--space-1);
      color: var(--color-primary);
      font-weight: 700;
    }

    b { color: var(--text-primary); font-weight: 600; }
  }
}
</style>
