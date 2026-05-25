<template>
  <div class="inspiration-page">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-inner">
        <div class="hero-text">
          <h1>灵感广场</h1>
          <p class="muted">发现优秀的小组模板、案例、干货与工具，启发你的下一个项目。</p>
        </div>
        <div class="hero-search">
          <el-input
            ref="searchRef"
            v-model="q"
            placeholder="搜索灵感…  (Ctrl + K)"
            size="large"
            clearable
            :prefix-icon="Search"
            @keydown.enter="onSearch"
            @clear="onSearch"
          >
            <template #append>
              <el-button :icon="Search" @click="onSearch">搜索</el-button>
            </template>
          </el-input>
        </div>
      </div>
    </section>

    <!-- Filter bar -->
    <section class="filter-bar card">
      <div class="filters">
        <div class="tabs">
          <button
            v-for="c in categories"
            :key="c.value"
            class="tab-btn"
            :class="{ active: category === c.value }"
            @click="onCategory(c.value)"
          >
            {{ c.label }}
          </button>
        </div>

        <div class="filter-right">
          <el-select v-model="sort" size="default" style="width: 120px" @change="reset">
            <el-option label="最新" value="latest" />
            <el-option label="最热" value="hot" />
            <el-option label="收藏多" value="favorites" />
          </el-select>
          <el-input
            v-model="courseTag"
            placeholder="课程标签"
            size="default"
            style="width: 160px"
            clearable
            @keydown.enter="reset"
            @clear="reset"
          />
          <el-switch
            v-model="favoritesOnly"
            active-text="我收藏的"
            inline-prompt
            @change="reset"
          />
          <el-button type="primary" :icon="Plus" @click="goNew">发布</el-button>
        </div>
      </div>
    </section>

    <!-- Grid -->
    <section class="grid-section">
      <div v-if="!loading && total" class="grid-meta muted tiny">
        共 {{ total }} 篇
      </div>

      <template v-if="loading && !items.length">
        <div class="grid">
          <div v-for="i in 6" :key="i" class="card sk-card">
            <el-skeleton animated>
              <template #template>
                <el-skeleton-item variant="image" style="width: 100%; height: 160px" />
                <div style="padding: 12px;">
                  <el-skeleton-item variant="h3" style="width: 60%" />
                  <el-skeleton-item variant="text" style="margin-top: 12px;" />
                  <el-skeleton-item variant="text" style="width: 80%" />
                </div>
              </template>
            </el-skeleton>
          </div>
        </div>
      </template>

      <template v-else-if="!items.length">
        <el-empty description="还没有相关内容，去发一篇吧" :image-size="120">
          <el-button type="primary" @click="goNew">+ 发布</el-button>
        </el-empty>
      </template>

      <template v-else>
        <div class="grid">
          <article
            v-for="p in items"
            :key="p.id"
            class="card post-card"
            @click="goDetail(p.id)"
          >
            <div class="cover">
              <img
                v-if="p.cover_url"
                :src="p.cover_url"
                :alt="p.title"
                loading="lazy"
              />
              <div v-else class="cover-placeholder" :style="gradientFor(p.id)">
                <span>{{ categoryLabel(p.category) }}</span>
              </div>
              <span class="cover-tag" :class="`cat-${p.category}`">
                {{ categoryLabel(p.category) }}
              </span>
            </div>
            <div class="post-body">
              <h3 class="post-title clamp-2">{{ p.title }}</h3>
              <p class="post-excerpt clamp-2 muted">{{ p.excerpt || '暂无摘要' }}</p>

              <div class="post-foot">
                <div class="post-author">
                  <el-avatar
                    :src="p.anon ? undefined : p.author_avatar"
                    :size="22"
                  >{{ authorInitial(p) }}</el-avatar>
                  <span class="author-name">{{ p.anon ? '匿名同学' : p.author_name }}</span>
                  <span v-if="p.course_tag" class="course-tag">#{{ p.course_tag }}</span>
                </div>

                <div class="post-stats">
                  <span :class="{ active: p.liked_by_me }">
                    <el-icon><Star /></el-icon> {{ p.likes }}
                  </span>
                  <span :class="{ active: p.favored_by_me }">
                    <el-icon><Collection /></el-icon> {{ p.favs }}
                  </span>
                  <span>
                    <el-icon><ChatDotRound /></el-icon> {{ p.comments }}
                  </span>
                </div>
              </div>

              <div v-if="p.category === 'template' && p.has_template" class="tpl-action">
                <el-button size="small" type="primary" plain @click.stop="goDetail(p.id)">
                  导入到我的小组
                </el-button>
              </div>
            </div>
          </article>
        </div>

        <div v-if="hasMore" class="load-more">
          <el-button :loading="loadingMore" @click="loadMore">加载更多</el-button>
        </div>
        <div v-else-if="items.length" class="muted tiny load-end">没有更多了</div>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Search, Plus, Star, Collection, ChatDotRound,
} from '@element-plus/icons-vue'
import { Api, type PostBrief } from '@/api'

const router = useRouter()

const searchRef = ref<any>(null)
const q = ref('')
const category = ref<string>('')
const sort = ref<'latest' | 'hot' | 'favorites'>('latest')
const courseTag = ref('')
const favoritesOnly = ref(false)

const items = ref<PostBrief[]>([])
const total = ref(0)
const page = ref(1)
const size = 12
const loading = ref(true)
const loadingMore = ref(false)

const categories = [
  { label: '全部', value: '' },
  { label: '模板', value: 'template' },
  { label: '案例', value: 'case' },
  { label: '干货', value: 'tip' },
  { label: '话术', value: 'script' },
  { label: '工具', value: 'tool' },
  { label: '网址', value: 'link' },
]

const hasMore = computed(() => items.value.length < total.value)

function categoryLabel(c: string) {
  return categories.find((x) => x.value === c)?.label || c
}

function authorInitial(p: PostBrief) {
  if (p.anon) return '匿'
  return (p.author_name || '?').slice(0, 1)
}

function gradientFor(id: number) {
  const palette = [
    'linear-gradient(135deg, #3D7EFF 0%, #6F4DFF 100%)',
    'linear-gradient(135deg, #FF9F45 0%, #FF6B6B 100%)',
    'linear-gradient(135deg, #43E97B 0%, #38F9D7 100%)',
    'linear-gradient(135deg, #FA709A 0%, #FEE140 100%)',
    'linear-gradient(135deg, #5EE7DF 0%, #B490CA 100%)',
    'linear-gradient(135deg, #FBC2EB 0%, #A6C1EE 100%)',
  ]
  return { background: palette[id % palette.length] }
}

async function fetchPosts(opts: { append?: boolean } = {}) {
  const params: Record<string, unknown> = {
    page: page.value,
    size,
    sort: sort.value,
  }
  if (q.value.trim()) params.q = q.value.trim()
  if (category.value) params.category = category.value
  if (courseTag.value.trim()) params.course_tag = courseTag.value.trim()
  if (favoritesOnly.value) params.favorites = true

  if (opts.append) loadingMore.value = true
  else loading.value = true

  try {
    const data = await Api.posts(params)
    total.value = data.total
    if (opts.append) items.value = [...items.value, ...data.items]
    else items.value = data.items
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载灵感失败')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function reset() {
  page.value = 1
  void fetchPosts()
}
function onSearch() {
  reset()
}
function onCategory(c: string) {
  category.value = c
  reset()
}
function loadMore() {
  page.value += 1
  void fetchPosts({ append: true })
}

function goDetail(id: number) {
  router.push(`/inspiration/p/${id}`)
}
function goNew() {
  router.push('/inspiration/new')
}

function onKey(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    const el = searchRef.value?.input || searchRef.value?.$el?.querySelector('input')
    el?.focus?.()
  }
}

onMounted(() => {
  void fetchPosts()
  window.addEventListener('keydown', onKey)
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
})
</script>

<style lang="scss" scoped>
.inspiration-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
}

/* hero */
.hero {
  position: relative;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: linear-gradient(135deg, #3D7EFF 0%, #6F4DFF 60%, #9B5BFF 100%);
  color: #fff;
  padding: 28px 28px 22px;
  box-shadow: var(--shadow-card);
}
.hero::after {
  content: '';
  position: absolute;
  width: 280px; height: 280px;
  right: -80px; top: -100px;
  background: rgba(255,255,255,0.1);
  border-radius: 50%;
}
.hero-inner {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.hero-text {
  h1 { margin: 0 0 4px 0; font-size: 26px; font-weight: 700; }
  p  { margin: 0; color: rgba(255,255,255,0.85); }
  .muted { color: rgba(255, 255, 255, 0.85); }
}
.hero-search { max-width: 720px; }
.hero-search :deep(.el-input-group__append) {
  background: rgba(255,255,255,0.9);
  border-color: rgba(255,255,255,0.4);
}

/* filter bar */
.filter-bar {
  position: sticky;
  top: 0;
  z-index: 5;
  padding: 12px 16px;
}
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}
.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.tab-btn {
  border: none;
  background: transparent;
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  border-radius: 999px;
  cursor: pointer;
  transition: all .15s ease;
  &:hover { background: var(--bg-soft); color: var(--text-primary); }
  &.active {
    background: rgba(61,126,255,0.12);
    color: var(--color-primary);
  }
}
.filter-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* grid */
.grid-section { display: flex; flex-direction: column; gap: 12px; }
.grid-meta { padding: 0 4px; }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.post-card {
  padding: 0;
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  transition: transform .15s ease, box-shadow .15s ease;
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.08);
  }
}
.cover {
  position: relative;
  width: 100%;
  height: 160px;
  overflow: hidden;
  background: var(--bg-soft);

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }
}
.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 1px;
}
.cover-tag {
  position: absolute;
  top: 10px; left: 10px;
  background: rgba(0,0,0,0.55);
  color: #fff;
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 999px;
  font-weight: 600;
  backdrop-filter: blur(4px);
}

.post-body {
  padding: 12px 14px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}
.post-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.35;
}
.post-excerpt {
  margin: 0;
  font-size: 13px;
  line-height: 1.45;
}
.clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
}

.post-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
  gap: 8px;
  flex-wrap: wrap;
}
.post-author {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  min-width: 0;

  .author-name {
    max-width: 90px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .course-tag {
    color: var(--color-primary);
    font-weight: 500;
  }
}
.post-stats {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--text-tertiary);
  span {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    &.active { color: var(--color-primary); }
  }
}
.tpl-action {
  margin-top: 4px;
  display: flex;
  justify-content: flex-end;
}

.load-more {
  display: flex;
  justify-content: center;
  margin-top: 8px;
}
.load-end {
  text-align: center;
  padding: 12px 0;
}

@media (max-width: 768px) {
  .hero { padding: 20px 16px; }
  .hero-text h1 { font-size: 22px; }
  .grid { grid-template-columns: 1fr; }
  .filters { flex-direction: column; align-items: stretch; }
  .filter-right { flex-direction: column; align-items: stretch; }
  .filter-right > * { width: 100%; }
}
</style>
