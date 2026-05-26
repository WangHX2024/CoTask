import { ElMessage, ElMessageBox, type ElMessageBoxOptions, type MessageParams } from 'element-plus'
import { isVNode } from 'vue'

const BOX_CLASS = 'cotask-message-box'
const TOAST_CLASS = 'cotask-message'

function withBoxClass(options?: ElMessageBoxOptions): ElMessageBoxOptions {
  const extra = options?.customClass
  const customClass = extra
    ? Array.isArray(extra)
      ? [BOX_CLASS, ...extra].join(' ')
      : `${BOX_CLASS} ${extra}`
    : BOX_CLASS
  return { ...options, customClass, roundButton: false }
}

/** Apply CoTask capsule styling class to every system message box. */
export function patchMessageBox(): void {
  const nativeConfirm = ElMessageBox.confirm.bind(ElMessageBox)
  const nativeAlert = ElMessageBox.alert.bind(ElMessageBox)
  const nativePrompt = ElMessageBox.prompt.bind(ElMessageBox)

  ElMessageBox.confirm = (message, title, options) =>
    nativeConfirm(message, title, withBoxClass(options))
  ElMessageBox.alert = (message, title, options) =>
    nativeAlert(message, title, withBoxClass(options))
  ElMessageBox.prompt = (message, title, options) =>
    nativePrompt(message, title, withBoxClass(options))
}

function withToastClass(params: MessageParams): MessageParams {
  if (typeof params === 'string') {
    return { message: params, customClass: TOAST_CLASS, plain: false }
  }
  if (isVNode(params)) {
    return { message: params, customClass: TOAST_CLASS, plain: false }
  }
  const extra = params.customClass
  const customClass = extra
    ? Array.isArray(extra)
      ? [TOAST_CLASS, ...extra].join(' ')
      : `${TOAST_CLASS} ${extra}`
    : TOAST_CLASS
  return { ...params, customClass, plain: false }
}

/** Apply CoTask capsule styling to ElMessage toasts. */
export function patchMessage(): void {
  const types = ['success', 'info', 'warning', 'error', 'primary'] as const
  for (const type of types) {
    const original = ElMessage[type].bind(ElMessage)
    ElMessage[type] = ((options?: MessageParams, appContext?) =>
      original(withToastClass(options ?? {}), appContext)) as typeof ElMessage[typeof type]
  }
}
