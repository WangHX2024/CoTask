/** Login page brand carousel — one AI slide, rest focus on collaboration features. */

export interface LoginHeroSlide {
  id: string
  dotLabel: string
  headline: [string, string]
  lead: string
}

export const LOGIN_HERO_SLIDES: LoginHeroSlide[] = [
  {
    id: 'ai',
    dotLabel: 'AI 助手',
    headline: ['自然语言协作，', '从想法到任务'],
    lead: '用对话生成与调整项目树，结合技能标签推荐负责人，并给出每日推进建议。',
  },
  {
    id: 'dashboard',
    dotLabel: '工作台',
    headline: ['待办与截止，', '一屏看清'],
    lead: '首页聚合今日焦点、紧急任务与日历提醒，帮你先抓该推进的事。',
  },
  {
    id: 'tree',
    dotLabel: '项目树',
    headline: ['WBS 拆解，', '认领与跟进'],
    lead: '树形管理课程项目，拖拽调整结构，成员按节点认领并更新状态。',
  },
  {
    id: 'timeline',
    dotLabel: '时间轴',
    headline: ['排期与负载，', '一目了然'],
    lead: '甘特视图展示成员任务与截止，紧急项高亮，今天线标出当前进度。',
  },
  {
    id: 'files',
    dotLabel: '文件',
    headline: ['资料挂到任务，', '小组共享'],
    lead: '课件与报告关联项目节点，文件夹与任务双视图，上传与秒传省心。',
  },
  {
    id: 'discussion',
    dotLabel: '讨论',
    headline: ['讨论区串联，', '上下文不丢'],
    lead: '按任务或主题发帖，@ 成员、引用资料，沟通记录与项目进度在一起。',
  },
  {
    id: 'inspiration',
    dotLabel: '灵感广场',
    headline: ['优质模板，', '一键起步'],
    lead: '浏览他人公开的项目结构，收藏后导入到自己的小组继续细化。',
  },
]
