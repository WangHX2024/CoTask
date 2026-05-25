import { defineStore } from 'pinia'
import { Api, type UserBrief } from '@/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: localStorage.getItem('access_token') || '',
    user: null as UserBrief | null,
  }),
  getters: {
    isAuthed: (s) => !!s.accessToken,
  },
  actions: {
    setToken(t: string) {
      this.accessToken = t
      localStorage.setItem('access_token', t)
    },
    setUser(u: UserBrief | null) {
      this.user = u
    },
    async login(account: string, password: string) {
      const { data } = await Api.login({ account, password })
      this.setToken(data.access_token)
      this.setUser(data.user)
      return data
    },
    async register(data: any) {
      const r = await Api.register(data)
      this.setToken(r.data.access_token)
      this.setUser(r.data.user)
      return r.data
    },
    async fetchMe() {
      const me = await Api.me()
      this.setUser(me as any)
      return me
    },
    clear() {
      this.accessToken = ''
      this.user = null
      localStorage.removeItem('access_token')
    },
  },
  persist: {
    key: 'cotask-auth',
    storage: localStorage,
    pick: ['user'],
  } as any,
})
