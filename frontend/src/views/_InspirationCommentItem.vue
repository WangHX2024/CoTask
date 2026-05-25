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
        <el-button
          text
          size="small"
          @click="$emit('startReply')"
        >
          <el-icon><ChatLineRound /></el-icon>&nbsp;回复
        </el-button>
      </div>

      <!-- Reply composer -->
      <div v-if="replyTargetId === comment.id" class="reply-composer">
        <el-input
          :model-value="replyText"
          type="textarea"
          :rows="2"
          placeholder="写下你的回复…"
          maxlength="500"
          @update:model-value="(v) => $emit('updateText', v)"
        />
        <div class="rc-actions">
          <el-checkbox v-model="replyAnon">匿名</el-checkbox>
          <div class="rc-btns">
            <el-button size="small" @click="$emit('cancelReply')">取消</el-button>
            <el-button
              size="small"
              type="primary"
              :disabled="!replyText.trim()"
              :loading="busy"
              @click="$emit('sendReply', comment.id, replyAnon)"
            >发送</el-button>
          </div>
        </div>
      </div>

      <!-- Nested replies (level 2) -->
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
import { ref, watch } from 'vue'
import { ChatLineRound } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import type { Comment } from '@/api'

interface Props {
  comment: Comment
  replies: Comment[]
  replyTargetId: number | null
  replyText: string
  busy: boolean
}

const props = defineProps<Props>()
defineEmits<{
  (e: 'startReply'): void
  (e: 'cancelReply'): void
  (e: 'sendReply', parentId: number, anon: boolean): void
  (e: 'updateText', v: string): void
}>()

const replyAnon = ref(false)

watch(
  () => props.replyTargetId,
  (val) => {
    if (val !== props.comment.id) replyAnon.value = false
  },
)

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
  gap: 10px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
  &:last-child { border-bottom: none; }
}
.c-avatar { flex-shrink: 0; }
.c-main { flex: 1; min-width: 0; }
.c-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 4px;
}
.c-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}
.c-body {
  font-size: 14px;
  line-height: 1.55;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}
.c-actions {
  margin-top: 4px;
}

.reply-composer {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
  padding: 10px;
  background: var(--bg-soft);
  border-radius: var(--radius-sm);
}
.rc-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.rc-btns { display: flex; gap: 6px; }

.replies {
  list-style: none;
  margin: 8px 0 0;
  padding: 0 0 0 32px;
  display: flex;
  flex-direction: column;
}
.reply {
  display: flex;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px dashed var(--border-color);
  &:last-child { border-bottom: none; }
}
</style>
