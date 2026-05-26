<template>
  <div class="profile-page page insp-sub-page">
    <header class="insp-page-header">
      <div class="insp-page-header__lead">
        <div class="page-header-text">
          <h1 class="page-title">个人中心</h1>
          <p class="page-desc">管理你的资料、技能标签与账户安全</p>
        </div>
      </div>
    </header>

    <SegmentedControl
      v-model="activeTab"
      size="md"
      class="profile-nav"
      :options="tabOptions"
    />

    <!-- 基础信息 -->
    <div v-show="activeTab === 'basic'" class="profile-pane">
      <div v-if="profile" class="insp-panel profile-panel">
        <div class="profile-hero">
          <el-avatar :src="profileForm.avatar_url || undefined" :size="72">
            {{ (profileForm.name || '?').slice(0, 1) }}
          </el-avatar>
          <div class="profile-hero__meta">
            <div class="profile-hero__name">{{ profileForm.name || '未设置姓名' }}</div>
            <div class="muted tiny">
              {{ profileForm.student_id || '—' }}
              <span v-if="profileForm.major"> · {{ profileForm.major }}</span>
            </div>
          </div>
        </div>

        <el-form
          ref="basicFormRef"
          :model="profileForm"
          label-position="top"
          class="profile-form"
        >
          <el-form-item label="头像地址">
            <el-input
              v-model="profileForm.avatar_url"
              class="insp-capsule-input"
              placeholder="头像图片链接（可选）"
              clearable
            />
          </el-form-item>

          <div class="form-grid">
            <el-form-item label="姓名">
              <el-input v-model="profileForm.name" class="insp-capsule-input" maxlength="32" />
            </el-form-item>
            <el-form-item label="学号">
              <el-input v-model="profileForm.student_id" class="insp-capsule-input" disabled />
            </el-form-item>
            <el-form-item label="手机号">
              <el-input v-model="profileForm.phone" class="insp-capsule-input" disabled />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input
                v-model="profileForm.email"
                class="insp-capsule-input"
                type="email"
                placeholder="example@school.edu"
              />
            </el-form-item>
            <el-form-item label="专业">
              <el-input v-model="profileForm.major" class="insp-capsule-input" />
            </el-form-item>
            <el-form-item label="年级">
              <el-input
                v-model="profileForm.grade"
                class="insp-capsule-input"
                placeholder="如：2023 级"
              />
            </el-form-item>
          </div>

          <el-form-item label="个人简介">
            <el-input
              v-model="profileForm.bio"
              class="insp-capsule-textarea"
              type="textarea"
              :rows="3"
              maxlength="200"
              show-word-limit
              placeholder="一句话介绍自己"
            />
          </el-form-item>

          <div class="panel-footer">
            <button
              type="button"
              class="insp-capsule-btn insp-capsule-btn--primary"
              :disabled="savingBasic"
              @click="saveBasic"
            >
              {{ savingBasic ? '保存中…' : '保存修改' }}
            </button>
          </div>
        </el-form>
      </div>
      <div v-else class="insp-panel profile-panel">
        <el-skeleton :rows="8" animated />
      </div>
    </div>

    <!-- 技能标签 -->
    <div v-show="activeTab === 'skills'" class="profile-pane">
      <div v-if="profile" class="insp-panel profile-panel">
        <div class="profile-hint">
          <el-icon><InfoFilled /></el-icon>
          <span>AI 辅助分配任务时会参考技能标签</span>
          <span v-if="skillsSaving" class="profile-hint__status muted tiny">保存中…</span>
          <span v-else-if="skillsSavedHint" class="profile-hint__status muted tiny">已保存</span>
        </div>

        <section class="profile-block">
          <h2 class="profile-block__title">已选技能</h2>
          <div v-if="selectedSkills.length" class="skill-chips">
            <button
              v-for="s in selectedSkills"
              :key="s"
              type="button"
              class="skill-chip skill-chip--selected"
              @click="toggleSkill(s)"
            >
              {{ s }}
              <span class="skill-chip__x" aria-hidden="true">×</span>
            </button>
          </div>
          <p v-else class="muted tiny">尚未选择技能，可从下方常用标签中添加</p>
        </section>

        <section class="profile-block">
          <h2 class="profile-block__title">常用技能</h2>
          <div class="skill-chips">
            <button
              v-for="s in presetSkills"
              :key="s"
              type="button"
              class="skill-chip"
              :class="{ 'skill-chip--selected': isSelected(s) }"
              @click="toggleSkill(s)"
            >
              {{ isSelected(s) ? '✓ ' : '+ ' }}{{ s }}
            </button>
          </div>
        </section>

        <section class="profile-block">
          <h2 class="profile-block__title">自定义标签</h2>
          <div class="custom-skill-row">
            <el-input
              v-model="customInput"
              class="insp-capsule-input custom-skill-input"
              placeholder="输入技能名，回车添加"
              maxlength="32"
              @keydown.enter.prevent="addCustom"
            />
            <button type="button" class="insp-capsule-btn" @click="addCustom">添加</button>
          </div>
        </section>
      </div>
      <div v-else class="insp-panel profile-panel">
        <el-skeleton :rows="6" animated />
      </div>
    </div>

    <!-- 通知偏好 -->
    <div v-show="activeTab === 'notify'" class="profile-pane">
      <div v-if="profile" class="insp-panel profile-panel profile-panel--list">
        <div class="settings-row">
          <div>
            <div class="settings-row__label">邮件通知</div>
            <div class="muted tiny">通过邮件接收重要任务和小组提醒</div>
          </div>
          <el-switch
            v-model="notifyForm.email"
            :disabled="savingNotify"
            @change="saveNotify"
          />
        </div>
        <div class="settings-row">
          <div>
            <div class="settings-row__label">站内通知</div>
            <div class="muted tiny">在 CoTask 内显示通知小红点和清单</div>
          </div>
          <el-switch
            v-model="notifyForm.inapp"
            :disabled="savingNotify"
            @change="saveNotify"
          />
        </div>
        <div class="settings-row">
          <div>
            <div class="settings-row__label">微信通知</div>
            <div class="muted tiny">通过微信公众号推送（需绑定微信）</div>
          </div>
          <el-switch
            v-model="notifyForm.wechat"
            :disabled="savingNotify"
            @change="saveNotify"
          />
        </div>
      </div>
      <div v-else class="insp-panel profile-panel">
        <el-skeleton :rows="3" animated />
      </div>
    </div>

    <!-- 账户安全 -->
    <div v-show="activeTab === 'security'" class="profile-pane">
      <div class="insp-panel profile-panel">
        <section class="profile-block">
          <h2 class="profile-block__title">修改密码</h2>
          <el-form
            ref="pwdFormRef"
            :model="pwdForm"
            :rules="pwdRules"
            label-position="top"
            class="profile-form profile-form--narrow"
          >
            <el-form-item label="当前密码" prop="current">
              <el-input
                v-model="pwdForm.current"
                class="insp-capsule-input"
                type="password"
                show-password
              />
            </el-form-item>
            <el-form-item label="新密码" prop="next">
              <el-input
                v-model="pwdForm.next"
                class="insp-capsule-input"
                type="password"
                show-password
              />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirm">
              <el-input
                v-model="pwdForm.confirm"
                class="insp-capsule-input"
                type="password"
                show-password
              />
            </el-form-item>
            <button
              type="button"
              class="insp-capsule-btn insp-capsule-btn--primary"
              :disabled="savingPwd"
              @click="savePwd"
            >
              {{ savingPwd ? '提交中…' : '修改密码' }}
            </button>
          </el-form>
        </section>

        <section class="profile-block profile-block--divider">
          <h2 class="profile-block__title">第三方账户</h2>
          <div class="settings-row settings-row--inline">
            <div>
              <div class="settings-row__label">微信</div>
              <div class="muted tiny">绑定微信以使用扫码登录和微信通知</div>
            </div>
            <button type="button" class="insp-capsule-btn" @click="onBindWechat">绑定微信</button>
          </div>
        </section>

        <section class="profile-block profile-block--divider profile-block--danger">
          <h2 class="profile-block__title profile-block__title--danger">危险操作</h2>
          <div class="settings-row settings-row--inline">
            <div>
              <div class="settings-row__label">注销账号</div>
              <div class="muted tiny">注销后所有数据将被永久删除，无法恢复</div>
            </div>
            <button
              type="button"
              class="insp-capsule-btn insp-capsule-btn--danger"
              @click="onDestroy"
            >
              注销账号
            </button>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import { Api, type UserProfile } from '@/api'
import { useAuthStore } from '@/stores/auth'
import SegmentedControl from '@/components/common/SegmentedControl.vue'

const auth = useAuthStore()

type ProfileTab = 'basic' | 'skills' | 'notify' | 'security'

const activeTab = ref<ProfileTab>('basic')
const tabOptions = [
  { label: '基础信息', value: 'basic' as const },
  { label: '技能标签', value: 'skills' as const },
  { label: '通知偏好', value: 'notify' as const },
  { label: '账户安全', value: 'security' as const },
]

const profile = ref<UserProfile | null>(null)
const profileForm = reactive({
  name: '',
  student_id: '',
  phone: '',
  email: '',
  major: '',
  grade: '',
  bio: '',
  avatar_url: '',
})
const savingBasic = ref(false)
const basicFormRef = ref<FormInstance>()

const skillsSavePaused = ref(true)
const skillsSaving = ref(false)
const skillsSavedHint = ref(false)
let skillsTimer: ReturnType<typeof setTimeout> | null = null
let skillsSavedTimer: ReturnType<typeof setTimeout> | null = null
let skillsRequestId = 0

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

function skillsKey(list: string[]) {
  return normalizeSkills(list).join('\0')
}

function applyProfile(p: UserProfile) {
  skillsSavePaused.value = true
  profile.value = p
  profileForm.name = p.name || ''
  profileForm.student_id = p.student_id || ''
  profileForm.phone = p.phone || ''
  profileForm.email = p.email || ''
  profileForm.major = p.major || ''
  profileForm.grade = p.grade || ''
  profileForm.bio = p.bio || ''
  profileForm.avatar_url = p.avatar_url || ''
  selectedSkills.value = normalizeSkills(p.skills || [])

  const np = (p.prefs?.notify || {}) as Record<string, unknown>
  notifyForm.email = !!np.email
  notifyForm.inapp = np.inapp !== false
  notifyForm.wechat = !!np.wechat

  nextTick(() => {
    skillsSavePaused.value = false
  })
}

async function loadProfile() {
  try {
    const me = await Api.me()
    applyProfile(me)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载资料失败')
  }
}

async function saveBasic() {
  savingBasic.value = true
  try {
    const updated = await Api.updateMe({
      name: profileForm.name.trim(),
      email: profileForm.email.trim() || undefined,
      major: profileForm.major.trim() || undefined,
      grade: profileForm.grade.trim() || undefined,
      bio: profileForm.bio.trim() || undefined,
      avatar_url: profileForm.avatar_url.trim() || undefined,
    } as Partial<UserProfile>)
    applyProfile(updated)
    auth.setUser({
      id: updated.id,
      name: updated.name,
      phone: updated.phone,
      student_id: updated.student_id,
      avatar_url: updated.avatar_url,
      major: updated.major,
      grade: updated.grade,
      bio: updated.bio,
      contribution: updated.contribution,
    })
    ElMessage.success('资料已更新')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
  } finally {
    savingBasic.value = false
  }
}

const presetSkills = [
  'PPT制作', '演讲', '写作', '文献综述', '数据分析',
  '摄影', '设计', '视频剪辑', '编程', '项目统筹', '翻译',
]
const selectedSkills = ref<string[]>([])
const customInput = ref('')

function isSelected(s: string) {
  return selectedSkills.value.includes(s)
}

function toggleSkill(s: string) {
  const idx = selectedSkills.value.indexOf(s)
  if (idx >= 0) selectedSkills.value.splice(idx, 1)
  else selectedSkills.value.push(s)
}

function addCustom() {
  const v = customInput.value.trim().slice(0, 32)
  if (!v) return
  if (selectedSkills.value.includes(v)) {
    ElMessage.info('已存在该标签')
    return
  }
  selectedSkills.value.push(v)
  customInput.value = ''
}

async function persistSkills(list: string[]) {
  const reqId = ++skillsRequestId
  const cleaned = normalizeSkills(list)
  skillsSaving.value = true
  skillsSavedHint.value = false

  try {
    const res = await Api.setSkills(cleaned)
    if (reqId !== skillsRequestId) return

    const server = normalizeSkills(res.skills || [])
    if (skillsKey(server) !== skillsKey(selectedSkills.value)) {
      skillsSavePaused.value = true
      selectedSkills.value = [...server]
      await nextTick()
      skillsSavePaused.value = false
    }

    skillsSavedHint.value = true
    if (skillsSavedTimer) clearTimeout(skillsSavedTimer)
    skillsSavedTimer = setTimeout(() => {
      skillsSavedHint.value = false
    }, 2000)
  } finally {
    if (reqId === skillsRequestId) {
      skillsSaving.value = false
    }
  }
}

watch(selectedSkills, (next) => {
  if (skillsSavePaused.value) return
  if (skillsTimer) clearTimeout(skillsTimer)
  skillsTimer = setTimeout(() => {
    void (async () => {
      try {
        await persistSkills([...next])
      } catch (e: any) {
        if (skillsRequestId > 0) {
          ElMessage.error(e?.response?.data?.message || '保存失败')
        }
      }
    })()
  }, 500)
}, { deep: true })

const notifyForm = reactive({
  email: true,
  inapp: true,
  wechat: false,
})
const savingNotify = ref(false)
let notifyTimer: ReturnType<typeof setTimeout> | null = null

function saveNotify() {
  if (notifyTimer) clearTimeout(notifyTimer)
  notifyTimer = setTimeout(async () => {
    savingNotify.value = true
    try {
      const oldPrefs = (profile.value?.prefs || {}) as Record<string, unknown>
      const updated = await Api.updateMe({
        prefs: { ...oldPrefs, notify: { ...notifyForm } },
      } as Partial<UserProfile>)
      profile.value = updated
      ElMessage.success('通知偏好已保存')
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.message || '保存失败')
    } finally {
      savingNotify.value = false
    }
  }, 300)
}

const pwdForm = reactive({ current: '', next: '', confirm: '' })
const savingPwd = ref(false)
const pwdFormRef = ref<FormInstance>()

const pwdRules: FormRules = {
  current: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  next: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码至少 8 位', trigger: 'blur' },
  ],
  confirm: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_r, v, cb) =>
        v === pwdForm.next ? cb() : cb(new Error('两次输入不一致')),
      trigger: 'blur',
    },
  ],
}

async function savePwd() {
  if (!pwdFormRef.value) return
  const ok = await pwdFormRef.value.validate().catch(() => false)
  if (!ok) return
  savingPwd.value = true
  try {
    await Api.changePassword(pwdForm.current, pwdForm.next)
    ElMessage.success('密码已更新')
    pwdForm.current = ''
    pwdForm.next = ''
    pwdForm.confirm = ''
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '修改失败')
  } finally {
    savingPwd.value = false
  }
}

function onBindWechat() {
  ElMessage.info('敬请期待')
}

function onDestroy() {
  ElMessage.info('敬请期待')
}

onMounted(() => {
  void loadProfile()
})
</script>

<style lang="scss">
@use '@/styles/inspiration-pages.scss';
</style>

<style lang="scss" scoped>
.profile-nav {
  width: fit-content;
  max-width: 100%;
}

.profile-pane {
  min-width: 0;
}

.profile-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.profile-panel--list {
  gap: 0;
}

.profile-hero {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--border-subtle);
}

.profile-hero__name {
  font-size: var(--fs-lg);
  font-weight: 700;
  color: var(--text-primary);
}

.profile-hero__meta {
  min-width: 0;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);

  :deep(.el-form-item__label) {
    font-weight: 600;
    color: var(--text-primary);
  }

  &--narrow {
    max-width: 400px;
  }
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 var(--space-4);
}

.panel-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: var(--space-4);
  border-top: 1px solid var(--border-subtle);
}

.profile-hint {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-radius: var(--radius-lg);
  font-size: var(--fs-sm);
  border: 1px solid color-mix(in srgb, var(--color-primary) 25%, transparent);

  .el-icon {
    font-size: 16px;
    flex-shrink: 0;
  }
}

.profile-hint__status {
  margin-left: auto;
}

.profile-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);

  &--divider {
    padding-top: var(--space-5);
    border-top: 1px solid var(--border-subtle);
  }

  &--danger .profile-block__title--danger {
    color: var(--color-danger);
  }
}

.profile-block__title {
  margin: 0;
  font-size: var(--fs-base);
  font-weight: 600;
  color: var(--text-primary);
}

.skill-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.skill-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 6px 14px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: var(--fs-sm);
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition:
    background 120ms ease,
    color 120ms ease,
    border-color 120ms ease;

  &:hover {
    border-color: var(--color-primary);
    color: var(--color-primary);
  }

  &--selected {
    background: var(--color-primary-light);
    border-color: transparent;
    color: var(--color-primary);
    font-weight: 600;
  }
}

.skill-chip__x {
  font-size: 14px;
  line-height: 1;
  opacity: 0.7;
}

.custom-skill-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  align-items: center;
}

.custom-skill-input {
  flex: 1;
  min-width: 200px;
  max-width: 360px;
}

.settings-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4) 0;
  border-bottom: 1px solid var(--border-subtle);

  &:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }

  &:first-child {
    padding-top: 0;
  }

  &--inline {
    align-items: flex-start;
  }
}

.settings-row__label {
  font-size: var(--fs-base);
  font-weight: 500;
  color: var(--text-primary);
}

@media (max-width: 720px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .profile-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .profile-hint__status {
    margin-left: 0;
    width: 100%;
  }
}
</style>
