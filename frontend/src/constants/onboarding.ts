import {
  Calendar,
  ChatDotRound,
  FolderOpened,
  HomeFilled,
  MagicStick,
  Share,
  Star,
} from '@element-plus/icons-vue'
import type { Component } from 'vue'

export const ONBOARDING_VERSION = 1

export interface OnboardingPrefs {
  completed?: boolean
  version?: number
  completed_at?: string
}

export interface FeatureTourSlide {
  id: string
  title: string
  desc: string
  icon: Component
  accent: string
  bullets: string[]
}

/** Feature tour — same order as login hero (one dedicated AI slide). */
export const FEATURE_TOUR_SLIDES: FeatureTourSlide[] = [
  {
    id: 'ai',
    title: 'AI 助手',
    desc: '用自然语言生成与调整项目树，结合成员技能推荐负责人，并联动每日建议。',
    icon: MagicStick,
    accent: '#8b5cf6',
    bullets: ['对话式生成与编辑 WBS', '参考技能标签推荐负责人', '与首页今日建议联动'],
  },
  {
    id: 'dashboard',
    title: '工作台 · 先抓重点',
    desc: 'Dashboard 汇总待办、截止与日历，今日焦点帮你决定先推进什么。',
    icon: HomeFilled,
    accent: '#2563eb',
    bullets: ['今日焦点与紧急任务', '待办与截止提醒', '日历跳转相关 DDL'],
  },
  {
    id: 'tree',
    title: '项目树 · 结构清晰',
    desc: '树形管理课程项目，成员按节点认领，拖拽与状态流转跟得上节奏。',
    icon: Share,
    accent: '#7c3aed',
    bullets: ['多级 WBS 与节点状态', '拖拽与负责人分配', '与文件、讨论关联'],
  },
  {
    id: 'timeline',
    title: '时间轴 · 排期看得见',
    desc: '甘特视图呈现成员负载与截止，紧急项高亮，今天线标出当前节点。',
    icon: Calendar,
    accent: '#0d9488',
    bullets: ['周/月视图切换', '逾期与 72h 内预警', '点击任务块查看详情'],
  },
  {
    id: 'files',
    title: '文件 · 资料随任务',
    desc: '课件与报告关联项目节点，小组共享，文件夹与任务视图切换方便。',
    icon: FolderOpened,
    accent: '#d97706',
    bullets: ['文件夹 + 任务双视图', '上传/秒传/批量操作', '讨论与任务资料互通'],
  },
  {
    id: 'discussion',
    title: '讨论 · 沟通有上下文',
    desc: '按任务或主题交流，@ 成员、引用文件，讨论与项目进度在同一空间。',
    icon: ChatDotRound,
    accent: '#db2777',
    bullets: ['任务/主题帖子', '@ 提醒与回复', '与项目树节点关联'],
  },
  {
    id: 'inspiration',
    title: '灵感广场 · 快速起步',
    desc: '浏览优质公开模板，一键导入到小组项目树，再按课程继续细化。',
    icon: Star,
    accent: '#ca8a04',
    bullets: ['浏览与收藏模板', '一键导入项目树', '导入后继续编辑与分工'],
  },
]
