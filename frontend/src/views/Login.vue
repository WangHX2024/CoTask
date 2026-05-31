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
                <span class="brand-feature-pill">{{ heroSlides[activeSlide].dotLabel }}</span>
                <LoginHeroShowcase :slide-id="heroSlides[activeSlide].id" />
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
          <p class="mobile-tagline">课程小组协作与项目管理</p>
        </div>

        <el-card class="login-card" shadow="never">
          <div class="card-header">
            <div class="card-title">欢迎使用 CoTask</div>
            <div class="card-sub">登录后创建或加入小组，开始协作管理课程项目</div>
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
                      placeholder="4 位验证码"
                      maxlength="4"
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
                      placeholder="4 位验证码"
                      maxlength="4"
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
import { User, Lock, Phone } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { Api } from '@/api'
import { LOGIN_HERO_SLIDES } from '@/constants/loginHero'
import CoTaskLogo from '@/components/common/CoTaskLogo.vue'
import SegmentedControl from '@/components/common/SegmentedControl.vue'
import LoginHeroShowcase from '@/components/auth/LoginHeroShowcase.vue'

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

const heroSlides = LOGIN_HERO_SLIDES

const activeSlide = ref(0)
const CAROUSEL_MS = 5200
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
    { pattern: /^\d{4}$/, message: '验证码为 4 位数字', trigger: 'blur' },
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
    { pattern: /^\d{4}$/, message: '验证码为 4 位数字', trigger: 'blur' },
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
    radial-gradient(ellipse 50% 45% at 10% 85%, rgba(255, 255, 255, 0.08), transparent 50%),
    radial-gradient(circle at 72% 68%, rgba(255, 255, 255, 0.06) 0%, transparent 28%);
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
  gap: clamp(var(--space-5), 3vh, var(--space-7));
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
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-3);
  min-height: 240px;
}

.brand-feature-pill {
  display: inline-flex;
  align-items: center;
  padding: 5px 12px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: rgba(255, 255, 255, 0.92);
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.08);
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
