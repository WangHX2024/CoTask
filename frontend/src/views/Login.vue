<template>
  <div class="login-page">
    <!-- Brand panel (≥ 992px) -->
    <aside class="brand-panel">
      <div class="brand-inner">
        <div class="brand-logo">
          <span class="brand-mark">Co</span>
          <span class="brand-name">Task</span>
        </div>
        <div class="brand-tagline">AI 赋能的课程小组协作平台</div>
        <ul class="feature-list">
          <li>
            <el-icon><Promotion /></el-icon>
            <div>
              <div class="f-title">递归项目树</div>
              <div class="f-desc">任务无限分解，结构清晰</div>
            </div>
          </li>
          <li>
            <el-icon><Calendar /></el-icon>
            <div>
              <div class="f-title">甘特图时间轴</div>
              <div class="f-desc">DDL、依赖、人员一目了然</div>
            </div>
          </li>
          <li>
            <el-icon><MagicStick /></el-icon>
            <div>
              <div class="f-title">灵感广场</div>
              <div class="f-desc">优秀模板一键导入</div>
            </div>
          </li>
        </ul>
        <div class="brand-footer">© {{ year }} CoTask · 让小组协作更轻松</div>
      </div>
    </aside>

    <!-- Form panel -->
    <section class="form-panel">
      <el-card class="login-card" shadow="never">
        <div class="card-header">
          <div class="card-title">欢迎使用 CoTask</div>
          <div class="card-sub">登录后开始你的小组协作之旅</div>
        </div>

        <el-tabs v-model="activeTab" class="login-tabs">
          <!-- 登录 -->
          <el-tab-pane label="登录" name="login">
            <el-form
              ref="loginFormRef"
              :model="loginForm"
              :rules="loginRules"
              label-position="top"
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
          </el-tab-pane>

          <!-- 注册 -->
          <el-tab-pane label="注册" name="register">
            <el-form
              ref="registerFormRef"
              :model="registerForm"
              :rules="registerRules"
              label-position="top"
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
          </el-tab-pane>

          <!-- 找回密码 -->
          <el-tab-pane label="找回密码" name="reset">
            <el-form
              ref="resetFormRef"
              :model="resetForm"
              :rules="resetRules"
              label-position="top"
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
          </el-tab-pane>
        </el-tabs>

        <div class="demo-tip">
          <span>演示账号: <code>13800000001</code> / <code>password123</code></span>
          <el-link type="primary" :underline="false" @click="fillDemo">一键填入</el-link>
        </div>
      </el-card>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onBeforeUnmount, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  User, Lock, Phone, Promotion, Calendar, MagicStick,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { Api } from '@/api'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const year = computed(() => new Date().getFullYear())
const activeTab = ref<'login' | 'register' | 'reset'>('login')

// ---------- helpers ----------
const phoneRegex = /^1[3-9]\d{9}$/
const validatePhone = (_: unknown, v: string, cb: (e?: Error) => void) => {
  if (!v) return cb(new Error('请输入手机号'))
  if (!phoneRegex.test(v)) return cb(new Error('手机号格式不正确'))
  cb()
}

// ---------- login ----------
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

// ---------- register ----------
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

// ---------- reset ----------
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

// ---------- sms ----------
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
  if (regTimer) window.clearInterval(regTimer)
  if (resetTimer) window.clearInterval(resetTimer)
})

// ---------- demo ----------
function fillDemo() {
  activeTab.value = 'login'
  loginForm.account = '13800000001'
  loginForm.password = 'password123'
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  background: var(--bg-page);
}

/* Brand panel */
.brand-panel {
  display: none;
  flex: 1 1 50%;
  max-width: 560px;
  background: linear-gradient(135deg, #3D7EFF 0%, #5b9dff 100%);
  color: #fff;
  position: relative;
  overflow: hidden;

  &::before, &::after {
    content: '';
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
  }
  &::before { width: 320px; height: 320px; top: -80px; right: -80px; }
  &::after  { width: 240px; height: 240px; bottom: -60px; left: -60px; }
}
.brand-inner {
  position: relative;
  z-index: 1;
  padding: 64px 56px;
  display: flex;
  flex-direction: column;
  height: 100%;
}
.brand-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 16px;
}
.brand-mark {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  padding: 4px 10px;
  backdrop-filter: blur(4px);
}
.brand-tagline {
  font-size: 18px;
  opacity: 0.9;
  margin-bottom: 48px;
}
.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 24px;

  li {
    display: flex;
    align-items: flex-start;
    gap: 14px;

    .el-icon {
      font-size: 22px;
      background: rgba(255, 255, 255, 0.18);
      border-radius: 8px;
      padding: 8px;
      flex-shrink: 0;
    }
    .f-title { font-size: 16px; font-weight: 600; margin-bottom: 4px; }
    .f-desc  { font-size: 13px; opacity: 0.85; }
  }
}
.brand-footer {
  margin-top: auto;
  font-size: 12px;
  opacity: 0.7;
}

@media (min-width: 992px) {
  .brand-panel { display: block; }
}

/* Form panel */
.form-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
}
.login-card {
  width: 100%;
  max-width: 420px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  background: var(--bg-card);

  :deep(.el-card__body) { padding: 32px; }
}
.card-header { margin-bottom: 16px; }
.card-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
}
.card-sub {
  font-size: 13px;
  color: var(--text-secondary);
}
.login-tabs {
  :deep(.el-tabs__header) { margin-bottom: 16px; }
  :deep(.el-tabs__nav-wrap::after) { background: var(--border-color); }
}
.submit-btn {
  width: 100%;
  margin-top: 8px;
}
.code-row {
  display: flex;
  gap: 8px;
  width: 100%;

  .el-input { flex: 1; }
  .code-btn {
    flex-shrink: 0;
    min-width: 128px;
  }
}
.demo-tip {
  margin-top: 20px;
  padding: 10px 12px;
  background: var(--bg-soft);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;

  code {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 1px 6px;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    color: var(--text-primary);
  }
}

@media (max-width: 480px) {
  .login-card :deep(.el-card__body) { padding: 24px 20px; }
  .card-title { font-size: 20px; }
}
</style>
