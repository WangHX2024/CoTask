/** Invite copy for sharing a group join code. */
export function buildGroupInvitePitch(
  g: { course_name: string; name: string; invite_code?: string },
  siteUrl: string,
): string {
  if (!g.invite_code) return ''
  return [
    '你好！邀请你加入我们的课程小组。',
    '',
    `【课程】${g.course_name}`,
    `【小组】${g.name}`,
    '',
    '我们使用 CoTask 协作平台开展小组学习与项目管理。CoTask 提供项目树拆解与进度汇总、甘特式时间轴、小组文件库、讨论区，以及 AI 辅助拆解任务与排期建议，帮助组员分工清晰、DDL 可控、协作过程可追溯。',
    '',
    siteUrl
      ? `请打开 ${siteUrl}，注册或登录后，进入「我的小组」→「加入小组」，输入下方 8 位邀请码即可完成加入。`
      : '请注册或登录 CoTask，进入「我的小组」→「加入小组」，输入下方 8 位邀请码即可完成加入。',
    '',
    `邀请码：${g.invite_code}`,
    '',
    '如有疑问，请联系本组组长。期待与你一起协作！',
  ].join('\n')
}
