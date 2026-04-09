<template>
  <div id="app">
    <el-container>
      <el-header class="app-header">
        <div class="header-content">
          <div class="header-left">
            <h1 class="logo">🎬 AIMedia</h1>
            <el-menu
              mode="horizontal"
              :default-active="$route.path"
              router
              class="header-menu"
              :ellipsis="false"
            >
              <el-menu-item index="/">项目列表</el-menu-item>
              <el-menu-item index="/tasks">任务管理</el-menu-item>
            </el-menu>
          </div>
          <div class="header-right">
            <span class="version-tag">v0.1.0</span>
          </div>
        </div>
      </el-header>

      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
const $route = useRoute()
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}

#app {
  min-height: 100vh;
  background: #f5f7fa;
}

.app-header {
  background: #1a1a2e;
  color: #fff;
  line-height: 60px;
  padding: 0;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0;
}

.logo {
  font-size: 20px;
  margin-right: 32px;
  color: #fff;
  white-space: nowrap;
}

.header-menu {
  background: transparent;
  border: none;
}

.header-menu .el-menu-item {
  color: #b0b8cc;
  font-size: 14px;
  height: 60px;
  line-height: 60px;
  border-bottom: 3px solid transparent;
}

.header-menu .el-menu-item:hover,
.header-menu .el-menu-item.is-active {
  background: rgba(255, 255, 255, 0.08) !important;
  color: #409eff !important;
  border-bottom-color: #409eff !important;
}

.header-right {
  display: flex;
  align-items: center;
}

.version-tag {
  font-size: 12px;
  color: #606266;
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

.el-main {
  padding: 20px;
}

/* Element Plus 全局样式增强 */
.el-button + .el-button {
  margin-left: 8px;
}
</style>
