<template>
  <div class="detail-page insp-sub-page page">
    <template v-if="loading && !post">
      <div class="insp-panel detail-skel">
        <el-skeleton animated :rows="10" />
      </div>
    </template>

    <template v-else-if="post">
      <button
        type="button"
        class="insp-capsule-btn insp-back-btn"
        aria-label="返回灵感广场"
        @click="goBack"
      >
        <el-icon><ArrowLeft /></el-icon>
        <span>返回</span>
      </button>

      <header class="detail-head">
        <div class="head-meta">
          <span class="insp-tag" :class="`cat-${post.category}`">{{ categoryLabel(post.category) }}</span>
          <span v-if="post.course_tag" class="insp-tag insp-tag--course">#{{ post.course_tag }}</span>
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

      <div
        class="insp-main-grid"
        :class="{ 'insp-main-grid--full': !showSidebar }"
      >
        <article class="insp-main-col">
          <div class="insp-action-strip">
            <div class="insp-action-strip__left">
              <button
                type="button"
                class="insp-capsule-btn"
                :class="{ active: post.liked_by_me }"
                :disabled="busy.like"
                @click="toggleLike"
              >
                <el-icon><ThumbUpIcon :filled="post.liked_by_me" /></el-icon>
                {{ post.liked_by_me ? '已点赞' : '点赞' }}
                <span class="cnt">{{ post.likes }}</span>
              </button>
              <button
                type="button"
                class="insp-capsule-btn"
                :class="{ active: post.favored_by_me, 'insp-capsule-btn--warn': post.favored_by_me }"
                :disabled="busy.fav"
                @click="toggleFav"
              >
                <el-icon>
                  <StarFilled v-if="post.favored_by_me" />
                  <Star v-else />
                </el-icon>
                {{ post.favored_by_me ? '已收藏' : '收藏' }}
                <span class="cnt">{{ post.favs }}</span>
              </button>
              <button type="button" class="insp-capsule-btn" @click="scrollToComments">
                <el-icon><ChatDotRound /></el-icon>
                评论
                <span class="cnt">{{ post.comments }}</span>
              </button>
            </div>
            <div class="insp-action-strip__right">
              <button type="button" class="insp-capsule-btn" @click="copyLink">
                <el-icon><CopyDocument /></el-icon>
                复制链接
              </button>
              <el-dropdown trigger="click" @command="onMoreCmd">
                <button type="button" class="insp-capsule-btn">
                  <el-icon><More /></el-icon>
                </button>
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

          <div
            v-if="post.has_template"
            class="insp-panel structure-card"
            v-loading="templateLoading"
          >
            <h2 class="section-title">项目结构</h2>
            <div class="template-preview__bar">
              <span class="template-preview__label">模板结构预览</span>
              <span v-if="templateStructureStats" class="template-preview__stats muted tiny">
                {{ templateStructureStats }}
              </span>
            </div>
            <div v-if="templateNodes.length" class="structure-card__tree">
              <TemplatePreviewTree :nodes="templateNodes" />
            </div>
            <p v-else-if="!templateLoading" class="muted tiny template-preview__empty">
              该模板暂无任务节点
            </p>
            <div class="structure-card__actions">
              <button
                type="button"
                class="insp-capsule-btn insp-capsule-btn--primary"
                @click="openImportDialog"
              >
                导入到我的小组
              </button>
            </div>
          </div>

          <div class="insp-panel body-card">
            <div
              class="markdown-body"
              v-html="renderedBody"
              ref="bodyEl"
            ></div>
          </div>

          <!-- Comments -->
          <div ref="commentsEl" class="insp-panel comments-card">
            <h2 class="section-title">
              <el-icon><ChatDotRound /></el-icon>&nbsp;评论 ({{ post.comments }})
            </h2>

            <div class="composer">
              <el-input
                v-model="newComment.body"
                class="insp-capsule-textarea"
                type="textarea"
                :rows="3"
                placeholder="留下你的想法…"
                maxlength="1000"
                show-word-limit
              />
              <div class="insp-comment-actions">
                <button
                  type="button"
                  class="insp-capsule-btn"
                  :disabled="!newComment.body.trim() || busy.comment"
                  @click="submitComment(true)"
                >
                  {{ busy.comment ? '提交中…' : '匿名发表' }}
                </button>
                <button
                  type="button"
                  class="insp-capsule-btn insp-capsule-btn--primary"
                  :disabled="!newComment.body.trim() || busy.comment"
                  @click="submitComment(false)"
                >
                  {{ busy.comment ? '提交中…' : '发表' }}
                </button>
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

        <aside v-if="showSidebar" class="insp-side-col">
          <div v-if="toc.length" class="toc-block">
            <div class="toc-block__title">目录</div>
            <ul class="toc">
              <li
                v-for="(h, i) in toc"
                :key="i"
                :class="['list-row', 'toc-item', `level-${h.level}`]"
                @click="scrollToHeading(h.id)"
              >
                {{ h.text }}
              </li>
            </ul>
          </div>

        </aside>
      </div>
    </template>

    <TemplateImportDialog
      v-if="post?.has_template"
      v-model="importDialogOpen"
      :post-id="postId"
      :template-nodes="templateNodes"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, Star, StarFilled, ChatDotRound, CopyDocument, More,
  Warning, Edit, Delete,
} from '@element-plus/icons-vue'
import ThumbUpIcon from '@/components/common/ThumbUpIcon.vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { relativeTime as relTime } from '@/utils/datetime'
import { Api, type Comment, type PostDetail, type TaskNode } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useGroupsStore } from '@/stores/groups'
import TemplatePreviewTree from '@/components/inspiration/TemplatePreviewTree.vue'
import TemplateImportDialog from '@/components/inspiration/TemplateImportDialog.vue'
import { previewTreeStats } from '@/components/inspiration/templatePreviewTree'
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
})

const newComment = reactive({ body: '' })
const replyTargetId = ref<number | null>(null)
const replyText = ref('')

const importDialogOpen = ref(false)
const templateLoading = ref(false)
const templateNodes = ref<TaskNode[]>([])

const templateStructureStats = computed(() => previewTreeStats(templateNodes.value))

const returnTo = computed(() => {
  const q = route.query.returnTo
  if (typeof q === 'string' && q.startsWith('/')) return q
  return '/inspiration'
})

function goBack() {
  router.replace(returnTo.value)
}

const isAuthor = computed(
  () =>
    !!(
      post.value
      && auth.user
      && (post.value.is_author ?? post.value.author_id === auth.user.id)
    ),
)

const leaderGroups = computed(() =>
  groupsStore.list.filter((g) => g.role === 'leader'),
)

const showSidebar = computed(() => toc.value.length > 0)

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

async function syncTemplateNodes() {
  templateNodes.value = []
  if (!post.value?.has_template) return

  const embedded = post.value.template_nodes
  if (embedded && embedded.length > 0) {
    templateNodes.value = embedded
    return
  }

  templateLoading.value = true
  try {
    const res = await Api.templateNodes(postId.value)
    templateNodes.value = res.nodes
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载模板结构失败')
  } finally {
    templateLoading.value = false
  }
}

function openImportDialog() {
  if (!leaderGroups.value.length) {
    ElMessage.warning('你目前不是任何小组的组长，无法导入模板')
    return
  }
  importDialogOpen.value = true
}

async function loadPost() {
  loading.value = true
  try {
    post.value = await Api.post(postId.value)
    comments.value = await Api.comments(postId.value)
    await syncTemplateNodes()
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
  if (!groupsStore.loaded) await groupsStore.refresh().catch(() => {})
  await loadPost()
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

const authorInitial = computed(() => {
  if (!post.value) return '?'
  if (post.value.anon) return '匿'
  return (post.value.author_name || '?').slice(0, 1)
})

// ---------- actions ----------
function applyEngagement(
  patch: Partial<Pick<PostDetail, 'likes' | 'favs' | 'comments' | 'liked_by_me' | 'favored_by_me'>>,
) {
  if (!post.value) return
  Object.assign(post.value, patch)
}

async function toggleLike() {
  if (!post.value) return
  busy.like = true
  try {
    const res = await Api.likePost(post.value.id)
    applyEngagement({
      likes: res.likes,
      liked_by_me: res.liked_by_me ?? res.liked,
    })
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
    const res = await Api.favPost(post.value.id)
    applyEngagement({
      favs: res.favs,
      favored_by_me: res.favored_by_me ?? res.favored,
    })
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
  if (cmd === 'edit') {
    const query: Record<string, string> = {}
    const rt = route.query.returnTo
    if (typeof rt === 'string' && rt.startsWith('/')) query.returnTo = rt
    router.push({ path: `/inspiration/p/${postId.value}/edit`, query })
  }
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

async function submitComment(asAnon: boolean) {
  if (!newComment.body.trim()) return
  busy.comment = true
  try {
    const c = await Api.addComment(postId.value, {
      body: newComment.body.trim(),
      anon: asAnon,
    })
    comments.value.push(c)
    if (post.value) {
      applyEngagement({
        comments: typeof c.comments === 'number' ? c.comments : post.value.comments + 1,
      })
    }
    newComment.body = ''
    ElMessage.success(asAnon ? '已匿名发表' : '已发表')
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
    if (post.value) {
      applyEngagement({
        comments: typeof c.comments === 'number' ? c.comments : post.value.comments + 1,
      })
    }
    cancelReply()
    ElMessage.success(anon ? '已匿名回复' : '已回复')
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

</script>

<style lang="scss">
@use '@/styles/inspiration-pages.scss';
</style>

<style lang="scss" scoped>
.detail-head {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.head-meta {
  display: flex;
  gap: var(--space-2);
  align-items: center;
  flex-wrap: wrap;
}

.detail-title {
  margin: 0;
  font-size: var(--fs-2xl);
  font-weight: 700;
  line-height: 1.3;
  color: var(--text-primary);
  word-break: break-word;
}

.author-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.author-info {
  display: flex;
  flex-direction: column;
}

.author-name {
  font-size: var(--fs-sm);
  font-weight: 500;
  color: var(--text-primary);
}

.structure-card__tree {
  max-height: 320px;
  overflow-y: auto;
  margin-bottom: var(--space-4);
  padding: var(--space-1) 0;
}

.structure-card__actions {
  display: flex;
  justify-content: flex-end;
  padding-top: var(--space-3);
  border-top: 1px solid var(--border-subtle);
}

.body-card,
.comments-card {
  width: 100%;
}

.markdown-body {
  width: 100%;
  max-width: none;
  margin: 0;
  line-height: 1.7;
  font-size: var(--fs-md);
  color: var(--text-primary);

  :deep(h1), :deep(h2), :deep(h3) {
    line-height: 1.3;
    margin: 1.6em 0 0.6em;
    color: var(--text-primary);
    font-weight: 700;
  }
  :deep(h1) { font-size: var(--fs-2xl); border-bottom: 1px solid var(--border-color); padding-bottom: var(--space-2); }
  :deep(h2) { font-size: var(--fs-xl); }
  :deep(h3) { font-size: var(--fs-lg); }
  :deep(p)  { margin: 0.8em 0; }
  :deep(a)  { color: var(--color-primary); }
  :deep(ul), :deep(ol) { padding-left: 1.5em; margin: 0.6em 0; }
  :deep(li) { margin: 0.3em 0; }
  :deep(blockquote) {
    margin: 1em 0;
    padding: var(--space-2) var(--space-4);
    border-left: 4px solid var(--color-primary);
    background: var(--bg-soft);
    color: var(--text-secondary);
    border-radius: var(--radius-sm);
  }
  :deep(code) {
    background: var(--bg-soft);
    padding: 2px var(--space-2);
    border-radius: var(--radius-sm);
    font-family: ui-monospace, "SFMono-Regular", Menlo, monospace;
    font-size: var(--fs-sm);
    color: var(--color-danger);
  }
  :deep(pre) {
    background: var(--bg-soft);
    border: 1px solid var(--border-color);
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-md);
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
    border-radius: var(--radius-md);
    margin: 0.8em 0;
  }
  :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
    th, td {
      border: 1px solid var(--border-color);
      padding: var(--space-2) var(--space-3);
      text-align: left;
    }
    th { background: var(--bg-soft); }
  }
  :deep(hr) { border: none; border-top: 1px dashed var(--border-color); margin: 1.5em 0; }
}

/* ============================================================
   Comments
   ============================================================ */
.section-title {
  margin: 0 0 var(--space-4) 0;
  font-size: var(--fs-lg);
  display: flex;
  align-items: center;
  font-weight: 600;
  color: var(--text-primary);
}

.composer {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}


.comment-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
}

/* TOC — flat list, no card chrome */
.toc-block {
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 0;
  box-shadow: none;
}

.toc-block__title {
  margin: 0 0 var(--space-3);
  font-size: var(--fs-base);
  font-weight: 600;
  color: var(--text-primary);
}

.toc {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  max-height: 60vh;
  overflow-y: auto;
}

/* TOC depth indentation only — base styles come from .list-row */
.toc-item.level-2 { padding-left: var(--space-5); }
.toc-item.level-3 { padding-left: var(--space-8); opacity: 0.8; }

@media (max-width: 992px) {
  .insp-side-col { display: none; }
}

@media (max-width: 768px) {
  .detail-title { font-size: var(--fs-xl); }
}
</style>
