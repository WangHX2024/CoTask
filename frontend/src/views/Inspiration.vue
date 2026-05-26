<template>
  <div class="inspiration-page page">
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
            class="hero-search-input"
            placeholder="搜索标题、作者、课程名…  (Ctrl + K)"
            size="large"
            clearable
            :prefix-icon="Search"
            @keydown.enter="onSearch"
            @clear="onSearch"
            @input="onSearchInput"
          />
        </div>
      </div>
    </section>

    <!-- Filter toolbar -->
    <div class="inspiration-toolbar">
      <SegmentedControl
        v-model="category"
        size="md"
        class="category-filter"
        :options="categories"
        @change="reset"
      />

      <div class="toolbar-actions">
        <el-select
          v-model="sort"
          class="toolbar-sort"
          @change="reset"
        >
          <el-option label="最新" value="latest" />
          <el-option label="最热" value="hot" />
          <el-option label="收藏多" value="favorites" />
        </el-select>
        <button
          type="button"
          class="toolbar-filter-btn"
          :class="{ active: favoritesOnly }"
          @click="toggleFavorites"
        >
          <el-icon><Star /></el-icon>
          <span>我收藏的</span>
        </button>
        <button
          type="button"
          class="toolbar-filter-btn"
          :class="{ active: mineOnly }"
          @click="toggleMine"
        >
          <el-icon><EditPen /></el-icon>
          <span>我发布的</span>
        </button>
        <el-button type="primary" round class="toolbar-publish" @click="goNew">
          <el-icon><Plus /></el-icon>&nbsp;发布
        </el-button>
      </div>
    </div>

    <!-- Grid -->
    <section v-loading="refreshing" class="grid-section">
      <div v-if="total" class="grid-meta muted tiny">
        共 {{ total }} 篇
      </div>

      <template v-if="initialLoading">
        <div class="grid">
          <div v-for="i in 6" :key="i" class="card sk-card">
            <el-skeleton animated>
              <template #template>
                <el-skeleton-item variant="image" class="sk-cover" />
                <div class="sk-body">
                  <el-skeleton-item variant="h3" style="width: 60%" />
                  <el-skeleton-item variant="text" />
                  <el-skeleton-item variant="text" style="width: 80%" />
                </div>
              </template>
            </el-skeleton>
          </div>
        </div>
      </template>

      <template v-else-if="!items.length">
        <el-empty description="还没有相关内容，去发一篇吧" :image-size="120">
          <el-button type="primary" round class="toolbar-publish" @click="goNew">
            <el-icon><Plus /></el-icon>&nbsp;发布
          </el-button>
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
                    :size="24"
                  >{{ authorInitial(p) }}</el-avatar>
                  <span class="author-name">{{ p.anon ? '匿名同学' : p.author_name }}</span>
                  <span v-if="p.course_tag" class="course-tag">#{{ p.course_tag }}</span>
                </div>

                <div class="post-stats">
                  <span :class="{ active: p.liked_by_me }">
                    <el-icon><ThumbUpIcon :filled="p.liked_by_me" /></el-icon>
                    {{ p.likes }}
                  </span>
                  <span :class="{ active: p.favored_by_me }">
                    <el-icon>
                      <StarFilled v-if="p.favored_by_me" />
                      <Star v-else />
                    </el-icon>
                    {{ p.favs }}
                  </span>
                  <span>
                    <el-icon><ChatDotRound /></el-icon> {{ p.comments }}
                  </span>
                </div>
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
import { useDebounceFn } from '@vueuse/core'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Search, Plus, Star, StarFilled, ChatDotRound, EditPen,
} from '@element-plus/icons-vue'
import { Api, type PostBrief } from '@/api'
import SegmentedControl from '@/components/common/SegmentedControl.vue'
import ThumbUpIcon from '@/components/common/ThumbUpIcon.vue'

const route = useRoute()
const router = useRouter()

const searchRef = ref<any>(null)
const q = ref('')
const category = ref<string>('')
const sort = ref<'latest' | 'hot' | 'favorites'>('latest')
const favoritesOnly = ref(false)
const mineOnly = ref(false)

const items = ref<PostBrief[]>([])
const total = ref(0)
const page = ref(1)
const size = 12
const initialLoading = ref(true)
const refreshing = ref(false)
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
  if (favoritesOnly.value) params.favorites = true
  if (mineOnly.value) params.mine = true

  if (opts.append) {
    loadingMore.value = true
  } else if (items.value.length > 0) {
    refreshing.value = true
  } else {
    initialLoading.value = true
  }

  try {
    const data = await Api.posts(params)
    total.value = data.total
    if (opts.append) items.value = [...items.value, ...data.items]
    else items.value = data.items
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载灵感失败')
  } finally {
    initialLoading.value = false
    refreshing.value = false
    loadingMore.value = false
  }
}

function reset() {
  page.value = 1
  void fetchPosts()
}

const debouncedSearch = useDebounceFn(() => reset(), 350)

function onSearchInput() {
  debouncedSearch()
}

function onSearch() {
  debouncedSearch.cancel()
  reset()
}

function toggleFavorites() {
  favoritesOnly.value = !favoritesOnly.value
  if (favoritesOnly.value) mineOnly.value = false
  reset()
}

function toggleMine() {
  mineOnly.value = !mineOnly.value
  if (mineOnly.value) favoritesOnly.value = false
  reset()
}
function loadMore() {
  page.value += 1
  void fetchPosts({ append: true })
}

function goDetail(id: number) {
  router.push({
    path: `/inspiration/p/${id}`,
    query: { returnTo: route.fullPath },
  })
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
/* Layout from .page (global) */
.inspiration-page {
  --toolbar-h: 38px;
}

/* ============================================================
   Hero — 32px uniform padding
   ============================================================ */
.hero {
  position: relative;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: linear-gradient(135deg, #2563EB 0%, #4F46E5 55%, #7C3AED 100%);
  color: var(--text-inverse);
  padding: var(--space-8);
  box-shadow: var(--shadow-md);

  &::before {
    content: '';
    position: absolute;
    width: 360px; height: 360px;
    right: -100px; top: -120px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 50%;
    pointer-events: none;
  }

  &::after {
    content: '';
    position: absolute;
    width: 200px; height: 200px;
    left: -60px; bottom: -80px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 50%;
    pointer-events: none;
  }
}

.hero-inner {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.hero-text {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);

  h1 {
    margin: 0;
    font-size: var(--fs-3xl);
    font-weight: 700;
    letter-spacing: -0.5px;
  }

  p {
    margin: 0;
    font-size: var(--fs-md);
    color: rgba(255, 255, 255, 0.84);
    line-height: 1.5;
  }
}

.hero-search {
  max-width: 680px;
}

.hero-search-input {
  :deep(.el-input__wrapper) {
    background: rgba(255, 255, 255, 0.95);
    box-shadow: var(--shadow-md);
    padding-left: var(--space-4);
    padding-right: var(--space-4);
    min-height: 48px;
  }

  :deep(.el-input__inner) {
    font-size: var(--fs-md);
  }

  :deep(.el-input__prefix) {
    color: var(--text-tertiary);
  }
}

/* ============================================================
   Filter toolbar — no outer card, sits in page flow
   ============================================================ */
.inspiration-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.category-filter {
  width: fit-content;
  max-width: 100%;
  flex: 0 0 auto;
  overflow-x: auto;

  :deep(.segmented-control.segmented-control--md) {
    height: var(--toolbar-h);
    box-sizing: border-box;
  }

  :deep(.segmented-control--md .segmented-control__btn) {
    min-height: calc(var(--toolbar-h) - 6px);
    padding: 7px 12px;
    box-sizing: border-box;
  }
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
  flex-wrap: wrap;
}

.toolbar-sort {
  width: 108px;

  :deep(.el-select__wrapper) {
    height: var(--toolbar-h) !important;
    min-height: var(--toolbar-h) !important;
    box-shadow: 0 0 0 1px var(--border-color) inset !important;
    padding: 0 var(--space-4) !important;
    background: var(--bg-card) !important;
    box-sizing: border-box;
  }

  :deep(.el-select__selected-item) {
    font-size: var(--fs-base);
  }
}

.toolbar-filter-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  height: var(--toolbar-h);
  padding: 0 var(--space-4);
  border: none;
  border-radius: var(--radius-full);
  background: var(--bg-card);
  box-shadow: 0 0 0 1px var(--border-color) inset;
  color: var(--text-secondary);
  font-size: var(--fs-base);
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: background 120ms ease, color 120ms ease, box-shadow 120ms ease;

  .el-icon {
    font-size: 14px;
  }

  &:hover:not(.active) {
    color: var(--text-primary);
    background: var(--bg-soft);
    box-shadow: 0 0 0 1px var(--text-tertiary) inset;
  }

  &.active {
    color: var(--color-primary);
    background: var(--color-primary-light);
    box-shadow: none;
  }
}

.toolbar-publish {
  height: var(--toolbar-h) !important;
  min-height: var(--toolbar-h) !important;
  padding: 0 var(--space-4) !important;
  font-size: var(--fs-base);
  font-weight: 600;
  line-height: 1;
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* ============================================================
   Content grid — uniform card-grid spacing
   ============================================================ */
.grid-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.grid-meta { padding: 0 var(--space-1); }

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(288px, 1fr));
  gap: var(--space-6);
}

/* Skeleton card matches real post-card layout */
.sk-card {
  padding: 0;
  overflow: hidden;
}
.sk-cover { width: 100%; height: 160px; }
.sk-body  {
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

/* ---------- Post card ---------- */
.post-card {
  padding: 0;
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  transition: border-color 150ms ease, box-shadow 150ms ease, transform 150ms ease;

  &:hover {
    border-color: var(--color-primary);
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
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
    transition: transform 200ms ease;
  }

  &:hover img { transform: scale(1.03); }
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-inverse);
  font-size: var(--fs-lg);
  font-weight: 600;
  letter-spacing: 1px;
}

.cover-tag {
  position: absolute;
  top: var(--space-2);
  left: var(--space-2);
  background: rgba(0, 0, 0, 0.5);
  color: var(--text-inverse);
  font-size: var(--fs-xs);
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  font-weight: 600;
  backdrop-filter: blur(6px);
}

/* Card body — uniform 16px padding/gap (compact card) */
.post-body {
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  flex: 1;
}

.post-title {
  margin: 0;
  font-size: var(--fs-md);
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
}

.post-excerpt {
  margin: 0;
  font-size: var(--fs-sm);
  line-height: 1.5;
  color: var(--text-secondary);
}

.post-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
  gap: var(--space-2);
  flex-wrap: wrap;
  padding-top: var(--space-2);
  border-top: 1px solid var(--border-subtle);
}

.post-author {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--fs-sm);
  color: var(--text-secondary);
  min-width: 0;

  .author-name {
    max-width: 80px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .course-tag {
    color: var(--color-primary);
    font-weight: 500;
    font-size: var(--fs-xs);
  }
}

.post-stats {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--fs-sm);
  color: var(--text-tertiary);

  span {
    display: inline-flex;
    align-items: center;
    gap: var(--space-1);
    transition: color 120ms ease;
    &.active { color: var(--color-primary); }
  }

  :deep(.el-icon) {
    font-size: 15px;
    line-height: 1;
  }
}

.load-more {
  display: flex;
  justify-content: center;
}

.load-end {
  text-align: center;
  padding: var(--space-4) 0;
  color: var(--text-tertiary);
  font-size: var(--fs-sm);
}

@media (max-width: 768px) {
  .hero { padding: var(--space-6); }
  .hero-text h1 { font-size: var(--fs-2xl); }
  .grid { grid-template-columns: 1fr; }
  .filters { flex-direction: column; align-items: stretch; }
  .filter-right { flex-direction: column; align-items: stretch; }
  .filter-right > * { width: 100%; }
}
</style>
