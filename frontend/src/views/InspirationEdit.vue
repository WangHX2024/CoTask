<template>
  <div class="edit-page">
    <header class="edit-head card">
      <div>
        <h1 class="title">{{ isEdit ? '编辑灵感' : '发布灵感' }}</h1>
        <p class="muted tiny">分享你的模板、案例、干货、话术、工具或网址给其他同学</p>
      </div>
      <div class="head-actions">
        <el-button @click="onCancel">取消</el-button>
        <el-button @click="onSaveDraft" :loading="busy.draft">保存草稿</el-button>
        <el-button type="primary" :loading="busy.publish" @click="onPublish">
          {{ isEdit ? '保存' : '发布' }}
        </el-button>
      </div>
    </header>

    <div class="form-grid">
      <!-- Form column -->
      <section class="form-col">
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent
        >
          <div class="card form-card">
            <el-form-item label="标题" prop="title">
              <el-input
                v-model="form.title"
                placeholder="一句话总结你的灵感"
                maxlength="80"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="类别" prop="category">
              <el-radio-group v-model="form.category">
                <el-radio
                  v-for="c in categoryOptions"
                  :key="c.value"
                  :value="c.value"
                  :label="c.value"
                >
                  {{ c.label }}
                </el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item
              v-if="form.category === 'tool' || form.category === 'link'"
              label="链接 URL"
              prop="link_url"
            >
              <el-input
                v-model="form.link_url"
                placeholder="https://…"
                clearable
              />
            </el-form-item>

            <el-form-item label="课程标签">
              <el-autocomplete
                v-model="form.course_tag"
                :fetch-suggestions="queryCourseTag"
                placeholder="比如：高数 / 软工导论"
                clearable
                style="width: 100%;"
              />
            </el-form-item>

            <el-form-item label="封面图 URL (可选)">
              <el-input
                v-model="form.cover_url"
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
              <el-select
                v-model="form.template_from_group_id"
                placeholder="选择一个你管理的小组"
                clearable
                style="width: 100%;"
                :disabled="!leaderGroups.length"
              >
                <el-option
                  v-for="g in leaderGroups"
                  :key="g.id"
                  :value="g.id"
                  :label="`[${g.course_name}] ${g.name}`"
                />
              </el-select>
              <div v-if="!leaderGroups.length" class="muted tiny mt-4">
                你目前不是任何小组的组长。
              </div>
            </el-form-item>

            <el-form-item>
              <el-switch v-model="form.anon" active-text="匿名发布" />
            </el-form-item>
          </div>

          <div class="card body-card">
            <div class="body-head">
              <label class="lbl">正文 (Markdown)</label>
              <el-switch
                v-model="preview"
                active-text="预览"
                inline-prompt
              />
            </div>

            <div class="body-area">
              <el-input
                v-if="!preview"
                v-model="form.body_md"
                type="textarea"
                :rows="22"
                placeholder="使用 Markdown 写下你的灵感… 支持标题、列表、代码块、链接、图片等"
                resize="vertical"
              />
              <div v-else class="md-preview markdown-body" v-html="renderedPreview"></div>
            </div>
          </div>
        </el-form>
      </section>

      <!-- Tips column -->
      <aside class="tips-col">
        <div class="card tips-card">
          <div class="side-title">写作小贴士</div>
          <ul class="tips">
            <li><b>标题</b> 简洁有力，控制在 80 字以内</li>
            <li><b>正文</b> 支持 Markdown：标题 #、列表 -、代码 ``、链接 [文字](url)</li>
            <li><b>模板</b> 类别会让其他组长可以一键导入到自己的项目</li>
            <li><b>课程标签</b> 让同课程的同学更容易发现你</li>
            <li><b>匿名发布</b> 不显示你的头像与姓名</li>
          </ul>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { Api } from '@/api'
import { useGroupsStore } from '@/stores/groups'

const route = useRoute()
const router = useRouter()
const groupsStore = useGroupsStore()

const editId = computed(() => {
  const v = route.params.id
  return v ? Number(v) : null
})
const isEdit = computed(() => editId.value != null)

const formRef = ref<FormInstance>()
const preview = ref(false)

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
}

const busy = reactive({ publish: false, draft: false })

const categoryOptions = [
  { label: '干货', value: 'tip' },
  { label: '模板', value: 'template' },
  { label: '案例', value: 'case' },
  { label: '话术', value: 'script' },
  { label: '工具', value: 'tool' },
  { label: '网址', value: 'link' },
]

const leaderGroups = computed(() =>
  groupsStore.list.filter((g) => g.role === 'leader'),
)

const commonCourseTags = [
  '高等数学', '线性代数', '概率论', '软件工程',
  '数据结构', '操作系统', '计算机网络', '人工智能',
  '产品设计', '市场营销', '英语口语', '微观经济学',
]
function queryCourseTag(query: string, cb: (arr: any[]) => void) {
  const q = (query || '').toLowerCase()
  const list = commonCourseTags
    .filter((t) => !q || t.toLowerCase().includes(q))
    .map((value) => ({ value }))
  cb(list)
}

marked.setOptions({ gfm: true, breaks: true })
const renderedPreview = computed(() => {
  if (!form.body_md) return '<p class="muted">还没有内容…</p>'
  const raw = marked.parse(form.body_md) as string
  return DOMPurify.sanitize(raw, { ADD_ATTR: ['target', 'rel'] })
})

function onCoverError() {
  ElMessage.warning('封面图加载失败，请检查链接')
}

function buildPayload() {
  const data: any = {
    title: form.title.trim(),
    category: form.category,
    body_md: form.body_md,
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

async function onPublish() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  busy.publish = true
  try {
    const data = buildPayload()
    let id: number
    if (isEdit.value && editId.value) {
      const res = await Api.updatePost(editId.value, data)
      id = res.id
      ElMessage.success('已保存')
    } else {
      const res = await Api.createPost(data)
      id = res.id
      ElMessage.success('已发布')
    }
    router.replace(`/inspiration/p/${id}`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '提交失败')
  } finally {
    busy.publish = false
  }
}

function onSaveDraft() {
  // For now, draft is the same as publish (no draft endpoint in v1.0).
  void onPublish()
}

async function onCancel() {
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
  if (isEdit.value && editId.value) {
    router.push(`/inspiration/p/${editId.value}`)
  } else {
    router.push('/inspiration')
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
})
</script>

<style lang="scss" scoped>
.edit-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.edit-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  gap: 12px;
  flex-wrap: wrap;

  .title {
    margin: 0;
    font-size: 20px;
    font-weight: 700;
    color: var(--text-primary);
  }
}
.head-actions { display: flex; gap: 8px; }

.form-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 16px;
  align-items: start;
}

.form-col { display: flex; flex-direction: column; gap: 16px; }
.form-card, .body-card { padding: 20px 24px; }

.body-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.lbl {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.body-area {
  min-height: 480px;
}

.md-preview {
  min-height: 480px;
  padding: 12px 16px;
  border: 1px dashed var(--border-color);
  border-radius: 8px;
  background: var(--bg-soft);
}

.markdown-body {
  line-height: 1.7;
  font-size: 14px;
  color: var(--text-primary);

  :deep(h1), :deep(h2), :deep(h3) {
    margin: 1em 0 0.4em;
    color: var(--text-primary);
    font-weight: 700;
  }
  :deep(h1) { font-size: 20px; }
  :deep(h2) { font-size: 17px; }
  :deep(h3) { font-size: 15px; }
  :deep(p)  { margin: 0.6em 0; }
  :deep(a)  { color: var(--color-primary); }
  :deep(ul), :deep(ol) { padding-left: 1.4em; }
  :deep(code) {
    background: var(--bg-card);
    padding: 1px 5px;
    border-radius: 4px;
    font-size: 12px;
    color: var(--color-danger);
  }
  :deep(pre) {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
  }
  :deep(blockquote) {
    border-left: 3px solid var(--color-primary);
    padding-left: 10px;
    color: var(--text-secondary);
    margin: 0.8em 0;
  }
  :deep(img) { max-width: 100%; border-radius: 6px; }
}

.cover-preview {
  margin-top: 8px;
  border-radius: 6px;
  overflow: hidden;
  max-width: 280px;
  background: var(--bg-soft);
  img { width: 100%; display: block; max-height: 160px; object-fit: cover; }
}

.tips-col {
  position: sticky;
  top: 0;
}
.tips-card { padding: 16px 18px; }
.side-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 10px;
}
.tips {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  li {
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.5;
    padding-left: 16px;
    position: relative;
    &::before {
      content: '•';
      position: absolute;
      left: 4px;
      color: var(--color-primary);
      font-weight: 700;
    }
    b { color: var(--text-primary); font-weight: 600; }
  }
}

.mt-4 { margin-top: 4px; }

@media (max-width: 992px) {
  .form-grid { grid-template-columns: 1fr; }
  .tips-col { position: static; }
}
@media (max-width: 768px) {
  .edit-head { flex-direction: column; align-items: stretch; }
  .head-actions { justify-content: flex-end; }
  .form-card, .body-card { padding: 14px; }
}
</style>
