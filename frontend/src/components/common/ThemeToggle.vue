<template>
  <el-dropdown class="topbar-icon-trigger" @command="onCmd">
    <el-button text class="topbar-icon-btn" aria-label="切换主题">
      <el-icon :size="20">
        <Sunny v-if="ui.theme === 'light'" />
        <Moon v-else-if="ui.theme === 'dark'" />
        <Monitor v-else />
      </el-icon>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="light"><el-icon><Sunny /></el-icon> 亮色</el-dropdown-item>
        <el-dropdown-item command="dark"><el-icon><Moon /></el-icon> 暗色</el-dropdown-item>
        <el-dropdown-item command="auto"><el-icon><Monitor /></el-icon> 跟随系统</el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { Sunny, Moon, Monitor } from '@element-plus/icons-vue'
import { useUIStore } from '@/stores/ui'
import type { ThemeMode } from '@/utils/theme'

const ui = useUIStore()
function onCmd(t: string) { ui.setTheme(t as ThemeMode) }
</script>
