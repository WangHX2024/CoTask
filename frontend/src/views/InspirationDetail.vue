<template>
  <div class="detail-page">
    <template v-if="loading && !post">
      <div class="card detail-skel">
        <el-skeleton animated :rows="10" />
      </div>
    </template>

    <template v-else-if="post">
      <!-- Header -->
      <header class="detail-head">
        <div class="head-meta">
          <span class="cat-tag" :class="`cat-${post.category}`">{{ categoryLabel(post.category) }}</span>
          <span v-if="post.course_tag" class="course-tag">#{{ post.course_tag }}</span>
        </div>
        <h1 class="detail-title">{{ post.title }}</h1>
        <div class="author-row">
          <el-avatar
            :src="post.anon ? undefined : post.author_avatar"
            :size="36"
          >{{ authorInitial }}</el-avatar>
          <div class="author-info">
            <div class="author-name">{{ post.anon ? '匿名同学' : post.author_name }}</div>
            <div class="muted tiny">
              发布于 {{ relTime(post.created_at) }}
            </div>
          </div>
        </div>
      </header>

      <!-- Action bar -->
      <div class="action-bar card">
        <div class="actions-left">
          <el-button
            :type="post.liked_by_me ? 'primary' : 'default'"
            :plain="!post.liked_by_me"
            @click="toggleLike"
            :loading="busy.like"
          >
            <el-icon><Star /></el-icon>&nbsp;
            {{ post.liked_by_me ? '已点赞' : '点赞' }}
            <span class="cnt">{{ post.likes }}</span>
          </el-button>
          <el-button
            :type="post.favored_by_me ? 'warning' : 'default'"
            :plain="!post.favored_by_me"
            @click="toggleFav"
            :loading="busy.fav"
          >
            <el-icon><Collection /></el-icon>&nbsp;
            {{ post.favored_by_me ? '已收藏' : '收藏' }}
            <span class="cnt">{{ post.favs }}</span>
          </el-button>
          <el-button @click="scrollToComments">
            <el-icon><ChatDotRound /></el-icon>&nbsp;评论
            <span class="cnt">{{ post.comments }}</span>
          </el-button>
        </div>
        <div class="actions-right">
          <el-button @click="copyLink">
            <el-icon><CopyDocument /></el-icon>&nbsp;复制链接
          </el-button>
          <el-dropdown @command="onMoreCmd" trigger="click">
            <el-button>
              <el-icon><More /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="report">
                  <el-icon><Warning /></el-icon> 举报
                </el-dropdown-item>
                <el-dropdown-item v-if="isAuthor" divided command="edit">
                  <el-icon><Edit /></el-icon> 编辑
                </el-dropdown-item>
                <el-dropdown-item v-if="isAuthor" command="delete">
                  <el-icon><Delete /></el-icon> 删除
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- Main layout -->
      <div class="main-grid">
        <!-- Body -->
        <article class="body-col">
          <div class="card body-card">
            <div
              class="markdown-body"
              v-html="renderedBody"
              ref="bodyEl"
            ></div>
          </div>

          <!-- Comments -->
          <div ref="commentsEl" class="card comments-card">
            <h2 class="section-title">
              <el-icon><ChatDotRound /></el-icon>&nbsp;评论 ({{ post.comments }})
            </h2>

            <!-- Composer -->
            <div class="composer">
              <el-input
                v-model="newComment.body"
                type="textarea"
                :rows="3"
                placeholder="留下你的想法…"
                maxlength="1000"
                show-word-limit
              />
              <div class="composer-actions">
                <el-checkbox v-model="newComment.anon">匿名发表</el-checkbox>
                <el-button
                  type="primary"
                  :disabled="!newComment.body.trim()"
                  :loading="busy.comment"
                  @click="submitComment()"
                >发表</el-button>
              </div>
            </div>

            <!-- List -->
            <ul v-if="topComments.length" class="comment-list">
              <li v-for="c in topComments" :key="c.id" class="comment">
                <CommentItem
                  :comment="c"
                  :replies="repliesOf(c.id)"
                  :reply-target-id="replyTargetId"
                  :reply-text="replyText"
                  :busy="busy.reply"
                  @start-reply="startReply(c.id)"
                  @cancel-reply="cancelReply"
                  @send-reply="sendReply"
                  @update-text="(v) => replyText = v"
                />
              </li>
            </ul>
            <el-empty
              v-else
              description="还没有评论，沙发是你的"
              :image-size="80"
            />
          </div>
        </article>

        <!-- Sidebar -->
        <aside class="side-col">
          <!-- TOC -->
          <div v-if="toc.length" class="card toc-card">
            <div class="side-title">目录</div>
            <ul class="toc">
              <li
                v-for="(h, i) in toc"
                :key="i"
                :class="['toc-item', `level-${h.level}`]"
                @click="scrollToHeading(h.id)"
              >
                {{ h.text }}
              </li>
            </ul>
          </div>

          <!-- Import card -->
          <div v-if="post.has_template" class="card import-card">
            <div class="import-head">
              <el-icon class="import-icon"><DocumentCopy /></el-icon>
              <div>
                <div class="side-title" style="margin-bottom: 2px;">导入到我的小组</div>
                <div class="muted tiny">复用这个项目结构，几秒钟开始</div>
              </div>
            </div>
            <div class="import-body">
              <label class="lbl">选择小组</label>
              <el-select
                v-model="importGid"
                placeholder="选择一个你管理的小组"
                size="default"
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

              <label class="lbl mt-12">导入模式</label>
              <el-radio-group v-model="importMode">
                <el-radio value="replace">替换</el-radio>
                <el-radio value="append">追加</el-radio>
              </el-radio-group>

              <el-button
                type="primary"
                style="width: 100%; margin-top: 12px;"
                :disabled="!importGid"
                :loading="busy.import"
                @click="confirmImport"
              >
                确认导入
              </el-button>
            </div>
          </div>
        </aside>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Star, Collection, ChatDotRound, CopyDocument, More,
  Warning, Edit, Delete, DocumentCopy,
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import dayjs from 'dayjs'
import { Api, type Comment, type PostDetail } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useGroupsStore } from '@/stores/groups'
import CommentItem from './_InspirationCommentItem.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const groupsStore = useGroupsStore()

const postId = computed(() => Number(route.params.id))

const loading = ref(true)
const post = ref<PostDetail | null>(null)
const comments = ref<Comment[]>([])
const bodyEl = ref<HTMLElement | null>(null)
const commentsEl = ref<HTMLElement | null>(null)

const busy = reactive({
  like: false,
  fav: false,
  comment: false,
  reply: false,
  import: false,
})

const newComment = reactive({ body: '', anon: false })
const replyTargetId = ref<number | null>(null)
const replyText = ref('')

const importGid = ref<number>(0)
const importMode = ref<'replace' | 'append'>('replace')

const isAuthor = computed(
  () => !!(post.value && auth.user && post.value.author_id === auth.user.id),
)

const leaderGroups = computed(() =>
  groupsStore.list.filter((g) => g.role === 'leader'),
)

interface TocEntry { id: string; text: string; level: number }
const toc = ref<TocEntry[]>([])

// Configure marked
marked.setOptions({ gfm: true, breaks: true })

const renderedBody = computed(() => {
  if (!post.value?.body_md) return ''
  const raw = marked.parse(post.value.body_md) as string
  const clean = DOMPurify.sanitize(raw, { ADD_ATTR: ['target', 'rel'] })
  return injectHeadingIds(clean)
})

function slugify(s: string, idx: number): string {
  return (
    'h-' +
    idx +
    '-' +
    s
      .toLowerCase()
      .replace(/[^a-z0-9一-龥]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 40)
  )
}

function injectHeadingIds(html: string): string {
  const list: TocEntry[] = []
  const result = html.replace(
    /<h([1-3])([^>]*)>([\s\S]*?)<\/h\1>/g,
    (_m, level, attrs, inner) => {
      const text = String(inner).replace(/<[^>]+>/g, '').trim()
      if (!text) return _m
      const id = slugify(text, list.length)
      list.push({ id, text, level: Number(level) })
      return `<h${level}${attrs} id="${id}">${inner}</h${level}>`
    },
  )
  toc.value = list
  return result
}

async function loadPost() {
  loading.value = true
  try {
    post.value = await Api.post(postId.value)
    comments.value = await Api.comments(postId.value)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载帖子失败')
  } finally {
    loading.value = false
  }
}

watch(postId, () => {
  if (postId.value) {
    void loadPost()
  }
})

onMounted(async () => {
  await loadPost()
  if (!groupsStore.loaded) await groupsStore.refresh().catch(() => {})
  if (leaderGroups.value.length && !importGid.value) {
    importGid.value = leaderGroups.value[0].id
  }
})

// ---------- helpers ----------
const categories: Record<string, string> = {
  template: '模板',
  case: '案例',
  tip: '干货',
  script: '话术',
  tool: '工具',
  link: '网址',
}
function categoryLabel(c: string) {
  return categories[c] || c
}

function relTime(iso: string): string {
  const t = dayjs(iso)
  const now = dayjs()
  const diffMin = now.diff(t, 'minute')
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin} 分钟前`
  const diffHr = now.diff(t, 'hour')
  if (diffHr < 24) return `${diffHr} 小时前`
  const diffD = now.diff(t, 'day')
  if (diffD < 7) return `${diffD} 天前`
  return t.format('YYYY-MM-DD')
}

const authorInitial = computed(() => {
  if (!post.value) return '?'
  if (post.value.anon) return '匿'
  return (post.value.author_name || '?').slice(0, 1)
})

// ---------- actions ----------
async function toggleLike() {
  if (!post.value) return
  busy.like = true
  try {
    const res: any = await Api.likePost(post.value.id)
    if (res && typeof res === 'object') {
      if (typeof res.likes === 'number') post.value.likes = res.likes
      if (typeof res.liked_by_me === 'boolean') {
        post.value.liked_by_me = res.liked_by_me
      } else {
        post.value.liked_by_me = !post.value.liked_by_me
      }
    } else {
      post.value.liked_by_me = !post.value.liked_by_me
      post.value.likes += post.value.liked_by_me ? 1 : -1
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  } finally {
    busy.like = false
  }
}

async function toggleFav() {
  if (!post.value) return
  busy.fav = true
  try {
    const res: any = await Api.favPost(post.value.id)
    if (res && typeof res === 'object') {
      if (typeof res.favs === 'number') post.value.favs = res.favs
      if (typeof res.favored_by_me === 'boolean') {
        post.value.favored_by_me = res.favored_by_me
      } else {
        post.value.favored_by_me = !post.value.favored_by_me
      }
    } else {
      post.value.favored_by_me = !post.value.favored_by_me
      post.value.favs += post.value.favored_by_me ? 1 : -1
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  } finally {
    busy.fav = false
  }
}

async function copyLink() {
  try {
    await navigator.clipboard.writeText(window.location.href)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.warning('复制失败，请手动复制地址栏链接')
  }
}

async function onMoreCmd(cmd: string) {
  if (cmd === 'edit') router.push(`/inspiration/p/${postId.value}/edit`)
  else if (cmd === 'delete') {
    try {
      await ElMessageBox.confirm('确定要删除这篇帖子吗？此操作不可撤销。', '提示', {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
      })
      await Api.deletePost(postId.value)
      ElMessage.success('已删除')
      router.replace('/inspiration')
    } catch (e: any) {
      if (e?.message && e.message.indexOf('cancel') < 0) {
        ElMessage.error(e?.response?.data?.message || '删除失败')
      }
    }
  } else if (cmd === 'report') {
    ElMessage.info('已收到你的举报，我们会尽快处理')
  }
}

// ---------- comments ----------
const topComments = computed(() => comments.value.filter((c) => !c.parent_id))
function repliesOf(parentId: number): Comment[] {
  return comments.value.filter((c) => c.parent_id === parentId)
}

async function submitComment() {
  if (!newComment.body.trim()) return
  busy.comment = true
  try {
    const c = await Api.addComment(postId.value, {
      body: newComment.body.trim(),
      anon: newComment.anon,
    })
    comments.value.push(c)
    if (post.value) post.value.comments += 1
    newComment.body = ''
    ElMessage.success('已发表')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '发表失败')
  } finally {
    busy.comment = false
  }
}

function startReply(parentId: number) {
  replyTargetId.value = parentId
  replyText.value = ''
}
function cancelReply() {
  replyTargetId.value = null
  replyText.value = ''
}

async function sendReply(parentId: number, anon: boolean) {
  if (!replyText.value.trim()) return
  busy.reply = true
  try {
    const c = await Api.addComment(postId.value, {
      body: replyText.value.trim(),
      parent_id: parentId,
      anon,
    })
    comments.value.push(c)
    if (post.value) post.value.comments += 1
    cancelReply()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '回复失败')
  } finally {
    busy.reply = false
  }
}

// ---------- TOC / scroll ----------
function scrollToHeading(id: string) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
function scrollToComments() {
  commentsEl.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// ---------- import ----------
async function confirmImport() {
  if (!post.value || !importGid.value) return
  busy.import = true
  try {
    await Api.importTemplate(post.value.id, importGid.value, importMode.value)
    ElMessage.success('已导入到小组')
    nextTick(() => {
      const target = leaderGroups.value.find((g) => g.id === importGid.value)
      if (target) {
        ElMessageBox.confirm('是否立即查看导入后的项目树？', '导入成功', {
          confirmButtonText: '前往',
          cancelButtonText: '留在此页',
        })
          .then(() => router.push(`/groups/${target.id}/tree`))
          .catch(() => {})
      }
    })
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '导入失败')
  } finally {
    busy.import = false
  }
}
</script>

<style lang="scss" scoped>
.detail-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.detail-skel { padding: 24px; }

/* header */
.detail-head {
  padding: 4px 4px 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.head-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.cat-tag {
  display: inline-block;
  padding: 3px 10px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 999px;
  background: rgba(61,126,255,0.12);
  color: var(--color-primary);
  &.cat-template { background: rgba(61,126,255,0.12); color: var(--color-primary); }
  &.cat-case     { background: rgba(103,194,58,0.14); color: #15803D; }
  &.cat-tip      { background: rgba(230,162,60,0.14); color: #B45309; }
  &.cat-script   { background: rgba(159,122,234,0.14); color: #6D28D9; }
  &.cat-tool     { background: rgba(20,184,166,0.14); color: #0F766E; }
  &.cat-link     { background: rgba(236,72,153,0.14); color: #BE185D; }
}
.course-tag {
  font-size: 12px;
  color: var(--color-primary);
  font-weight: 500;
}
.detail-title {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  line-height: 1.3;
  color: var(--text-primary);
  word-break: break-word;
}
.author-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.author-info {
  display: flex;
  flex-direction: column;
}
.author-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

/* action bar */
.action-bar {
  position: sticky;
  top: 0;
  z-index: 5;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}
.actions-left, .actions-right { display: flex; gap: 6px; flex-wrap: wrap; }
.cnt { margin-left: 6px; font-weight: 600; }

/* main grid */
.main-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 16px;
  align-items: start;
}

/* body */
.body-card { padding: 24px 28px; }
.markdown-body {
  max-width: 760px;
  margin: 0 auto;
  line-height: 1.7;
  font-size: 15px;
  color: var(--text-primary);

  :deep(h1), :deep(h2), :deep(h3) {
    line-height: 1.3;
    margin: 1.6em 0 0.6em;
    color: var(--text-primary);
    font-weight: 700;
  }
  :deep(h1) { font-size: 24px; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; }
  :deep(h2) { font-size: 20px; }
  :deep(h3) { font-size: 17px; }
  :deep(p)  { margin: 0.8em 0; }
  :deep(a)  { color: var(--color-primary); }
  :deep(ul), :deep(ol) { padding-left: 1.5em; margin: 0.6em 0; }
  :deep(li) { margin: 0.3em 0; }
  :deep(blockquote) {
    margin: 1em 0;
    padding: 8px 14px;
    border-left: 4px solid var(--color-primary);
    background: var(--bg-soft);
    color: var(--text-secondary);
    border-radius: 4px;
  }
  :deep(code) {
    background: var(--bg-soft);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: ui-monospace, "SFMono-Regular", Menlo, monospace;
    font-size: 13px;
    color: var(--color-danger);
  }
  :deep(pre) {
    background: var(--bg-soft);
    border: 1px solid var(--border-color);
    padding: 12px 14px;
    border-radius: 8px;
    overflow-x: auto;
    line-height: 1.5;
  }
  :deep(pre code) {
    background: transparent;
    color: var(--text-primary);
    padding: 0;
  }
  :deep(img) {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin: 0.8em 0;
  }
  :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
    th, td {
      border: 1px solid var(--border-color);
      padding: 8px 12px;
      text-align: left;
    }
    th { background: var(--bg-soft); }
  }
  :deep(hr) { border: none; border-top: 1px dashed var(--border-color); margin: 1.5em 0; }
}

/* comments */
.comments-card { padding: 20px 24px; margin-top: 16px; }
.section-title {
  margin: 0 0 14px 0;
  font-size: 17px;
  display: flex;
  align-items: center;
  font-weight: 600;
  color: var(--text-primary);
}
.composer {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 18px;
}
.composer-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.comment-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
}

/* sidebar */
.side-col {
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: sticky;
  top: 70px;
}
.side-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 10px;
}

/* TOC */
.toc {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 60vh;
  overflow-y: auto;
}
.toc-item {
  padding: 6px 10px;
  font-size: 13px;
  color: var(--text-secondary);
  border-radius: 4px;
  cursor: pointer;
  line-height: 1.4;
  &:hover { background: var(--bg-soft); color: var(--color-primary); }
  &.level-2 { padding-left: 18px; font-size: 12px; }
  &.level-3 { padding-left: 28px; font-size: 12px; opacity: 0.85; }
}

/* Import card */
.import-card {
  background: linear-gradient(135deg, rgba(61,126,255,0.05), rgba(155,91,255,0.05));
  border: 1px solid rgba(61,126,255,0.2);
}
.import-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 14px;
}
.import-icon {
  font-size: 24px;
  color: var(--color-primary);
  background: rgba(61,126,255,0.12);
  padding: 8px;
  border-radius: 10px;
}
.lbl {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 6px;
  font-weight: 500;
}
.mt-4  { margin-top: 4px; }
.mt-12 { margin-top: 12px; }

@media (max-width: 992px) {
  .main-grid { grid-template-columns: 1fr; }
  .side-col {
    position: static;
    display: none;
  }
}

@media (max-width: 768px) {
  .body-card { padding: 16px; }
  .detail-title { font-size: 22px; }
  .comments-card { padding: 16px; }
  .action-bar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
