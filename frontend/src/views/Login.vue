<template>
  <div class="login-page">
    <!-- Brand hero (desktop) -->
    <aside class="brand-panel">
      <div class="brand-mesh" aria-hidden="true" />
      <div class="brand-inner">
        <CoTaskLogo size="lg" variant="on-dark" class="brand-logo" />

        <div
          class="brand-carousel"
          @mouseenter="pauseCarousel"
          @mouseleave="resumeCarousel"
        >
          <transition name="hero-fade" mode="out-in">
            <div :key="heroSlides[activeSlide].id" class="carousel-slide">
              <div class="brand-copy">
                <h1 class="brand-headline">
                  {{ heroSlides[activeSlide].headline[0] }}<br />
                  <span class="brand-headline-accent">{{ heroSlides[activeSlide].headline[1] }}</span>
                </h1>
                <p class="brand-lead">{{ heroSlides[activeSlide].lead }}</p>
              </div>

              <div class="brand-showcase" aria-hidden="true">
                <div v-if="heroSlides[activeSlide].id === 'tree'" class="showcase-stack">
                  <div class="showcase-card showcase-card--tree showcase-card--solo">
                    <div class="sc-label">项目树</div>
                    <div class="sc-tree">
                      <div class="sc-node sc-node--root" />
                      <div class="sc-branch">
                        <div class="sc-node" />
                        <div class="sc-node sc-node--active" />
                      </div>
                      <div class="sc-branch sc-branch--short">
                        <div class="sc-node" />
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else-if="heroSlides[activeSlide].id === 'timeline'" class="showcase-stack">
                  <div class="showcase-card showcase-card--timeline showcase-card--solo">
                    <div class="sc-label">本周 DDL</div>
                    <div class="sc-bars">
                      <span class="sc-bar" style="--w: 72%" />
                      <span class="sc-bar sc-bar--warn" style="--w: 45%" />
                      <span class="sc-bar" style="--w: 88%" />
                      <span class="sc-bar" style="--w: 60%" />
                    </div>
                  </div>
                </div>
                <div v-else class="showcase-stack showcase-stack--ai">
                  <div class="showcase-card showcase-card--ai showcase-card--solo">
                    <div class="sc-label">AI 今日建议</div>
                    <p class="sc-ai-line">你今天有 3 项待办，其中 1 项紧急。</p>
                    <p class="sc-ai-focus">
                      <el-icon><MagicStick /></el-icon>
                      重点推进：文献综述初稿
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </transition>

          <div class="carousel-dots" role="tablist" aria-label="功能介绍">
            <button
              v-for="(s, i) in heroSlides"
              :key="s.id"
              type="button"
              class="carousel-dot"
              :class="{ active: activeSlide === i }"
              :aria-label="s.dotLabel"
              :aria-selected="activeSlide === i"
              role="tab"
              @click="goSlide(i)"
            />
          </div>
        </div>

        <div class="brand-foot">
          <div class="brand-copyright">© {{ year }} CoTask</div>
        </div>
      </div>
    </aside>

    <!-- Form -->
    <section class="form-panel">
      <div class="form-wrap">
        <div class="mobile-brand">
          <CoTaskLogo size="md" variant="on-light" />
          <p class="mobile-tagline">AI 赋能的课程小组协作平台</p>
        </div>

        <el-card class="login-card" shadow="never">
          <div class="card-header">
            <div class="card-title">欢迎使用 CoTask</div>
            <div class="card-sub">登录后开始你的小组协作之旅</div>
          </div>

          <SegmentedControl
            v-model="activeTab"
            size="md"
            class="auth-segment"
            :options="authTabOptions"
          />

          <el-form
            v-show="activeTab === 'login'"
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            label-position="top"
            class="auth-form"
            @submit.prevent="onLogin"
          >
                <el-form-item label="手机号 / 学号" prop="account">
                  <el-input
                    v-model="loginForm.account"
                    size="large"
                    placeholder="请输入手机号或学号"
                    clearable
                    :prefix-icon="User"
                  />
                </el-form-item>
                <el-form-item label="密码" prop="password">
                  <el-input
                    v-model="loginForm.password"
                    size="large"
                    type="password"
                    placeholder="请输入密码"
                    show-password
                    :prefix-icon="Lock"
                    @keyup.enter="onLogin"
                  />
                </el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  class="submit-btn"
                  :loading="loginLoading"
                  @click="onLogin"
                >
                  登录
                </el-button>
          </el-form>

          <el-form
            v-show="activeTab === 'register'"
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            label-position="top"
            class="auth-form"
            @submit.prevent="onRegister"
          >
                <el-form-item label="手机号" prop="phone">
                  <el-input
                    v-model="registerForm.phone"
                    size="large"
                    placeholder="11 位手机号"
                    maxlength="11"
                    clearable
                    :prefix-icon="Phone"
                  />
                </el-form-item>
                <el-form-item label="验证码" prop="code">
                  <div class="code-row">
                    <el-input
                      v-model="registerForm.code"
                      size="large"
                      placeholder="6 位验证码"
                      maxlength="6"
                    />
                    <el-button
                      size="large"
                      class="code-btn"
                      :disabled="regSmsCountdown > 0 || smsLoading"
                      :loading="smsLoading"
                      @click="onSendSms('register')"
                    >
                      {{ regSmsCountdown > 0 ? `${regSmsCountdown}s 后重试` : '获取验证码' }}
                    </el-button>
                  </div>
                </el-form-item>
                <el-form-item label="密码" prop="password">
                  <el-input
                    v-model="registerForm.password"
                    size="large"
                    type="password"
                    placeholder="至少 6 位"
                    show-password
                    :prefix-icon="Lock"
                  />
                </el-form-item>
                <el-form-item label="姓名" prop="name">
                  <el-input
                    v-model="registerForm.name"
                    size="large"
                    placeholder="你的真实姓名"
                    :prefix-icon="User"
                  />
                </el-form-item>
                <el-form-item label="学号 (可选)" prop="student_id">
                  <el-input
                    v-model="registerForm.student_id"
                    size="large"
                    placeholder="学号"
                  />
                </el-form-item>
                <el-form-item label="专业 (可选)" prop="major">
                  <el-input
                    v-model="registerForm.major"
                    size="large"
                    placeholder="专业"
                  />
                </el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  class="submit-btn"
                  :loading="registerLoading"
                  @click="onRegister"
                >
                  注册并登录
                </el-button>
          </el-form>

          <el-form
            v-show="activeTab === 'reset'"
            ref="resetFormRef"
            :model="resetForm"
            :rules="resetRules"
            label-position="top"
            class="auth-form"
            @submit.prevent="onReset"
          >
                <el-form-item label="手机号" prop="phone">
                  <el-input
                    v-model="resetForm.phone"
                    size="large"
                    placeholder="11 位手机号"
                    maxlength="11"
                    clearable
                    :prefix-icon="Phone"
                  />
                </el-form-item>
                <el-form-item label="验证码" prop="code">
                  <div class="code-row">
                    <el-input
                      v-model="resetForm.code"
                      size="large"
                      placeholder="6 位验证码"
                      maxlength="6"
                    />
                    <el-button
                      size="large"
                      class="code-btn"
                      :disabled="resetSmsCountdown > 0 || smsLoading"
                      :loading="smsLoading"
                      @click="onSendSms('reset')"
                    >
                      {{ resetSmsCountdown > 0 ? `${resetSmsCountdown}s 后重试` : '获取验证码' }}
                    </el-button>
                  </div>
                </el-form-item>
                <el-form-item label="新密码" prop="new_password">
                  <el-input
                    v-model="resetForm.new_password"
                    size="large"
                    type="password"
                    placeholder="至少 6 位"
                    show-password
                    :prefix-icon="Lock"
                  />
                </el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  class="submit-btn"
                  :loading="resetLoading"
                  @click="onReset"
                >
                  重置密码
                </el-button>
          </el-form>

          <div v-show="activeTab === 'login'" class="guest-login-row">
            <button
              type="button"
              class="guest-login-link"
              :disabled="loginLoading"
              @click="onGuestLogin"
            >
              游客登录
            </button>
          </div>
        </el-card>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Phone, MagicStick } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { Api } from '@/api'
import CoTaskLogo from '@/components/common/CoTaskLogo.vue'
import SegmentedControl from '@/components/common/SegmentedControl.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const year = computed(() => new Date().getFullYear())
const activeTab = ref<'login' | 'register' | 'reset'>('login')

const authTabOptions = [
  { label: '登录', value: 'login' as const },
  { label: '注册', value: 'register' as const },
  { label: '找回密码', value: 'reset' as const },
]

const heroSlides = [
  {
    id: 'tree',
    dotLabel: '项目树',
    headline: ['课程小组协作，', '从任务树开始'],
    lead: '无限层级的任务分解，让每个人都知道自己该做什么。',
  },
  {
    id: 'timeline',
    dotLabel: '时间轴',
    headline: ['DDL 与依赖，', '一图看清'],
    lead: '甘特时间轴对齐截止日与负责人，进度风险提前暴露。',
  },
  {
    id: 'ai',
    dotLabel: 'AI 助手',
    headline: ['AI 智能助手，', '每日帮你推进'],
    lead: '生成任务树、对话编辑结构，并给出今日行动建议。',
  },
] as const

const activeSlide = ref(0)
const CAROUSEL_MS = 4800
let carouselTimer: number | null = null
let carouselPaused = false

function goSlide(index: number) {
  activeSlide.value = index
}

function tickCarousel() {
  activeSlide.value = (activeSlide.value + 1) % heroSlides.length
}

function startCarousel() {
  stopCarousel()
  carouselTimer = window.setInterval(() => {
    if (!carouselPaused) tickCarousel()
  }, CAROUSEL_MS)
}

function stopCarousel() {
  if (carouselTimer) {
    window.clearInterval(carouselTimer)
    carouselTimer = null
  }
}

function pauseCarousel() {
  carouselPaused = true
}

function resumeCarousel() {
  carouselPaused = false
}

onMounted(() => startCarousel())

const phoneRegex = /^1[3-9]\d{9}$/
const validatePhone = (_: unknown, v: string, cb: (e?: Error) => void) => {
  if (!v) return cb(new Error('请输入手机号'))
  if (!phoneRegex.test(v)) return cb(new Error('手机号格式不正确'))
  cb()
}

const loginFormRef = ref<FormInstance>()
const loginForm = reactive({ account: '', password: '' })
const loginRules: FormRules = {
  account: [{ required: true, message: '请输入手机号或学号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}
const loginLoading = ref(false)
async function onLogin() {
  if (!loginFormRef.value) return
  try {
    await loginFormRef.value.validate()
  } catch { return }
  loginLoading.value = true
  try {
    await auth.login(loginForm.account.trim(), loginForm.password)
    ElMessage.success('登录成功')
    const next = (route.query.next as string) || '/dashboard'
    router.push(next)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '登录失败，请检查账号密码')
  } finally {
    loginLoading.value = false
  }
}

const registerFormRef = ref<FormInstance>()
const registerForm = reactive({
  phone: '', code: '', password: '', name: '',
  student_id: '', major: '',
})
const registerRules: FormRules = {
  phone: [{ required: true, validator: validatePhone, trigger: 'blur' }],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: '验证码为 6 位数字', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
}
const registerLoading = ref(false)
async function onRegister() {
  if (!registerFormRef.value) return
  try {
    await registerFormRef.value.validate()
  } catch { return }
  registerLoading.value = true
  try {
    await auth.register({
      phone: registerForm.phone.trim(),
      code: registerForm.code.trim(),
      password: registerForm.password,
      name: registerForm.name.trim(),
      student_id: registerForm.student_id.trim() || undefined,
      major: registerForm.major.trim() || undefined,
    })
    ElMessage.success('注册成功，欢迎加入 CoTask')
    const next = (route.query.next as string) || '/dashboard'
    router.push(next)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '注册失败，请稍后重试')
  } finally {
    registerLoading.value = false
  }
}

const resetFormRef = ref<FormInstance>()
const resetForm = reactive({ phone: '', code: '', new_password: '' })
const resetRules: FormRules = {
  phone: [{ required: true, validator: validatePhone, trigger: 'blur' }],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: '验证码为 6 位数字', trigger: 'blur' },
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
}
const resetLoading = ref(false)
async function onReset() {
  if (!resetFormRef.value) return
  try {
    await resetFormRef.value.validate()
  } catch { return }
  resetLoading.value = true
  try {
    await Api.resetPassword({
      phone: resetForm.phone.trim(),
      code: resetForm.code.trim(),
      new_password: resetForm.new_password,
    })
    ElMessage.success('密码已重置，请登录')
    loginForm.account = resetForm.phone.trim()
    loginForm.password = ''
    activeTab.value = 'login'
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '重置失败，请稍后重试')
  } finally {
    resetLoading.value = false
  }
}

const smsLoading = ref(false)
const regSmsCountdown = ref(0)
const resetSmsCountdown = ref(0)
let regTimer: number | null = null
let resetTimer: number | null = null

function startCountdown(purpose: 'register' | 'reset') {
  const tickRef = purpose === 'register' ? regSmsCountdown : resetSmsCountdown
  tickRef.value = 60
  const id = window.setInterval(() => {
    tickRef.value -= 1
    if (tickRef.value <= 0) {
      window.clearInterval(id)
      if (purpose === 'register') regTimer = null
      else resetTimer = null
    }
  }, 1000)
  if (purpose === 'register') regTimer = id
  else resetTimer = id
}

async function onSendSms(purpose: 'register' | 'reset') {
  const phone = (purpose === 'register' ? registerForm.phone : resetForm.phone).trim()
  if (!phoneRegex.test(phone)) {
    ElMessage.warning('请先输入正确的手机号')
    return
  }
  smsLoading.value = true
  try {
    await Api.sendSms(phone, purpose)
    ElMessage.success('验证码已发送')
    startCountdown(purpose)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '发送失败，请稍后重试')
  } finally {
    smsLoading.value = false
  }
}

onBeforeUnmount(() => {
  stopCarousel()
  if (regTimer) window.clearInterval(regTimer)
  if (resetTimer) window.clearInterval(resetTimer)
})

const DEMO_ACCOUNT = '13800000001'
const DEMO_PASSWORD = 'password123'

async function onGuestLogin() {
  activeTab.value = 'login'
  loginForm.account = DEMO_ACCOUNT
  loginForm.password = DEMO_PASSWORD
  await onLogin()
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr;
  background: var(--bg-page);
}

/* ---------- Brand hero ---------- */
.brand-panel {
  display: none;
  min-width: 0;
  background: linear-gradient(155deg, #1d4ed8 0%, #3d7eff 42%, #6366f1 100%);
  color: var(--text-inverse);
  position: relative;
  overflow: hidden;
}

.brand-mesh {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 70% 55% at 85% 15%, rgba(255, 255, 255, 0.14), transparent 55%),
    radial-gradient(ellipse 50% 45% at 10% 85%, rgba(255, 255, 255, 0.08), transparent 50%);
  pointer-events: none;
}

.brand-inner {
  position: relative;
  z-index: 1;
  height: 100%;
  min-height: 100vh;
  padding: clamp(var(--space-8), 5vh, var(--space-10)) var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  box-sizing: border-box;
}

.brand-carousel {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: min(400px, 52vh);
}

.carousel-slide {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.hero-fade-enter-active,
.hero-fade-leave-active {
  transition: opacity 0.45s ease, transform 0.45s ease;
}

@media (prefers-reduced-motion: reduce) {
  .hero-fade-enter-active,
  .hero-fade-leave-active {
    transition: opacity 0.2s ease;
  }

  .hero-fade-enter-from,
  .hero-fade-leave-to {
    transform: none;
  }
}

.hero-fade-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.hero-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.carousel-dots {
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-6);
}

.carousel-dot {
  width: 8px;
  height: 8px;
  padding: 0;
  border: none;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.28);
  cursor: pointer;
  transition: width 0.25s ease, background 0.25s ease;

  &.active {
    width: 22px;
    background: rgba(255, 255, 255, 0.92);
  }

  &:hover:not(.active) {
    background: rgba(255, 255, 255, 0.5);
  }
}

.brand-copy {
  max-width: 420px;
}

.brand-headline {
  margin: 0 0 var(--space-4);
  font-size: clamp(28px, 3.2vw, 36px);
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.03em;
}

.brand-headline-accent {
  background: linear-gradient(90deg, #fff 0%, rgba(255, 255, 255, 0.75) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.brand-lead {
  margin: 0;
  font-size: var(--fs-md);
  line-height: 1.65;
  color: rgba(255, 255, 255, 0.82);
  max-width: 36em;
}

.brand-showcase {
  display: flex;
  align-items: center;
  min-height: 200px;
}

.showcase-stack {
  position: relative;
  width: 100%;
  max-width: 400px;
  min-height: 200px;
}

.showcase-card {
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.12);
}

.showcase-card--solo {
  width: 100%;
}

.showcase-card--ai {
  .sc-ai-line {
    margin: 0 0 var(--space-3);
    font-size: var(--fs-sm);
    line-height: 1.55;
    opacity: 0.9;
  }

  .sc-ai-focus {
    margin: 0;
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--fs-sm);
    font-weight: 600;
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-sm);
    background: rgba(255, 255, 255, 0.14);
  }
}

.sc-label {
  font-size: var(--fs-xs);
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  opacity: 0.75;
  margin-bottom: var(--space-3);
}

.sc-tree {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding-left: var(--space-2);
  border-left: 2px solid rgba(255, 255, 255, 0.25);
}

.sc-branch {
  display: flex;
  gap: var(--space-2);
  padding-left: var(--space-3);

  &--short {
    padding-left: var(--space-2);
  }
}

.sc-node {
  height: 8px;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.35);
  flex: 1;
  min-width: 24px;

  &--root {
    max-width: 100%;
    height: 10px;
    background: rgba(255, 255, 255, 0.5);
  }

  &--active {
    background: #fff;
    box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.2);
  }
}

.sc-bars {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.sc-bar {
  display: block;
  height: 8px;
  width: var(--w, 50%);
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.45);

  &--warn {
    background: rgba(251, 191, 36, 0.85);
  }
}

.brand-foot {
  flex-shrink: 0;
}

.brand-copyright {
  font-size: var(--fs-sm);
  color: rgba(255, 255, 255, 0.5);
}

@media (min-width: 960px) {
  .login-page {
    grid-template-columns: 1fr 1fr;
  }

  .brand-panel {
    display: flex;
  }
}

/* ---------- Form panel — centered in viewport ---------- */
.form-panel {
  min-width: 0;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-8) clamp(var(--space-6), 6vw, var(--space-10));
  box-sizing: border-box;
}

.form-wrap {
  width: 100%;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: var(--space-6);
  margin: auto;
}

.mobile-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  text-align: center;
}

.mobile-tagline {
  margin: 0;
  font-size: var(--fs-sm);
  color: var(--text-secondary);
}

@media (min-width: 960px) {
  .mobile-brand { display: none; }
}

.login-card {
  width: 100%;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  box-shadow: var(--shadow-lg);

  :deep(.el-card__body) { padding: var(--space-8); }
}

.card-header {
  margin-bottom: var(--space-5);
}

.card-title {
  font-size: var(--fs-2xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-1) 0;
  letter-spacing: -0.3px;
}

.card-sub {
  font-size: var(--fs-base);
  color: var(--text-secondary);
  margin: 0;
}

.auth-segment {
  width: 100%;
  margin-bottom: var(--space-5);

  :deep(.segmented-control) {
    display: flex;
    width: 100%;
  }

  :deep(.segmented-control__btn) {
    flex: 1;
    justify-content: center;
    padding-left: var(--space-2);
    padding-right: var(--space-2);
  }
}

.auth-form {
  width: 100%;
}

.submit-btn {
  width: 100%;
  margin-top: var(--space-2);
  height: 40px;
  font-size: var(--fs-base);
  font-weight: 600;
}

.code-row {
  display: flex;
  gap: var(--space-2);
  width: 100%;

  .el-input { flex: 1; }

  .code-btn {
    flex-shrink: 0;
    min-width: 120px;
    font-size: var(--fs-sm);
  }
}

.guest-login-row {
  display: flex;
  justify-content: center;
  margin-top: var(--space-3);
}

.guest-login-link {
  border: none;
  background: none;
  padding: var(--space-1) var(--space-2);
  font-size: var(--fs-sm);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: color 120ms ease;

  &:hover:not(:disabled) {
    color: var(--color-primary);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

@media (max-width: 480px) {
  .login-card :deep(.el-card__body) { padding: var(--space-5) var(--space-4); }
  .card-title { font-size: var(--fs-xl); }
  .form-panel { padding: var(--space-4) var(--space-3); }
}
</style>
