import axios, { type AxiosError, type AxiosInstance } from 'axios'
import { ElMessage } from 'element-plus'

declare const __VITE_API_BASE__: string

const BASE = (typeof __VITE_API_BASE__ === 'string' ? __VITE_API_BASE__ : '/api')

export const http: AxiosInstance = axios.create({
  baseURL: BASE,
  timeout: 30000,
  withCredentials: true,
})

let refreshing: Promise<void> | null = null

http.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('access_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

http.interceptors.response.use(
  (res) => res,
  async (error: AxiosError<any>) => {
    const original = error.config as any
    if (error.response?.status === 401 && !original?._retry) {
      original._retry = true
      try {
        if (!refreshing) {
          refreshing = (async () => {
            const res = await axios.post(`${BASE}/auth/refresh`, {}, { withCredentials: true })
            const token = (res.data as any).access_token
            if (token) localStorage.setItem('access_token', token)
          })()
        }
        await refreshing
        refreshing = null
        original.headers.Authorization = `Bearer ${localStorage.getItem('access_token')}`
        return http(original)
      } catch {
        refreshing = null
        localStorage.removeItem('access_token')
        const { useAuthStore } = await import('@/stores/auth')
        useAuthStore().clear()
        if (location.pathname !== '/login') location.href = '/login'
        return Promise.reject(error)
      }
    }
    // Surface known business errors
    const data = error.response?.data as any
    if (data?.code && data?.message) {
      ElMessage.error(`${data.message}`)
    } else if (error.response?.status && error.response.status >= 500) {
      ElMessage.error('服务异常，请稍后再试')
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时')
    }
    return Promise.reject(error)
  },
)
