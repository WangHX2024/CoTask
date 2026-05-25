/** Typed API wrappers. */
import { http } from './client'

// ---------- Types ----------
export interface UserBrief {
  id: number; name: string; phone?: string; student_id?: string
  avatar_url?: string; major?: string; grade?: string; bio?: string
  contribution: number
}
export interface UserProfile extends UserBrief {
  email?: string; skills: string[]; prefs: Record<string, unknown>; created_at: string
}
export interface GroupBrief {
  id: number; course_name: string; name: string; invite_code?: string
  status: string; description?: string; created_by: number; created_at: string
  role: 'leader' | 'member'; member_count: number; progress: number
}
export interface MemberInfo {
  user_id: number; name: string; avatar_url?: string
  role: 'leader' | 'member'; anon_id?: string; joined_at: string
  contribution: number; skills: string[]
}
export interface TaskNode {
  id: number; parent_id: number | null; title: string; description: string
  is_leaf: boolean; refined: boolean
  start_date?: string; end_date?: string
  status: 'todo' | 'in_progress' | 'done' | 'blocked'
  progress: number; depth: number; position: number
  path: string; assignees: number[]; dependencies: number[]; version: number
}
export interface TreeResponse { group_id: number; version: number; nodes: TaskNode[] }

export interface GanttBlock {
  task_id: number; title: string; user_id: number; user_name: string; user_avatar: string
  start_date: string; end_date: string; status: string; progress: number; urgent: boolean
  dependencies: number[]
}
export interface GroupRow {
  user_id: number; name: string; avatar_url: string; role: string
  blocks: GanttBlock[]
}
export interface TimelineResponse { view: string; start: string; end: string; rows: GroupRow[] }

export interface DashTask {
  task_id: number; title: string; group_id: number; group_name: string
  course_name: string; end_date: string; status: string; progress: number
  urgent: boolean; days_left: number
}
export interface LeaderGroup {
  group_id: number; course_name: string; name: string; progress: number
  todo: number; in_progress: number; done: number; blocked: number; urgent_count: number
}
export interface DashResponse { tasks: DashTask[]; urgent: DashTask[]; leader_groups: LeaderGroup[] }
export interface AdviceResponse {
  advice: string; suggestions: string[]; generated_at: string; cached: boolean
}

export interface PostBrief {
  id: number; title: string; cover_url?: string; category: string; course_tag?: string
  author_id: number; author_name: string; author_avatar: string; anon: boolean
  likes: number; favs: number; comments: number; link_url?: string
  has_template: boolean; excerpt: string; created_at: string
  liked_by_me: boolean; favored_by_me: boolean
}
export interface PostDetail extends PostBrief { body_md: string; template_root_id?: number }
export interface Comment {
  id: number; post_id: number; body: string; author_id: number
  author_name: string; author_avatar: string; anon: boolean
  parent_id?: number; created_at: string
}
export interface NotificationItem {
  id: number; type: string; payload: Record<string, unknown>
  read_at?: string; created_at: string
}
export interface FileInfo {
  id: number; filename: string; size: number; mime?: string; md5?: string
  uploader_id: number; uploader_name?: string; group_id?: number; task_id?: number
  folder_id?: number; visibility: string; version: number
  parent_file_id?: number; download_url: string; created_at: string
}
export interface FolderInfo { id: number; name: string; parent_id: number | null; path: string }

export interface DiscussionMessage {
  id: number; channel_id?: number; task_id?: number; body: string
  author_id: number; author_name: string; author_avatar: string; anon: boolean
  quote_id?: number; created_at: string
}
export interface Channel {
  id: number; name: string; created_by: number; created_at: string
}

// ---------- Endpoints ----------
export const Api = {
  // auth
  sendSms: (phone: string, purpose = 'register') =>
    http.post('/auth/sms', { phone, purpose }),
  register: (data: { phone: string; code: string; password: string; name: string; student_id?: string; major?: string }) =>
    http.post<{ access_token: string; refresh_token: string; user: UserBrief }>('/auth/register', data),
  login: (data: { account: string; password: string }) =>
    http.post<{ access_token: string; refresh_token: string; user: UserBrief }>('/auth/login', data),
  resetPassword: (data: { phone: string; code: string; new_password: string }) =>
    http.post('/auth/reset-password', data),

  // users
  me: () => http.get<UserProfile>('/users/me').then((r) => r.data),
  updateMe: (patch: Partial<UserProfile>) =>
    http.patch<UserProfile>('/users/me', patch).then((r) => r.data),
  setSkills: (skills: string[]) =>
    http.put<{ skills: string[] }>('/users/me/skills', { skills }).then((r) => r.data),
  changePassword: (current_password: string, new_password: string) =>
    http.put('/users/me/password', { current_password, new_password }),
  contribution: () => http.get('/users/me/contribution').then((r) => r.data),

  // groups
  listGroups: () => http.get<GroupBrief[]>('/groups').then((r) => r.data),
  createGroup: (data: { course_name: string; name: string; description?: string }) =>
    http.post<GroupBrief>('/groups', data).then((r) => r.data),
  joinGroup: (invite_code: string) =>
    http.post<GroupBrief>('/groups/join', { invite_code }).then((r) => r.data),
  getGroup: (gid: number) => http.get<GroupBrief>(`/groups/${gid}`).then((r) => r.data),
  updateGroup: (gid: number, patch: any) =>
    http.patch<GroupBrief>(`/groups/${gid}`, patch).then((r) => r.data),
  members: (gid: number) =>
    http.get<MemberInfo[]>(`/groups/${gid}/members`).then((r) => r.data),
  kick: (gid: number, uid: number) => http.delete(`/groups/${gid}/members/${uid}`),
  transfer: (gid: number, target_user_id: number) =>
    http.post(`/groups/${gid}/transfer`, { target_user_id }),
  leaveGroup: (gid: number) => http.post(`/groups/${gid}/leave`),
  dissolveGroup: (gid: number, confirm_name: string) =>
    http.delete(`/groups/${gid}`, { data: { confirm_name } }),

  // tree
  getTree: (gid: number) => http.get<TreeResponse>(`/groups/${gid}/tree`).then((r) => r.data),
  putTree: (gid: number, payload: { expected_version?: number; nodes: any[] }) =>
    http.put<TreeResponse>(`/groups/${gid}/tree`, payload).then((r) => r.data),
  createNode: (gid: number, data: any) =>
    http.post<TaskNode>(`/groups/${gid}/tree/nodes`, data).then((r) => r.data),
  updateNode: (gid: number, tid: number, data: any) =>
    http.patch<TaskNode>(`/groups/${gid}/tree/nodes/${tid}`, data).then((r) => r.data),
  deleteNode: (gid: number, tid: number) =>
    http.delete(`/groups/${gid}/tree/nodes/${tid}`),
  moveNode: (gid: number, tid: number, new_parent_id?: number | null, new_position?: number) =>
    http.post(`/groups/${gid}/tree/nodes/${tid}/move`, { new_parent_id, new_position }),

  // tasks
  taskDetail: (gid: number, tid: number) =>
    http.get(`/groups/${gid}/tasks/${tid}`).then((r) => r.data),
  changeStatus: (gid: number, tid: number, status: string) =>
    http.patch(`/groups/${gid}/tasks/${tid}/status`, { status }).then((r) => r.data),
  assign: (gid: number, tid: number, assignees: number[]) =>
    http.post(`/groups/${gid}/tasks/${tid}/assign`, { assignees }).then((r) => r.data),
  nudge: (gid: number, tid: number, message?: string) =>
    http.post(`/groups/${gid}/tasks/${tid}/nudge`, { message: message ?? '加把劲！这个任务快到 DDL 了' }),

  // timeline
  timeline: (gid: number, view = 'week', start?: string) =>
    http.get<TimelineResponse>(`/groups/${gid}/timeline`, { params: { view, start } }).then((r) => r.data),

  // dashboard
  dashboard: () => http.get<DashResponse>('/dashboard/tasks').then((r) => r.data),
  advice: () => http.get<AdviceResponse>('/dashboard/advice').then((r) => r.data),

  // inspiration
  posts: (q: Record<string, unknown> = {}) =>
    http.get<{ items: PostBrief[]; total: number; page: number; size: number }>(
      '/inspiration/posts',
      { params: q },
    ).then((r) => r.data),
  post: (id: number) => http.get<PostDetail>(`/inspiration/posts/${id}`).then((r) => r.data),
  createPost: (data: any) => http.post<PostDetail>('/inspiration/posts', data).then((r) => r.data),
  updatePost: (id: number, data: any) =>
    http.patch<PostDetail>(`/inspiration/posts/${id}`, data).then((r) => r.data),
  deletePost: (id: number) => http.delete(`/inspiration/posts/${id}`),
  likePost: (id: number) => http.post(`/inspiration/posts/${id}/like`).then((r) => r.data),
  favPost: (id: number) => http.post(`/inspiration/posts/${id}/favorite`).then((r) => r.data),
  comments: (id: number) =>
    http.get<Comment[]>(`/inspiration/posts/${id}/comments`).then((r) => r.data),
  addComment: (id: number, data: { body: string; parent_id?: number; anon?: boolean }) =>
    http.post<Comment>(`/inspiration/posts/${id}/comments`, data).then((r) => r.data),
  importTemplate: (postId: number, to_group_id: number, mode = 'replace') =>
    http.post(`/inspiration/posts/${postId}/import`, { to_group_id, mode }).then((r) => r.data),

  // files
  signUpload: (data: any) => http.post('/files/sign', data).then((r) => r.data as any),
  finalizeFile: (file_id: number) =>
    http.post<FileInfo>('/files/finalize', { file_id }).then((r) => r.data),
  deleteFile: (id: number) => http.delete(`/files/${id}`),
  listFiles: (gid: number, params: any = {}) =>
    http.get<FileInfo[]>(`/groups/${gid}/files`, { params }).then((r) => r.data),
  listFolders: (gid: number) =>
    http.get<FolderInfo[]>(`/groups/${gid}/folders`).then((r) => r.data),
  createFolder: (gid: number, data: { name: string; parent_id?: number }) =>
    http.post<FolderInfo>(`/groups/${gid}/folders`, data).then((r) => r.data),

  // discussion
  channels: (gid: number) =>
    http.get<Channel[]>(`/groups/${gid}/discussion/channels`).then((r) => r.data),
  createChannel: (gid: number, name: string) =>
    http.post<Channel>(`/groups/${gid}/discussion/channels`, { name }).then((r) => r.data),
  messages: (gid: number, params: any) =>
    http.get<DiscussionMessage[]>(`/groups/${gid}/discussion/messages`, { params }).then((r) => r.data),
  postMessage: (gid: number, data: any) =>
    http.post<DiscussionMessage>(`/groups/${gid}/discussion/messages`, data).then((r) => r.data),

  // notifications
  notifications: (params: any = {}) =>
    http.get<NotificationItem[]>('/notifications', { params }).then((r) => r.data),
  unreadCount: () => http.get<{ count: number }>('/notifications/unread-count').then((r) => r.data),
  markRead: (ids?: number[]) => http.post('/notifications/read', { ids: ids ?? [] }),

  // ai
  aiJob: (scope: string, group_id: number | null, payload: any) =>
    http.post<{ id: number; status: string }>('/ai/jobs', { scope, group_id, payload }).then((r) => r.data),
  aiJobStatus: (id: number) =>
    http.get<{ id: number; status: string; result: any; error?: string }>(`/ai/jobs/${id}`).then((r) => r.data),
}
