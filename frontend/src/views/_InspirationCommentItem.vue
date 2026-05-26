<template>
  <div class="c-item">
    <el-avatar
      :src="comment.anon ? undefined : comment.author_avatar"
      :size="32"
      class="c-avatar"
    >{{ initial(comment) }}</el-avatar>
    <div class="c-main">
      <div class="c-head">
        <span class="c-name">{{ comment.anon ? '匿名同学' : comment.author_name }}</span>
        <span class="muted tiny">{{ relTime(comment.created_at) }}</span>
      </div>
      <div class="c-body">{{ comment.body }}</div>
      <div class="c-actions">
        <button type="button" class="c-reply-btn" @click="$emit('startReply')">
          <el-icon><ChatLineRound /></el-icon>
          <span>回复</span>
        </button>
      </div>

      <div v-if="replyTargetId === comment.id" class="reply-composer">
        <el-input
          :model-value="replyText"
          class="insp-capsule-textarea"
          type="textarea"
          :rows="2"
          placeholder="写下你的回复…"
          maxlength="500"
          show-word-limit
          @update:model-value="(v) => $emit('updateText', v)"
        />
        <div class="insp-comment-actions">
          <button type="button" class="insp-capsule-btn" @click="$emit('cancelReply')">
            取消
          </button>
          <button
            type="button"
            class="insp-capsule-btn"
            :disabled="!replyText.trim() || busy"
            @click="$emit('sendReply', comment.id, true)"
          >
            {{ busy ? '提交中…' : '匿名回复' }}
          </button>
          <button
            type="button"
            class="insp-capsule-btn insp-capsule-btn--primary"
            :disabled="!replyText.trim() || busy"
            @click="$emit('sendReply', comment.id, false)"
          >
            {{ busy ? '回复中…' : '回复' }}
          </button>
        </div>
      </div>

      <ul v-if="replies.length" class="replies">
        <li v-for="r in replies" :key="r.id" class="reply">
          <el-avatar
            :src="r.anon ? undefined : r.author_avatar"
            :size="26"
            class="c-avatar"
          >{{ initial(r) }}</el-avatar>
          <div class="c-main">
            <div class="c-head">
              <span class="c-name">{{ r.anon ? '匿名同学' : r.author_name }}</span>
              <span class="muted tiny">{{ relTime(r.created_at) }}</span>
            </div>
            <div class="c-body">{{ r.body }}</div>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ChatLineRound } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import type { Comment } from '@/api'

defineProps<{
  comment: Comment
  replies: Comment[]
  replyTargetId: number | null
  replyText: string
  busy: boolean
}>()

defineEmits<{
  (e: 'startReply'): void
  (e: 'cancelReply'): void
  (e: 'sendReply', parentId: number, anon: boolean): void
  (e: 'updateText', v: string): void
}>()

function initial(c: Comment) {
  if (c.anon) return '匿'
  return (c.author_name || '?').slice(0, 1)
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
</script>

<style lang="scss" scoped>
.c-item {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-4) 0;
  border-bottom: 1px solid var(--border-subtle);

  &:last-child {
    border-bottom: none;
  }
}

.c-avatar {
  flex-shrink: 0;
}

.c-main {
  flex: 1;
  min-width: 0;
}

.c-head {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
  margin-bottom: var(--space-1);
}

.c-name {
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.c-body {
  font-size: var(--fs-base);
  line-height: 1.55;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.c-actions {
  margin-top: var(--space-2);
}

.c-reply-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--fs-sm);
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: color 120ms ease, background 120ms ease;

  &:hover {
    color: var(--color-primary);
    background: var(--bg-soft);
  }

  .el-icon {
    font-size: 14px;
  }
}

.reply-composer {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-top: var(--space-3);
  padding: var(--space-4);
  background: var(--bg-soft);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
}

.replies {
  list-style: none;
  margin: var(--space-3) 0 0;
  padding: 0 0 0 var(--space-8);
  display: flex;
  flex-direction: column;
}

.reply {
  display: flex;
  gap: var(--space-2);
  padding: var(--space-3) 0;
  border-bottom: 1px dashed var(--border-subtle);

  &:last-child {
    border-bottom: none;
  }
}
</style>
