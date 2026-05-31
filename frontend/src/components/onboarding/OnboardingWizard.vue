<template>
  <el-dialog
    v-model="open"
    class="ob-dialog"
    :show-close="false"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    width="min(560px, 94vw)"
    align-center
    append-to-body
    destroy-on-close
  >
    <div class="ob">
      <header class="ob-header">
        <CoTaskLogo size="sm" variant="on-light" :show-wordmark="true" />
        <div class="ob-header__end">
          <span class="ob-kicker">{{ stepMeta[step].label }} · {{ step + 1 }}/3</span>
          <button
            v-if="step < 2"
            type="button"
            class="ob-text-btn"
            :disabled="finishing"
            @click="onSkipAll"
          >
            跳过
          </button>
        </div>
      </header>

      <div class="ob-progress" role="progressbar" :aria-valuenow="step + 1" aria-valuemin="1" aria-valuemax="3">
        <span
          v-for="(_, i) in stepMeta"
          :key="i"
          class="ob-progress__seg"
          :class="{ 'is-done': step > i, 'is-active': step === i }"
        />
      </div>

      <main class="ob-body">
        <div class="ob-intro">
          <h2 class="ob-intro__title">{{ heroCopy.title }}</h2>
          <p class="ob-intro__desc">{{ heroCopy.lead }}</p>
        </div>

        <Transition name="ob-fade" mode="out-in">
          <!-- Skills -->
          <section v-if="step === 0" key="skills" class="ob-step">
            <div v-if="selectedSkills.length" class="ob-block">
              <div class="ob-block__label">
                <span>已选技能</span>
                <span class="ob-block__meta">{{ selectedSkills.length }} 项</span>
              </div>
              <div class="ob-chips">
                <button
                  v-for="s in selectedSkills"
                  :key="s"
                  type="button"
                  class="ob-chip is-selected"
                  @click="toggleSkill(s)"
                >
                  {{ s }}
                  <span class="ob-chip__close" aria-hidden="true">×</span>
                </button>
              </div>
            </div>

            <div class="ob-block">
              <div class="ob-block__label">常用技能</div>
              <div class="ob-chips">
                <button
                  v-for="s in presetSkills"
                  :key="s"
                  type="button"
                  class="ob-chip"
                  :class="{ 'is-selected': isSelected(s) }"
                  @click="toggleSkill(s)"
                >
                  {{ s }}
                </button>
              </div>
            </div>

            <div class="ob-field-row">
              <el-input
                v-model="customSkill"
                class="insp-capsule-input"
                placeholder="自定义技能"
                maxlength="32"
                @keydown.enter.prevent="addCustomSkill"
              />
              <button type="button" class="insp-capsule-btn" @click="addCustomSkill">添加</button>
            </div>
          </section>

          <!-- Group -->
          <section v-else-if="step === 1" key="group" class="ob-step">
            <div v-if="groupsStore.list.length" class="ob-notice ob-notice--ok">
              <el-icon :size="18"><CircleCheckFilled /></el-icon>
              <span>已加入 {{ groupsStore.list.length }} 个小组，可直接进入下一步</span>
            </div>

            <SegmentedControl
              v-model="groupMode"
              size="md"
              class="ob-segment"
              :options="groupModeOptions"
            />

            <div class="ob-panel">
              <el-form
                v-if="groupMode === 'create'"
                ref="createFormRef"
                :model="createForm"
                :rules="createRules"
                label-position="top"
                class="ob-form"
              >
                <el-form-item label="课程名" prop="course_name">
                  <el-input
                    v-model="createForm.course_name"
                    class="insp-capsule-input"
                    placeholder="如：软件工程"
                    maxlength="40"
                  />
                </el-form-item>
                <el-form-item label="小组名" prop="name">
                  <el-input
                    v-model="createForm.name"
                    class="insp-capsule-input"
                    placeholder="小组名称"
                    maxlength="40"
                  />
                </el-form-item>
                <button
                  type="button"
                  class="insp-capsule-btn insp-capsule-btn--primary ob-form__action"
                  :disabled="groupBusy"
                  @click="onCreateGroup"
                >
                  {{ groupBusy ? '创建中…' : '创建小组' }}
                </button>
              </el-form>

              <el-form
                v-else
                ref="joinFormRef"
                :model="joinForm"
                :rules="joinRules"
                label-position="top"
                class="ob-form"
              >
                <el-form-item
                  label="邀请码"
                  prop="invite_code"
                  class="ob-form-item--invite"
                >
                  <el-input
                    v-model="joinForm.invite_code"
                    class="insp-capsule-input"
                    placeholder="8 位字母或数字"
                    maxlength="8"
                    @input="onInviteInput"
                  />
                  <p class="ob-form__hint">向组织者索取邀请码</p>
                </el-form-item>
                <button
                  type="button"
                  class="insp-capsule-btn insp-capsule-btn--primary ob-form__action"
                  :disabled="groupBusy"
                  @click="onJoinGroup"
                >
                  {{ groupBusy ? '加入中…' : '加入小组' }}
                </button>
              </el-form>
            </div>
          </section>

          <!-- Tour -->
          <section v-else key="tour" class="ob-step ob-step--tour">
            <div class="ob-tour">
              <Transition :name="slideAnim" mode="out-in">
                <div
                  :key="tourIndex"
                  class="ob-tour__slide"
                  :style="{ '--tour-accent': currentSlide.accent }"
                >
                  <div class="ob-tour__preview">
                    <TourIllustration
                      :slide-id="currentSlide.id"
                      :accent="currentSlide.accent"
                    />
                  </div>
                  <div class="ob-tour__copy">
                    <div class="ob-tour__badge">
                      <el-icon :size="16"><component :is="currentSlide.icon" /></el-icon>
                      <span>{{ tourIndex + 1 }} / {{ tourSlides.length }}</span>
                    </div>
                    <h3 class="ob-tour__title">{{ currentSlide.title }}</h3>
                    <p class="ob-tour__desc">{{ currentSlide.desc }}</p>
                    <ul class="ob-tour__points">
                      <li v-for="b in currentSlide.bullets" :key="b">{{ b }}</li>
                    </ul>
                  </div>
                </div>
              </Transition>
            </div>

            <div class="ob-tour-nav" :style="{ '--tour-accent': currentSlide.accent }">
              <button
                type="button"
                class="ob-icon-btn"
                :disabled="tourIndex === 0"
                aria-label="上一页"
                @click="prevTour"
              >
                <el-icon><ArrowLeft /></el-icon>
              </button>
              <div class="ob-tour-dots" role="tablist">
                <button
                  v-for="(s, i) in tourSlides"
                  :key="s.id"
                  type="button"
                  class="ob-tour-dot"
                  :class="{ 'is-active': tourIndex === i }"
                  :aria-label="s.title"
                  @click="goTour(i)"
                />
              </div>
              <button
                type="button"
                class="ob-icon-btn"
                aria-label="下一页"
                @click="nextTour"
              >
                <el-icon><ArrowRight /></el-icon>
              </button>
            </div>
          </section>
        </Transition>
      </main>

      <footer class="ob-footer">
        <button
          v-if="step > 0"
          type="button"
          class="insp-capsule-btn"
          :disabled="stepBusy || finishing"
          @click="prevStep"
        >
          上一步
        </button>
        <div class="ob-footer__spacer" />
        <button
          v-if="step === 1 && !groupsStore.list.length"
          type="button"
          class="insp-capsule-btn"
          :disabled="stepBusy || finishing || groupBusy"
          @click="skipGroupStep"
        >
          暂时跳过
        </button>
        <button
          v-if="step < 2"
          type="button"
          class="insp-capsule-btn insp-capsule-btn--primary"
          :disabled="stepBusy || finishing"
          @click="nextStep"
        >
          {{ stepNextLabel }}
        </button>
        <button
          v-else
          type="button"
          class="insp-capsule-btn insp-capsule-btn--primary"
          :disabled="finishing"
          @click="finish"
        >
          {{ finishing ? '完成中…' : '开始使用' }}
        </button>
      </footer>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  ArrowLeft,
  ArrowRight,
  CircleCheckFilled,
  CollectionTag,
  Compass,
  School,
} from '@element-plus/icons-vue'
import { Api } from '@/api'
import { FEATURE_TOUR_SLIDES } from '@/constants/onboarding'
import { PRESET_SKILLS } from '@/constants/skills'
import { buildOnboardingCompletedPrefs } from '@/utils/onboarding'
import { useGroupsStore } from '@/stores/groups'
import CoTaskLogo from '@/components/common/CoTaskLogo.vue'
import SegmentedControl from '@/components/common/SegmentedControl.vue'
import TourIllustration from '@/components/onboarding/TourIllustration.vue'

const props = defineProps<{
  modelValue: boolean
  initialPrefs?: Record<string, unknown> | null
}>()

const emit = defineEmits<{
  'update:modelValue': [open: boolean]
  completed: []
}>()

const groupsStore = useGroupsStore()

const open = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const stepMeta = [
  { label: '技能', icon: CollectionTag },
  { label: '小组', icon: School },
  { label: '导览', icon: Compass },
]

const heroCopyByStep = [
  {
    title: '完善你的技能标签',
    lead: '选几项擅长方向，便于后续任务分工与推荐负责人。',
  },
  {
    title: '进入课程小组',
    lead: '创建或加入小组后，即可使用项目树、文件与讨论等功能。',
  },
  {
    title: '快速了解主要功能',
    lead: '翻页浏览工作台、项目树、时间轴等。',
  },
]

const step = ref(0)
const stepBusy = ref(false)
const finishing = ref(false)
const heroCopy = computed(() => heroCopyByStep[step.value])

const presetSkills = PRESET_SKILLS
const selectedSkills = ref<string[]>([])
const customSkill = ref('')

const groupMode = ref<'create' | 'join'>('create')
const groupModeOptions = [
  { label: '新建', value: 'create' as const },
  { label: '加入', value: 'join' as const },
]
const groupBusy = ref(false)
const createFormRef = ref<FormInstance>()
const joinFormRef = ref<FormInstance>()
const createForm = reactive({ course_name: '', name: '' })
const joinForm = reactive({ invite_code: '' })
const createRules: FormRules = {
  course_name: [{ required: true, message: '请填写课程名', trigger: 'blur' }],
  name: [{ required: true, message: '请填写小组名', trigger: 'blur' }],
}
const joinRules: FormRules = {
  invite_code: [
    { required: true, message: '请填写邀请码', trigger: 'blur' },
    { len: 8, message: '邀请码为 8 位', trigger: 'blur' },
  ],
}

const tourSlides = FEATURE_TOUR_SLIDES
const tourIndex = ref(0)
const slideAnim = ref('ob-slide-next')
const currentSlide = computed(() => tourSlides[tourIndex.value])

const stepNextLabel = computed(() => {
  if (step.value === 0) return '继续'
  if (step.value === 1) return '继续'
  return '继续'
})

watch(
  () => props.modelValue,
  async (v) => {
    if (!v) return
    step.value = 0
    tourIndex.value = 0
    customSkill.value = ''
    groupMode.value = 'create'
    createForm.course_name = ''
    createForm.name = ''
    joinForm.invite_code = ''
    try {
      const me = await Api.me()
      selectedSkills.value = normalizeSkills(me.skills || [])
    } catch {
      selectedSkills.value = []
    }
    void groupsStore.refresh().catch(() => {})
  },
)

function normalizeSkills(list: string[]) {
  const out: string[] = []
  const seen = new Set<string>()
  for (const raw of list) {
    const s = raw.trim().slice(0, 32)
    if (!s || seen.has(s)) continue
    seen.add(s)
    out.push(s)
    if (out.length >= 30) break
  }
  return out
}

function isSelected(s: string) {
  return selectedSkills.value.includes(s)
}

function toggleSkill(s: string) {
  const i = selectedSkills.value.indexOf(s)
  if (i >= 0) selectedSkills.value.splice(i, 1)
  else selectedSkills.value.push(s)
}

function addCustomSkill() {
  const s = customSkill.value.trim().slice(0, 32)
  if (!s) return
  if (!selectedSkills.value.includes(s)) selectedSkills.value.push(s)
  customSkill.value = ''
}

async function saveSkills() {
  const skills = normalizeSkills(selectedSkills.value)
  if (!skills.length) {
    ElMessage.warning('请至少选择 1 项技能')
    return false
  }
  stepBusy.value = true
  try {
    await Api.setSkills(skills)
    return true
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
    return false
  } finally {
    stepBusy.value = false
  }
}

function onInviteInput(v: string) {
  joinForm.invite_code = v.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 8)
}

async function onCreateGroup() {
  if (!createFormRef.value) return
  const ok = await createFormRef.value.validate().catch(() => false)
  if (!ok) return
  groupBusy.value = true
  try {
    await groupsStore.create({
      course_name: createForm.course_name.trim(),
      name: createForm.name.trim(),
    })
    ElMessage.success('小组已创建')
    createForm.course_name = ''
    createForm.name = ''
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '创建失败')
  } finally {
    groupBusy.value = false
  }
}

async function onJoinGroup() {
  if (!joinFormRef.value) return
  const ok = await joinFormRef.value.validate().catch(() => false)
  if (!ok) return
  groupBusy.value = true
  try {
    const g = await groupsStore.join(joinForm.invite_code)
    ElMessage.success(`已加入 ${g.name}`)
    joinForm.invite_code = ''
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加入失败')
  } finally {
    groupBusy.value = false
  }
}

function validateGroupStep(): boolean {
  if (groupsStore.list.length > 0) return true
  ElMessage.warning('请先创建或加入小组，也可暂时跳过')
  return false
}

async function nextStep() {
  if (step.value === 0) {
    if (!(await saveSkills())) return
    step.value = 1
    return
  }
  if (step.value === 1) {
    if (!validateGroupStep()) return
    step.value = 2
  }
}

function prevStep() {
  if (step.value > 0) step.value -= 1
}

function goTour(i: number) {
  slideAnim.value = i > tourIndex.value ? 'ob-slide-next' : 'ob-slide-prev'
  tourIndex.value = i
}

function prevTour() {
  if (tourIndex.value <= 0) return
  slideAnim.value = 'ob-slide-prev'
  tourIndex.value -= 1
}

function nextTour() {
  slideAnim.value = 'ob-slide-next'
  if (tourIndex.value >= tourSlides.length - 1) {
    tourIndex.value = 0
    return
  }
  tourIndex.value += 1
}

async function persistCompleted() {
  const prefs = buildOnboardingCompletedPrefs(props.initialPrefs)
  await Api.updateMe({ prefs } as any)
}

async function finish() {
  finishing.value = true
  try {
    await persistCompleted()
    open.value = false
    emit('completed')
    ElMessage.success('欢迎加入 CoTask')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
  } finally {
    finishing.value = false
  }
}

async function onSkipAll() {
  try {
    await ElMessageBox.confirm(
      '跳过后可在个人中心补充技能、在我的小组中加入项目。确定跳过？',
      '跳过引导',
      { confirmButtonText: '跳过', cancelButtonText: '继续', type: 'info' },
    )
  } catch {
    return
  }
  finishing.value = true
  try {
    await persistCompleted()
    open.value = false
    emit('completed')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  } finally {
    finishing.value = false
  }
}

function skipGroupStep() {
  step.value = 2
}
</script>

<style lang="scss" scoped>
/* Layout rhythm: 32px horizontal, 24px vertical blocks (8pt grid) */
.ob {
  --ob-px: var(--space-8);
  --ob-py: var(--space-6);
  --ob-gap: var(--space-6);
  --ob-gap-sm: var(--space-4);

  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  color: var(--text-primary);
}

.ob-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--ob-py) var(--ob-px) var(--space-4);
}

.ob-header__end {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.ob-kicker {
  font-size: var(--fs-sm);
  color: var(--text-tertiary);
  font-weight: 500;
  white-space: nowrap;
}

.ob-text-btn {
  border: none;
  background: none;
  padding: var(--space-1) var(--space-2);
  font-size: var(--fs-sm);
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: color 0.15s;

  &:hover:not(:disabled) {
    color: var(--color-primary);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.ob-progress {
  display: flex;
  gap: var(--space-2);
  padding: 0 var(--ob-px) var(--space-4);
}

.ob-progress__seg {
  flex: 1;
  height: 3px;
  border-radius: var(--radius-full);
  background: var(--border-subtle);
  transition: background 0.35s ease;

  &.is-active {
    background: var(--color-primary);
  }

  &.is-done {
    background: color-mix(in srgb, var(--color-primary) 45%, var(--border-subtle));
  }
}

.ob-body {
  flex: 1;
  padding: 0 var(--ob-px) var(--ob-py);
  min-height: 360px;
}

.ob-intro {
  margin-bottom: var(--ob-gap);

  &__title {
    margin: 0 0 var(--space-2);
    font-size: var(--fs-xl);
    font-weight: 600;
    letter-spacing: -0.025em;
    line-height: 1.3;
    color: var(--text-primary);
  }

  &__desc {
    margin: 0;
    font-size: var(--fs-base);
    line-height: 1.55;
    color: var(--text-secondary);
    max-width: 42ch;
  }
}

.ob-step {
  display: flex;
  flex-direction: column;
  gap: var(--ob-gap);
}

.ob-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);

  & + & {
    padding-top: var(--ob-gap);
    border-top: 1px solid var(--border-subtle);
  }

  &__label {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: var(--space-3);
    font-size: var(--fs-sm);
    font-weight: 500;
    color: var(--text-secondary);
  }

  &__meta {
    font-size: var(--fs-sm);
    color: var(--text-tertiary);
    font-weight: 400;
  }
}

.ob-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.ob-chip {
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  border-radius: var(--radius-full);
  padding: 7px 14px;
  font-size: var(--fs-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, color 0.15s;

  &:hover {
    border-color: color-mix(in srgb, var(--color-primary) 40%, var(--border-color));
    color: var(--text-primary);
  }

  &.is-selected {
    border-color: var(--color-primary);
    background: var(--color-primary-light);
    color: var(--color-primary);
    font-weight: 500;
  }

  &__close {
    margin-left: 6px;
    opacity: 0.55;
    font-weight: 400;
  }
}

.ob-field-row {
  display: flex;
  gap: var(--space-3);
  align-items: center;
  padding-top: var(--space-2);

  .el-input {
    flex: 1;
  }
}

.ob-notice {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--fs-sm);
  line-height: 1.45;

  &--ok {
    background: color-mix(in srgb, var(--color-success) 8%, var(--bg-soft));
    color: var(--text-secondary);

    .el-icon {
      color: var(--color-success);
      flex-shrink: 0;
    }
  }
}

.ob-segment {
  width: fit-content;
  max-width: 100%;
  align-self: flex-start;
}

.ob-panel {
  padding: var(--ob-gap);
  background: var(--bg-soft);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
}

.ob-form {
  :deep(.el-form-item) {
    margin-bottom: var(--space-4);
  }

  :deep(.el-form-item__label) {
    padding-bottom: var(--space-2);
    font-size: var(--fs-sm);
    font-weight: 500;
    color: var(--text-secondary);
    line-height: 1.4;
  }

  &__hint {
    margin: var(--space-2) 0 0;
    font-size: var(--fs-sm);
    line-height: 1.45;
    color: var(--text-tertiary);
  }

  :deep(.ob-form-item--invite.is-error) {
    .ob-form__hint {
      display: none;
    }

    .el-form-item__error {
      position: static;
      margin-top: var(--space-2);
      padding-top: 0;
    }
  }

  &__action {
    width: 100%;
    margin-top: var(--space-2);
  }
}

/* Tour */
.ob-step--tour {
  gap: var(--ob-gap-sm);
}

.ob-tour {
  display: flex;
  flex-direction: column;
  gap: var(--ob-gap);
}

.ob-tour__slide {
  display: flex;
  flex-direction: column;
  gap: var(--ob-gap);
}

.ob-tour__preview {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 184px;
  padding: var(--space-1) 0 var(--space-3);
  margin: 0 calc(var(--ob-px) * -0.35);
  border-radius: var(--radius-md);
  background: radial-gradient(
    ellipse 90% 70% at 50% 35%,
    color-mix(in srgb, var(--tour-accent, #3d7eff) 7%, var(--bg-soft)) 0%,
    transparent 72%
  );
}

.ob-tour__copy {
  padding: 0 2px;
}

.ob-tour__badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
  padding: 5px 11px;
  border-radius: var(--radius-full);
  font-size: var(--fs-xs);
  font-weight: 600;
  color: color-mix(in srgb, var(--tour-accent, var(--color-primary)) 72%, var(--text-secondary));
  background: color-mix(in srgb, var(--tour-accent, #3d7eff) 9%, var(--bg-soft));
  border: 1px solid color-mix(in srgb, var(--tour-accent, var(--border-subtle)) 22%, var(--border-subtle));

  .el-icon {
    color: var(--tour-accent, var(--color-primary));
  }
}

.ob-tour__title {
  margin: 0 0 var(--space-2);
  font-size: var(--fs-md);
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.35;
}

.ob-tour__desc {
  margin: 0 0 var(--space-4);
  font-size: var(--fs-sm);
  line-height: 1.55;
  color: var(--text-secondary);
}

.ob-tour__points {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);

  li {
    position: relative;
    padding-left: calc(var(--space-4) + 2px);
    font-size: var(--fs-sm);
    line-height: 1.55;
    color: var(--text-secondary);

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0.62em;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--tour-accent, var(--color-primary));
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--tour-accent, #3d7eff) 14%, transparent);
      opacity: 0.9;
    }
  }
}

.ob-tour-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding-top: var(--space-2);
}

.ob-icon-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  background: var(--bg-card);
  color: var(--text-secondary);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;

  &:hover:not(:disabled) {
    border-color: var(--color-primary);
    color: var(--color-primary);
  }

  &:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }
}

.ob-tour-dots {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ob-tour-dot {
  flex-shrink: 0;
  width: 6px;
  height: 6px;
  padding: 0;
  border: none;
  border-radius: var(--radius-full);
  background: var(--border-color);
  cursor: pointer;
  transition: width 0.2s ease, background 0.2s;

  &.is-active {
    width: 20px;
    background: var(--tour-accent, var(--color-primary));
  }

  &:hover:not(.is-active) {
    background: color-mix(in srgb, var(--tour-accent, var(--border-color)) 35%, var(--border-color));
  }
}

.ob-footer {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) var(--ob-px) var(--ob-py);
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-card);
}

.ob-footer__spacer {
  flex: 1;
}

/* Transitions */
.ob-fade-enter-active,
.ob-fade-leave-active {
  transition: opacity 0.28s ease, transform 0.28s ease;
}

.ob-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.ob-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.ob-slide-next-enter-active,
.ob-slide-next-leave-active,
.ob-slide-prev-enter-active,
.ob-slide-prev-leave-active {
  transition: opacity 0.32s ease, transform 0.32s ease;
}

.ob-slide-next-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.ob-slide-next-leave-to {
  opacity: 0;
  transform: translateX(-16px);
}

.ob-slide-prev-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.ob-slide-prev-leave-to {
  opacity: 0;
  transform: translateX(16px);
}

@media (max-width: 480px) {
  .ob {
    --ob-px: var(--space-5);
    --ob-py: var(--space-5);
  }

  .ob-kicker {
    display: none;
  }

  .ob-tour__preview {
    min-height: 148px;
    margin: 0;
    padding: var(--space-2) 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .ob-fade-enter-active,
  .ob-fade-leave-active,
  .ob-slide-next-enter-active,
  .ob-slide-next-leave-active,
  .ob-slide-prev-enter-active,
  .ob-slide-prev-leave-active {
    transition-duration: 0.12s;
  }

  .ob-fade-enter-from,
  .ob-fade-leave-to,
  .ob-slide-next-enter-from,
  .ob-slide-next-leave-to,
  .ob-slide-prev-enter-from,
  .ob-slide-prev-leave-to {
    transform: none;
  }
}
</style>

<style lang="scss">
.ob-dialog.el-dialog {
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-lg);

  .el-dialog__header {
    display: none;
  }

  .el-dialog__body {
    padding: 0;
  }
}

.el-overlay:has(.ob-dialog) {
  backdrop-filter: blur(6px);
  background-color: rgba(17, 24, 39, 0.32) !important;
}
</style>
