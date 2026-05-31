<template>
  <div class="scene" :class="`scene--${variant} scene--${slideId}`" aria-hidden="true">
    <div class="scene__glow" aria-hidden="true" />
    <div class="scene__content">
    <!-- AI hub -->
    <template v-if="slideId === 'ai'">
      <div class="scene__ai-head">
        <span class="scene__ai-orb"><span class="scene__spark scene__spark--lg" /></span>
        <div class="scene__ai-head-text">
          <span class="scene__ai-title">CoTask AI</span>
          <span class="scene__ai-sub">项目树 · 分工 · 今日建议</span>
        </div>
      </div>
      <div class="scene__ai-chat">
        <div class="scene__ai-bubble scene__ai-bubble--user">
          <span class="scene__ai-bubble-text">帮我把「软件工程大作业」拆成两周可执行的 WBS</span>
        </div>
        <div class="scene__ai-bubble scene__ai-bubble--bot">
          <span class="scene__ai-bubble-label">
            <span class="scene__spark" /> AI 已生成 8 个节点
          </span>
          <div class="scene__ai-preview">
            <span class="scene__tree-bar" />
            <div class="scene__ai-preview-sub">
              <span class="scene__tree-bar scene__tree-bar--short" />
              <span class="scene__tree-bar scene__tree-bar--short" />
            </div>
          </div>
          <span class="scene__ai-bubble-foot">已为 3 项任务匹配技能标签负责人</span>
        </div>
      </div>
      <div class="scene__ai-chips">
        <span>生成项目树</span>
        <span>今日建议</span>
        <span>调整分工</span>
      </div>
    </template>

    <!-- Dashboard -->
    <template v-else-if="slideId === 'dashboard'">
      <div class="scene__kicker">今日焦点</div>
      <div class="scene__row scene__pills">
        <span class="scene__pill scene__pill--urgent">紧急 2</span>
        <span class="scene__pill">待办 5</span>
      </div>
      <div class="scene__card scene__card--task">
        <span class="scene__dot scene__dot--warn" />
        <div class="scene__lines">
          <span class="scene__line scene__line--md" />
          <span class="scene__line scene__line--sm" />
        </div>
        <div class="scene__avatars">
          <span /><span /><span class="scene__av-more">+1</span>
        </div>
      </div>
      <div class="scene__card scene__card--task scene__card--dim">
        <span class="scene__dot" />
        <div class="scene__lines">
          <span class="scene__line scene__line--md" />
          <span class="scene__line scene__line--sm" />
        </div>
      </div>
      <div class="scene__cal">
        <div class="scene__cal-week">
          <span v-for="d in weekDays" :key="d">{{ d }}</span>
        </div>
        <div class="scene__cal-cells">
          <span v-for="n in 14" :key="n" :class="{ hot: n === 9, has: n === 5 || n === 12 }" />
        </div>
      </div>
    </template>

    <!-- Tree -->
    <template v-else-if="slideId === 'tree'">
      <div class="scene__tree">
        <div class="scene__tree-node scene__tree-node--root">
          <span class="scene__tree-bar" />
          <span class="scene__status scene__status--done" />
          <span class="scene__tree-av" />
        </div>
        <div class="scene__tree-children">
          <div class="scene__tree-node scene__tree-node--active">
            <span class="scene__tree-bar" />
            <span class="scene__status scene__status--prog" />
            <span class="scene__tree-av" />
          </div>
          <div class="scene__tree-node">
            <span class="scene__tree-bar scene__tree-bar--short" />
            <span class="scene__status" />
          </div>
        </div>
        <div class="scene__tree-children scene__tree-children--deep">
          <div class="scene__tree-node">
            <span class="scene__tree-bar scene__tree-bar--xs" />
          </div>
        </div>
      </div>
      <div class="scene__tree-hint">
        <span class="scene__hint-text">拖拽调整 · 状态一目了然</span>
      </div>
    </template>

    <!-- Timeline -->
    <template v-else-if="slideId === 'timeline'">
      <div class="scene__kicker">本周 2 项临近截止</div>
      <div class="scene__gantt">
        <div class="scene__gantt-row">
          <span class="scene__gantt-av" />
          <div class="scene__gantt-track">
            <span class="scene__gantt-bar" style="--l: 8%; --w: 42%" />
          </div>
        </div>
        <div class="scene__gantt-row">
          <span class="scene__gantt-av" />
          <div class="scene__gantt-track">
            <span class="scene__gantt-bar scene__gantt-bar--warn" style="--l: 20%; --w: 55%" />
          </div>
        </div>
        <div class="scene__gantt-row">
          <span class="scene__gantt-av" />
          <div class="scene__gantt-track">
            <span class="scene__gantt-bar scene__gantt-bar--done" style="--l: 5%; --w: 30%" />
            <span class="scene__gantt-bar" style="--l: 48%; --w: 38%" />
          </div>
        </div>
      </div>
      <div class="scene__gantt-legend">
        <span><i class="leg leg--warn" />即将截止</span>
        <span><i class="leg leg--today" />今天</span>
      </div>
      <div class="scene__today-line" />
    </template>

    <!-- Files -->
    <template v-else-if="slideId === 'files'">
      <div class="scene__kicker">资料关联任务节点</div>
      <div class="scene__files">
        <aside class="scene__files-side">
          <div class="scene__files-item is-on">
            <span class="scene__files-ico scene__files-ico--folder" />
            <span class="scene__line scene__line--sm" />
          </div>
          <div class="scene__files-item">
            <span class="scene__files-ico scene__files-ico--folder" />
            <span class="scene__line scene__line--xs" />
          </div>
          <div class="scene__files-item">
            <span class="scene__files-ico scene__files-ico--doc" />
            <span class="scene__line scene__line--xs" />
          </div>
        </aside>
        <div class="scene__files-main">
          <div class="scene__files-row" v-for="i in 3" :key="i">
            <span class="scene__files-ico" :class="fileIco(i)" />
            <div class="scene__lines">
              <span class="scene__line scene__line--sm" />
              <span class="scene__line scene__line--xs" />
            </div>
            <span class="scene__files-tag">PDF</span>
          </div>
        </div>
      </div>
    </template>

    <!-- Discussion -->
    <template v-else-if="slideId === 'discussion'">
      <div class="scene__channel">
        <span class="scene__hash">#</span>
        <span class="scene__line scene__line--sm scene__line--grow" />
      </div>
      <div class="scene__msg">
        <span class="scene__gantt-av" />
        <div class="scene__msg-body">
          <span class="scene__line scene__line--md" />
          <span class="scene__line scene__line--sm" />
        </div>
      </div>
      <div class="scene__msg scene__msg--me">
        <span class="scene__gantt-av" />
        <div class="scene__msg-body">
          <span class="scene__line scene__line--md" />
        </div>
      </div>
      <div class="scene__composer">
        <span class="scene__mention">@成员</span>
        <span class="scene__line scene__line--xs scene__line--grow" />
        <span class="scene__send" aria-hidden="true" />
      </div>
    </template>

    <!-- Inspiration -->
    <template v-else-if="slideId === 'inspiration'">
      <div class="scene__insp">
        <div class="scene__insp-head">
          <span class="scene__insp-star">★</span>
          <div class="scene__lines">
            <span class="scene__line scene__line--md" />
            <span class="scene__line scene__line--xs" />
          </div>
          <span class="scene__insp-score">4.9</span>
        </div>
        <div class="scene__insp-tree">
          <span class="scene__tree-bar" />
          <div class="scene__insp-tree-sub">
            <span class="scene__tree-bar scene__tree-bar--short" />
            <span class="scene__tree-bar scene__tree-bar--short" />
          </div>
        </div>
        <div class="scene__insp-cta">一键导入到小组</div>
      </div>
    </template>

    <template v-else>
      <div class="scene__ai-head">
        <span class="scene__ai-orb"><span class="scene__spark scene__spark--lg" /></span>
        <span class="scene__ai-title">CoTask AI</span>
      </div>
    </template>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    slideId: string
    variant?: 'glass' | 'light'
  }>(),
  { variant: 'glass' },
)

const weekDays = ['一', '二', '三', '四', '五', '六', '日']

function fileIco(i: number) {
  return i === 1 ? 'scene__files-ico--doc' : i === 2 ? 'scene__files-ico--img' : 'scene__files-ico--doc'
}
</script>

<style scoped lang="scss">
/* ---- Tokens per variant ---- */
.scene--glass {
  --sc-surface: rgba(255, 255, 255, 0.1);
  --sc-surface-2: rgba(255, 255, 255, 0.16);
  --sc-border: rgba(255, 255, 255, 0.22);
  --sc-line: rgba(255, 255, 255, 0.45);
  --sc-line-dim: rgba(255, 255, 255, 0.28);
  --sc-text: rgba(255, 255, 255, 0.92);
  --sc-text-dim: rgba(255, 255, 255, 0.65);
  --sc-primary: #fff;
  --sc-primary-bg: rgba(255, 255, 255, 0.22);
  --sc-warn: rgba(251, 191, 36, 0.95);
  --sc-warn-bg: rgba(251, 191, 36, 0.28);
  --sc-success: rgba(134, 239, 172, 0.95);
  --sc-success-bg: rgba(34, 197, 94, 0.25);
  --sc-ai: rgba(196, 181, 253, 0.95);
  --sc-ai-bg: rgba(139, 92, 246, 0.35);
  --sc-mention-bg: rgba(96, 165, 250, 0.35);
  --sc-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
}

.scene--light {
  --sc-surface: var(--bg-card);
  --sc-surface-2: var(--bg-soft);
  --sc-border: var(--border-subtle);
  --sc-line: var(--border-color);
  --sc-line-dim: color-mix(in srgb, var(--border-color) 70%, transparent);
  --sc-text: var(--text-primary);
  --sc-text-dim: var(--text-tertiary);
  --sc-primary: var(--color-primary);
  --sc-primary-bg: var(--color-primary-light);
  --sc-warn: var(--color-warning);
  --sc-warn-bg: color-mix(in srgb, var(--color-warning) 18%, var(--bg-soft));
  --sc-success: var(--color-success);
  --sc-success-bg: color-mix(in srgb, var(--color-success) 14%, var(--bg-soft));
  --sc-ai: #7c3aed;
  --sc-ai-bg: color-mix(in srgb, #7c3aed 12%, var(--bg-soft));
  --sc-mention-bg: var(--color-primary-light);
  --sc-shadow: var(--shadow-sm);
}

/* Per-slide accent (open layout, no card chrome) */
.scene--ai {
  --sc-accent: #c4b5fd;
}

.scene--dashboard {
  --sc-accent: #93c5fd;
}

.scene--tree {
  --sc-accent: #a78bfa;
}

.scene--timeline {
  --sc-accent: #5eead4;
}

.scene--files {
  --sc-accent: #fbbf24;
}

.scene--discussion {
  --sc-accent: #f472b6;
}

.scene--inspiration {
  --sc-accent: #facc15;
}

.scene {
  position: relative;
  width: 100%;
}

.scene__glow {
  position: absolute;
  inset: -12% -8% auto;
  height: 55%;
  border-radius: 50%;
  pointer-events: none;
  opacity: 0.35;
  background: radial-gradient(
    ellipse 80% 100% at 30% 0%,
    color-mix(in srgb, var(--sc-accent, #fff) 55%, transparent),
    transparent 70%
  );
}

.scene--light .scene__glow {
  opacity: 0.5;
}

.scene__content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.scene__content > * {
  animation: scene-rise 0.52s cubic-bezier(0.22, 1, 0.36, 1) backwards;
}

.scene__content > *:nth-child(1) {
  animation-delay: 0.02s;
}

.scene__content > *:nth-child(2) {
  animation-delay: 0.07s;
}

.scene__content > *:nth-child(3) {
  animation-delay: 0.12s;
}

.scene__content > *:nth-child(4) {
  animation-delay: 0.17s;
}

.scene__content > *:nth-child(5) {
  animation-delay: 0.22s;
}

.scene__content > *:nth-child(6) {
  animation-delay: 0.27s;
}

@keyframes scene-rise {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .scene__content > * {
    animation: none;
  }
}

.scene__kicker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--sc-text-dim);
  line-height: 1.3;

  &::before {
    content: '';
    width: 14px;
    height: 2px;
    border-radius: 1px;
    background: linear-gradient(90deg, var(--sc-accent, var(--sc-primary)), transparent);
    opacity: 0.9;
  }
}

/* Open layout: no nested glass/card panels on feature slides */
.scene--glass,
.scene--light {
  .scene__card,
  .scene__cal,
  .scene__files-main,
  .scene__tree-hint {
    border: none;
    background: transparent;
    box-shadow: none;
    padding-left: 0;
    padding-right: 0;
  }

  .scene__files-side {
    background: transparent;
    box-shadow: none;
    border-top: none;
    border-left: none;
    border-bottom: none;
  }

  .scene__card {
    padding-top: 4px;
    padding-bottom: 4px;
  }

  .scene__cal {
    padding: 4px 0 0;
  }

  .scene__gantt-track {
    border: none;
    background: color-mix(in srgb, var(--sc-line-dim) 35%, transparent);
  }

  .scene__channel {
    background: transparent;
    border-top: none;
    border-left: none;
    border-right: none;
    border-bottom: 1px solid color-mix(in srgb, var(--sc-accent, var(--sc-border)) 30%, var(--sc-border));
    padding-bottom: 8px;
  }

  .scene__composer {
    margin-top: 2px;
    padding: 10px 0 0;
    border: none;
    border-top: 1px solid color-mix(in srgb, var(--sc-accent, var(--sc-border)) 22%, var(--sc-border));
    border-radius: 0;
    background: transparent;
  }

  .scene__insp,
  .scene__insp-tree {
    border: none;
    background: transparent;
    box-shadow: none;
    padding-left: 0;
    padding-right: 0;
  }

  .scene__insp-tree {
    border-left: 2px solid color-mix(in srgb, var(--sc-accent, var(--sc-border)) 40%, var(--sc-border));
  }

  .scene__msg--me .scene__msg-body {
    border: none;
    background: color-mix(in srgb, var(--sc-primary-bg) 70%, transparent);
    box-shadow: none;
  }

  .scene__msg:not(.scene__msg--me) .scene__msg-body {
    padding: 4px 0;
  }
}

.scene__row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.scene__pill {
  font-size: 10px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: var(--radius-full);
  border: 1px solid color-mix(in srgb, var(--sc-accent, var(--sc-border)) 25%, var(--sc-border));
  background: color-mix(in srgb, var(--sc-accent, var(--sc-surface)) 12%, var(--sc-surface));
  color: var(--sc-text-dim);
  line-height: 1.2;
  backdrop-filter: blur(6px);

  &--urgent {
    color: var(--sc-warn);
    background: var(--sc-warn-bg);
    border-color: color-mix(in srgb, var(--sc-warn) 40%, transparent);
  }

  &--ai {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    color: var(--sc-ai);
    background: var(--sc-ai-bg);
    border-color: color-mix(in srgb, var(--sc-ai) 35%, transparent);
  }

  &--sm {
    margin-left: auto;
    font-weight: 500;
  }
}

.scene__spark {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--sc-ai);
  box-shadow: 0 0 8px var(--sc-ai);

  &--lg {
    width: 14px;
    height: 14px;
    box-shadow: 0 0 14px var(--sc-ai);
  }
}

.scene--ai {
  gap: 12px;
}

.scene__ai-head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.scene__ai-orb {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(
    145deg,
    color-mix(in srgb, var(--sc-ai) 35%, transparent),
    color-mix(in srgb, var(--sc-ai) 8%, transparent)
  );
  border: 1px solid color-mix(in srgb, var(--sc-ai) 35%, transparent);
  box-shadow: 0 0 24px color-mix(in srgb, var(--sc-ai) 30%, transparent);
}

.scene__ai-head-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.scene__ai-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--sc-text);
  letter-spacing: -0.02em;
}

.scene__ai-sub {
  font-size: 10px;
  color: var(--sc-text-dim);
}

.scene__ai-chat {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.scene__ai-bubble {
  border-radius: 12px;
  padding: 10px 12px;
  border: 1px solid transparent;

  &--user {
    align-self: flex-end;
    max-width: 92%;
    background: color-mix(in srgb, var(--sc-primary-bg) 90%, transparent);
    border-color: color-mix(in srgb, var(--sc-primary) 18%, transparent);
    backdrop-filter: blur(8px);
  }

  &--bot {
    background: color-mix(in srgb, var(--sc-ai-bg) 65%, transparent);
    border-color: color-mix(in srgb, var(--sc-ai) 22%, transparent);
    backdrop-filter: blur(10px);
  }
}

.scene__ai-bubble-text {
  font-size: 10px;
  line-height: 1.45;
  color: var(--sc-text);
}

.scene__ai-bubble-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  font-weight: 600;
  color: var(--sc-ai);
  margin-bottom: 8px;
}

.scene__ai-bubble-foot {
  display: block;
  margin-top: 8px;
  font-size: 9px;
  color: var(--sc-text-dim);
}

.scene__ai-preview {
  padding: 6px 0 2px 12px;
  border-left: 2px solid color-mix(in srgb, var(--sc-ai) 45%, transparent);
}

.scene__ai-preview-sub {
  display: flex;
  gap: 6px;
  padding: 6px 0 0 10px;
  margin-top: 4px;
  border-left: 1px dashed var(--sc-border);

  .scene__tree-bar {
    flex: 1;
  }
}

.scene__ai-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;

  span {
    font-size: 9px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: var(--radius-full);
    border: 1px solid color-mix(in srgb, var(--sc-ai) 28%, transparent);
    background: color-mix(in srgb, var(--sc-ai-bg) 80%, transparent);
    color: var(--sc-ai);
    backdrop-filter: blur(6px);
  }
}

.scene__ai-banner {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid color-mix(in srgb, var(--sc-ai) 30%, transparent);
  background: var(--sc-ai-bg);

  &--compact {
    align-items: center;
    padding: 8px 10px;

    .scene__ai-banner-title {
      font-size: 10px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
}

.scene__ai-banner-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.scene__ai-banner-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--sc-ai);
  line-height: 1.3;
}

.scene--glass .scene__ai-bubble--user {
  background: rgba(255, 255, 255, 0.18);
}

.scene--glass .scene__ai-title,
.scene--glass .scene__ai-bubble-text {
  color: rgba(255, 255, 255, 0.95);
}

.scene__card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--sc-border);
  background: var(--sc-surface-2);
  box-shadow: var(--sc-shadow);

  &--dim {
    opacity: 0.72;
  }
}

.scene__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--sc-line);

  &--warn {
    background: var(--sc-warn);
    box-shadow: 0 0 0 3px var(--sc-warn-bg);
  }
}

.scene__lines {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.scene__line {
  display: block;
  height: 6px;
  border-radius: var(--radius-full);
  background: linear-gradient(
    90deg,
    var(--sc-line) 0%,
    color-mix(in srgb, var(--sc-line) 55%, transparent) 100%
  );

  &--md {
    width: 78%;
  }

  &--sm {
    width: 52%;
    background: linear-gradient(
      90deg,
      var(--sc-line-dim) 0%,
      color-mix(in srgb, var(--sc-line-dim) 40%, transparent) 100%
    );
  }

  &--xs {
    width: 38%;
    background: linear-gradient(
      90deg,
      var(--sc-line-dim) 0%,
      color-mix(in srgb, var(--sc-line-dim) 35%, transparent) 100%
    );
  }

  &--grow {
    flex: 1;
    width: auto;
    height: 8px;
  }
}

.scene__avatars {
  display: flex;
  align-items: center;

  span {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    border: 2px solid var(--sc-surface-2);
    background: var(--sc-line);
    margin-left: -6px;

    &:first-child {
      margin-left: 0;
    }
  }
}

.scene--glass .scene__avatars span {
  background: rgba(255, 255, 255, 0.5);
}

.scene--light .scene__avatars span {
  background: color-mix(in srgb, var(--color-primary) 25%, var(--border-subtle));
}

.scene__av-more {
  width: auto !important;
  min-width: 22px;
  padding: 0 4px;
  font-size: 9px;
  font-weight: 600;
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  color: var(--sc-text-dim);
  background: var(--sc-surface) !important;
}

.scene__cal {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--sc-border);
  background: var(--sc-surface);
}

.scene__cal-week {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-bottom: 8px;
  font-size: 9px;
  font-weight: 600;
  text-align: center;
  color: var(--sc-text-dim);
}

.scene__cal-cells {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;

  span {
    aspect-ratio: 1;
    border-radius: 4px;
    background: var(--sc-line-dim);

    &.has {
      background: var(--sc-primary-bg);
    }

    &.hot {
      background: var(--sc-primary);
      box-shadow: 0 0 0 2px var(--sc-primary-bg);
    }
  }
}

.scene--glass .scene__cal-cells span.hot {
  background: #fff;
}

/* Tree */
.scene__tree {
  padding: 8px 0 4px 10px;
  border-left: 2px solid var(--sc-border);
}

.scene__tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;

  &--root .scene__tree-bar {
    height: 9px;
    opacity: 1;
  }

  &--active .scene__tree-bar {
    background: linear-gradient(
      90deg,
      var(--sc-accent, var(--sc-primary)),
      color-mix(in srgb, var(--sc-accent, var(--sc-primary)) 45%, transparent)
    );
    opacity: 1;
    box-shadow: 0 0 12px color-mix(in srgb, var(--sc-accent, var(--sc-primary)) 35%, transparent);
  }
}

.scene__tree-bar {
  flex: 1;
  height: 7px;
  border-radius: var(--radius-full);
  background: linear-gradient(90deg, var(--sc-line), color-mix(in srgb, var(--sc-line) 40%, transparent));
  max-width: 100%;

  &--short {
    max-width: 55%;
  }

  &--xs {
    max-width: 38%;
  }
}

.scene__tree-children {
  padding-left: 14px;
  border-left: 1px dashed var(--sc-border);
  margin-left: 6px;

  &--deep {
    padding-left: 12px;
    margin-top: -4px;
  }
}

.scene__status {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--sc-line-dim);

  &--done {
    background: var(--sc-success);
    box-shadow: 0 0 0 2px var(--sc-success-bg);
  }

  &--prog {
    background: var(--sc-primary);
    box-shadow: 0 0 0 2px var(--sc-primary-bg);
  }
}

.scene__tree-av {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--sc-line);
}

.scene--glass .scene__tree-av {
  background: rgba(255, 255, 255, 0.55);
}

.scene__tree-hint {
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  padding: 0;
}

.scene__hint-text {
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.02em;
  color: var(--sc-text-dim);
  padding-left: 2px;
  border-left: 2px solid color-mix(in srgb, var(--sc-accent, var(--sc-border)) 50%, var(--sc-border));
}

/* Gantt */
.scene__gantt {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.scene__gantt-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.scene__gantt-av {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--sc-line);
}

.scene--glass .scene__gantt-av {
  background: rgba(255, 255, 255, 0.4);
}

.scene--light .scene__gantt-av {
  background: color-mix(in srgb, var(--color-primary) 20%, var(--border-subtle));
}

.scene__gantt-track {
  flex: 1;
  height: 22px;
  border-radius: 6px;
  background: var(--sc-surface);
  border: 1px solid var(--sc-border);
  position: relative;
  overflow: hidden;
}

.scene__gantt-bar {
  position: absolute;
  top: 4px;
  bottom: 4px;
  left: var(--l, 0);
  width: var(--w, 40%);
  border-radius: 4px;
  background: var(--sc-primary-bg);
  border: 1px solid color-mix(in srgb, var(--sc-primary) 50%, transparent);

  &--warn {
    background: var(--sc-warn-bg);
    border-color: color-mix(in srgb, var(--sc-warn) 45%, transparent);
  }

  &--done {
    opacity: 0.55;
  }
}

.scene--glass .scene__gantt-bar {
  background: rgba(255, 255, 255, 0.35);
  border-color: rgba(255, 255, 255, 0.25);
}

.scene--glass .scene__gantt-bar--warn {
  background: var(--sc-warn-bg);
}

.scene__gantt-legend {
  display: flex;
  gap: 12px;
  font-size: 9px;
  color: var(--sc-text-dim);

  span {
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
}

.leg {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  font-style: normal;

  &--warn {
    background: var(--sc-warn);
  }

  &--today {
    background: var(--sc-primary);
  }
}

.scene--timeline {
  position: relative;
}

.scene__today-line {
  position: absolute;
  top: 28px;
  bottom: 36px;
  left: 58%;
  width: 2px;
  border-radius: 1px;
  background: var(--sc-primary);
  opacity: 0.85;
  pointer-events: none;
}

/* Files */
.scene__files {
  display: grid;
  grid-template-columns: 88px 1fr;
  gap: 0 14px;
  min-height: 132px;
  align-items: start;
}

.scene__files-side {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 2px 12px 2px 0;
  border-right: 1px solid color-mix(in srgb, var(--sc-accent, var(--sc-border)) 28%, var(--sc-border));
}

.scene__files-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 2px;
  border-radius: 6px;

  &.is-on .scene__line {
    background: linear-gradient(
      90deg,
      var(--sc-accent, var(--sc-primary)),
      color-mix(in srgb, var(--sc-accent, var(--sc-line)) 40%, transparent)
    );
  }
}

.scene__files-main {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  border-radius: 8px;
  border: 1px solid var(--sc-border);
  background: var(--sc-surface-2);
}

.scene__files-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.scene__files-ico {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  flex-shrink: 0;
  background: var(--sc-line-dim);

  &--folder {
    background: var(--sc-warn-bg);
    position: relative;

    &::after {
      content: '';
      position: absolute;
      top: -4px;
      left: 2px;
      width: 10px;
      height: 4px;
      border-radius: 2px 2px 0 0;
      background: inherit;
    }
  }

  &--doc {
    background: var(--sc-primary-bg);
  }

  &--img {
    background: color-mix(in srgb, #ec4899 20%, var(--sc-surface));
  }
}

.scene__files-tag {
  font-size: 9px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--sc-surface);
  border: 1px solid var(--sc-border);
  color: var(--sc-text-dim);
}

/* Discussion */
.scene__channel {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--sc-border);
}

.scene__hash {
  font-size: 14px;
  font-weight: 700;
  color: var(--sc-text-dim);
}

.scene__msg {
  display: flex;
  gap: 8px;
  align-items: flex-start;

  &--me {
    flex-direction: row-reverse;

    .scene__msg-body {
      align-items: flex-end;
      background: var(--sc-primary-bg);
      border: 1px solid var(--sc-border);
      border-radius: 10px 10px 2px 10px;
      padding: 8px 10px;
    }
  }
}

.scene__msg-body {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 6px 0;
  flex: 1;
  min-width: 0;
}

.scene__mention {
  font-size: 10px;
  font-weight: 600;
  color: var(--sc-primary);
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--sc-mention-bg);
  align-self: flex-start;
}

.scene__composer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid var(--sc-border);
  background: var(--sc-surface);
}

.scene__send {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--sc-primary);
}

.scene--glass .scene__send {
  background: rgba(255, 255, 255, 0.9);
}

/* Inspiration */
.scene__insp {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.scene__insp-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 0;
}

.scene__insp-star {
  font-size: 22px;
  line-height: 1;
  color: #fbbf24;
  filter: drop-shadow(0 2px 4px rgba(251, 191, 36, 0.4));
}

.scene__insp-score {
  font-size: 11px;
  font-weight: 700;
  color: var(--sc-warn);
  padding: 3px 8px;
  border-radius: var(--radius-full);
  background: var(--sc-warn-bg);
  flex-shrink: 0;
}

.scene__insp-tree {
  padding: 4px 0 4px 10px;
  border-left: 2px solid var(--sc-border);
}

.scene__insp-tree-sub {
  display: flex;
  gap: 8px;
  padding: 8px 0 0 12px;
  border-left: 1px dashed var(--sc-border);
  margin-left: 4px;
  margin-top: 6px;

  .scene__tree-bar {
    flex: 1;
  }
}

.scene__insp-cta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--sc-accent, var(--sc-primary));
  line-height: 1.4;

  &::after {
    content: '→';
    font-size: 12px;
    opacity: 0.75;
    transition: transform 0.2s ease;
  }
}

.scene--glass .scene__insp-cta {
  color: color-mix(in srgb, var(--sc-accent, #fff) 75%, #fff);
}

.scene__spark {
  animation: spark-pulse 2.4s ease-in-out infinite;
}

@keyframes spark-pulse {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }

  50% {
    opacity: 0.72;
    transform: scale(0.92);
  }
}

@media (prefers-reduced-motion: reduce) {
  .scene__spark {
    animation: none;
  }
}
</style>
