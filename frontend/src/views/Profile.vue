<template>
  <div class="profile-page">
    <div class="page-head">
      <h1 class="page-title">个人中心</h1>
      <div class="muted tiny">管理你的资料、技能、贡献和账户设置</div>
    </div>

    <el-tabs v-model="activeTab" class="profile-tabs">
      <!-- 1. 基础信息 -->
      <el-tab-pane label="基础信息" name="basic">
        <div class="card pane-card" v-if="profile">
          <el-form
            ref="basicFormRef"
            :model="profileForm"
            label-position="top"
            class="basic-form"
          >
            <div class="avatar-row">
              <el-avatar :src="profileForm.avatar_url || undefined" :size="80">
                {{ (profileForm.name || '?').slice(0, 1) }}
              </el-avatar>
              <div class="avatar-fields">
                <el-form-item label="头像地址">
                  <el-input
                    v-model="profileForm.avatar_url"
                    placeholder="头像 URL（粘贴图片链接）"
                  />
                </el-form-item>
              </div>
            </div>

            <div class="form-grid">
              <el-form-item label="姓名" prop="name">
                <el-input v-model="profileForm.name" maxlength="32" />
              </el-form-item>
              <el-form-item label="学号">
                <el-input v-model="profileForm.student_id" disabled />
              </el-form-item>
              <el-form-item label="手机号">
                <el-input v-model="profileForm.phone" disabled />
              </el-form-item>
              <el-form-item label="邮箱">
                <el-input
                  v-model="profileForm.email"
                  type="email"
                  placeholder="example@school.edu"
                />
              </el-form-item>
              <el-form-item label="专业">
                <el-input v-model="profileForm.major" />
              </el-form-item>
              <el-form-item label="年级">
                <el-input
                  v-model="profileForm.grade"
                  placeholder="如：2023 级"
                />
              </el-form-item>
            </div>

            <el-form-item label="个人简介">
              <el-input
                v-model="profileForm.bio"
                type="textarea"
                :rows="3"
                maxlength="200"
                show-word-limit
                placeholder="一句话介绍自己"
              />
            </el-form-item>

            <div class="form-footer">
              <el-button
                type="primary"
                :loading="savingBasic"
                @click="saveBasic"
              >保存修改</el-button>
            </div>
          </el-form>
        </div>
        <el-skeleton v-else :rows="6" animated />
      </el-tab-pane>

      <!-- 2. 技能标签 -->
      <el-tab-pane label="技能标签" name="skills">
        <div class="card pane-card" v-if="profile">
          <div class="ai-note">
            <el-icon class="info-icon"><InfoFilled /></el-icon>
            AI 在帮组长分配任务时会参考你的标签
          </div>

          <div class="skill-section">
            <div class="section-label">已选技能</div>
            <div v-if="selectedSkills.length" class="skill-row">
              <el-tag
                v-for="s in selectedSkills"
                :key="s"
                closable
                effect="dark"
                class="skill-chip"
                @close="toggleSkill(s)"
              >{{ s }}</el-tag>
            </div>
            <div v-else class="muted tiny">尚未选择技能</div>
          </div>

          <div class="skill-section">
            <div class="section-label">常用技能</div>
            <div class="skill-row">
              <el-tag
                v-for="s in presetSkills"
                :key="s"
                :type="isSelected(s) ? 'primary' : 'info'"
                :effect="isSelected(s) ? 'dark' : 'plain'"
                class="skill-chip clickable"
                @click="toggleSkill(s)"
              >
                {{ isSelected(s) ? '✓ ' : '+ ' }}{{ s }}
              </el-tag>
            </div>
          </div>

          <div class="skill-section">
            <div class="section-label">自定义标签</div>
            <div class="custom-row">
              <el-input
                v-model="customInput"
                placeholder="输入技能名，回车添加"
                maxlength="32"
                show-word-limit
                style="max-width: 320px"
                @keydown.enter.prevent="addCustom"
              />
              <el-button type="primary" plain @click="addCustom">
                添加
              </el-button>
            </div>
          </div>
        </div>
        <el-skeleton v-else :rows="6" animated />
      </el-tab-pane>

      <!-- 3. 贡献分 -->
      <el-tab-pane label="贡献分" name="contrib">
        <div class="card pane-card" v-if="contribLoaded">
          <div class="contrib-header">
            <div class="contrib-num-block">
              <div class="contrib-total">{{ contribTotal }}</div>
              <div class="muted tiny">总贡献分</div>
            </div>
            <div class="contrib-level-block">
              <span class="level-badge">{{ levelName(contribTotal) }}</span>
              <div class="level-progress">
                <el-progress
                  :percentage="levelProgressPct(contribTotal)"
                  :stroke-width="10"
                  :color="'#3D7EFF'"
                />
                <div class="muted tiny">
                  距离下一级
                  <b>{{ nextLevelName(contribTotal) }}</b>
                  还差
                  <b>{{ nextLevelDelta(contribTotal) }}</b>
                  分
                </div>
              </div>
            </div>
          </div>

          <div class="section-label">最近记录</div>
          <el-table
            :data="contribLog"
            stripe
            empty-text="暂无记录"
            class="contrib-table"
          >
            <el-table-column prop="created_at" label="时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="变动" width="100">
              <template #default="{ row }">
                <span :class="row.delta >= 0 ? 'delta-pos' : 'delta-neg'">
                  {{ row.delta >= 0 ? '+' : '' }}{{ row.delta }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="原因">
              <template #default="{ row }">
                {{ reasonLabel(row.reason) }}
              </template>
            </el-table-column>
          </el-table>
        </div>
        <el-skeleton v-else :rows="6" animated />
      </el-tab-pane>

      <!-- 4. 通知偏好 -->
      <el-tab-pane label="通知偏好" name="notify">
        <div class="card pane-card" v-if="profile">
          <div class="notify-row">
            <div class="notify-info">
              <div class="notify-label">邮件通知</div>
              <div class="muted tiny">通过邮件接收重要任务和小组提醒</div>
            </div>
            <el-switch
              v-model="notifyForm.email"
              :loading="savingNotify"
              @change="saveNotify"
            />
          </div>
          <div class="notify-row">
            <div class="notify-info">
              <div class="notify-label">站内通知</div>
              <div class="muted tiny">在 CoTask 内显示通知小红点和清单</div>
            </div>
            <el-switch
              v-model="notifyForm.inapp"
              :loading="savingNotify"
              @change="saveNotify"
            />
          </div>
          <div class="notify-row">
            <div class="notify-info">
              <div class="notify-label">微信通知</div>
              <div class="muted tiny">通过微信公众号推送（需绑定微信）</div>
            </div>
            <el-switch
              v-model="notifyForm.wechat"
              :loading="savingNotify"
              @change="saveNotify"
            />
          </div>
        </div>
        <el-skeleton v-else :rows="3" animated />
      </el-tab-pane>

      <!-- 5. 账户安全 -->
      <el-tab-pane label="账户安全" name="security">
        <div class="card pane-card">
          <div class="section-label">修改密码</div>
          <el-form
            ref="pwdFormRef"
            :model="pwdForm"
            :rules="pwdRules"
            label-position="top"
            class="pwd-form"
          >
            <el-form-item label="当前密码" prop="current">
              <el-input
                v-model="pwdForm.current"
                type="password"
                show-password
              />
            </el-form-item>
            <el-form-item label="新密码" prop="next">
              <el-input
                v-model="pwdForm.next"
                type="password"
                show-password
              />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirm">
              <el-input
                v-model="pwdForm.confirm"
                type="password"
                show-password
              />
            </el-form-item>
            <el-button
              type="primary"
              :loading="savingPwd"
              @click="savePwd"
            >修改密码</el-button>
          </el-form>

          <el-divider />

          <div class="section-label">第三方账户</div>
          <div class="wechat-row">
            <div>
              <div class="notify-label">微信</div>
              <div class="muted tiny">绑定微信以使用扫码登录和微信通知</div>
            </div>
            <el-button @click="onBindWechat">绑定微信</el-button>
          </div>

          <el-divider />

          <div class="section-label danger-label">危险操作</div>
          <div class="danger-row">
            <div>
              <div class="notify-label">注销账号</div>
              <div class="muted tiny">注销后所有数据将被永久删除，无法恢复</div>
            </div>
            <el-button type="danger" plain @click="onDestroy">
              注销账号
            </el-button>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { Api, type UserProfile } from '@/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const activeTab = ref<'basic' | 'skills' | 'contrib' | 'notify' | 'security'>('basic')

// ---------- profile ----------
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

function applyProfile(p: UserProfile) {
  profile.value = p
  profileForm.name = p.name || ''
  profileForm.student_id = p.student_id || ''
  profileForm.phone = p.phone || ''
  profileForm.email = p.email || ''
  profileForm.major = p.major || ''
  profileForm.grade = p.grade || ''
  profileForm.bio = p.bio || ''
  profileForm.avatar_url = p.avatar_url || ''
  selectedSkills.value = (p.skills || []).slice()

  const np = (p.prefs?.notify || {}) as Record<string, unknown>
  notifyForm.email = !!np.email
  notifyForm.inapp = np.inapp !== false // default true
  notifyForm.wechat = !!np.wechat
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

// ---------- skills ----------
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

// Debounced save (500ms)
let skillsTimer: number | null = null
let firstSkillLoad = true
watch(selectedSkills, (next) => {
  if (firstSkillLoad) {
    firstSkillLoad = false
    return
  }
  if (skillsTimer) window.clearTimeout(skillsTimer)
  skillsTimer = window.setTimeout(async () => {
    try {
      await Api.setSkills(next.slice())
      ElMessage.success('技能标签已保存', { duration: 1500 } as any)
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.message || '保存失败')
    }
  }, 500) as unknown as number
}, { deep: true })

// ---------- contribution ----------
const contribTotal = ref(0)
const contribLog = ref<any[]>([])
const contribLoaded = ref(false)

const LEVEL_THRESHOLDS = [0, 50, 150, 350, 700, 1200, 2000]
const LEVEL_NAMES = [
  '萌新协作者', '入门组员', '可靠搭档', '协作能手',
  '小组中坚', '协作专家', '协作大师',
]

function levelIndex(total: number) {
  let i = 0
  for (let k = LEVEL_THRESHOLDS.length - 1; k >= 0; k--) {
    if (total >= LEVEL_THRESHOLDS[k]) { i = k; break }
  }
  return i
}
function levelName(total: number) {
  return LEVEL_NAMES[levelIndex(total)]
}
function nextLevelName(total: number) {
  const i = levelIndex(total)
  return LEVEL_NAMES[Math.min(i + 1, LEVEL_NAMES.length - 1)]
}
function levelProgressPct(total: number) {
  const i = levelIndex(total)
  if (i >= LEVEL_THRESHOLDS.length - 1) return 100
  const lo = LEVEL_THRESHOLDS[i]
  const hi = LEVEL_THRESHOLDS[i + 1]
  return Math.round(((total - lo) / (hi - lo)) * 100)
}
function nextLevelDelta(total: number) {
  const i = levelIndex(total)
  if (i >= LEVEL_THRESHOLDS.length - 1) return 0
  return LEVEL_THRESHOLDS[i + 1] - total
}

const REASON_MAP: Record<string, string> = {
  task_done_on_time: '按时完成任务',
  task_done_late: '逾期完成任务',
  task_assigned: '被分配任务',
  helped_member: '协助组员',
  task_blocked: '任务阻塞',
}
function reasonLabel(r: string) {
  return REASON_MAP[r] || r
}
function formatDate(iso: string) {
  return dayjs(iso).format('YYYY-MM-DD HH:mm')
}

async function loadContribution() {
  try {
    const data: any = await Api.contribution()
    contribTotal.value = data?.total ?? data?.contribution ?? 0
    contribLog.value = data?.log ?? data?.entries ?? data?.items ?? []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载贡献分失败')
  } finally {
    contribLoaded.value = true
  }
}

// ---------- notify ----------
const notifyForm = reactive({
  email: true,
  inapp: true,
  wechat: false,
})
const savingNotify = ref(false)
let notifyTimer: number | null = null

function saveNotify() {
  if (notifyTimer) window.clearTimeout(notifyTimer)
  notifyTimer = window.setTimeout(async () => {
    savingNotify.value = true
    try {
      const oldPrefs = (profile.value?.prefs || {}) as Record<string, unknown>
      const newPrefs = {
        ...oldPrefs,
        notify: { ...notifyForm },
      }
      const updated = await Api.updateMe({ prefs: newPrefs } as Partial<UserProfile>)
      profile.value = updated
      ElMessage.success('通知偏好已保存', { duration: 1500 } as any)
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.message || '保存失败')
    } finally {
      savingNotify.value = false
    }
  }, 300) as unknown as number
}

// ---------- password ----------
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

// ---------- mount ----------
onMounted(async () => {
  await loadProfile()
  await loadContribution()
})
</script>

<style lang="scss" scoped>
.profile-page {
  max-width: 880px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.page-head {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.page-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
}

.profile-tabs {
  --el-tabs-header-height: 44px;
}

.pane-card {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.basic-form {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.avatar-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
  .avatar-fields { flex: 1; min-width: 0; }
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 16px;
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

/* Skills */
.ai-note {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(61,126,255,0.08);
  color: var(--color-primary);
  border-radius: var(--radius-sm);
  font-size: 12.5px;
  .info-icon { font-size: 16px; }
}
.skill-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.section-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}
.danger-label { color: var(--color-danger); }
.skill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.skill-chip {
  font-size: 12px;
  &.clickable { cursor: pointer; }
}
.custom-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

/* Contrib */
.contrib-header {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 8px 4px 16px;
  border-bottom: 1px solid var(--border-color);
}
.contrib-num-block { text-align: center; min-width: 120px; }
.contrib-total {
  font-size: 42px;
  font-weight: 700;
  color: var(--color-primary);
  line-height: 1;
}
.contrib-level-block {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.level-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 999px;
  background: rgba(230,162,60,0.16);
  color: #B45309;
  font-size: 13px;
  font-weight: 600;
  align-self: flex-start;
}
.level-progress {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.delta-pos { color: var(--color-success); font-weight: 600; }
.delta-neg { color: var(--color-danger); font-weight: 600; }
.contrib-table { margin-top: 4px; }

/* Notify */
.notify-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 4px;
  border-bottom: 1px solid var(--border-color);
  &:last-child { border-bottom: none; }
}
.notify-info { display: flex; flex-direction: column; gap: 2px; }
.notify-label { font-size: 14px; font-weight: 500; color: var(--text-primary); }

/* Security */
.pwd-form {
  max-width: 360px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.wechat-row, .danger-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 4px;
}

@media (max-width: 720px) {
  .form-grid { grid-template-columns: 1fr; }
  .contrib-header { flex-direction: column; align-items: flex-start; gap: 12px; }
  .avatar-row { flex-direction: column; align-items: flex-start; }
}
</style>
