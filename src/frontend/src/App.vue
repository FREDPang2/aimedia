<template>
  <div id="app">
    <el-container>
      <el-header class="app-header">
        <div class="header-content">
          <h1 class="logo">🎬 AIMedia</h1>
          <el-menu
            mode="horizontal"
            :default-active="$route.path"
            router
            class="header-menu"
          >
            <el-menu-item index="/">项目列表</el-menu-item>
          </el-menu>
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

.app-header {
  background: #1a1a2e;
  color: #fff;
  line-height: 60px;
  padding: 0;
}

.header-content {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 24px;
}

.logo {
  font-size: 20px;
  margin-right: 40px;
  color: #fff;
}

.header-menu {
  background: transparent;
  border: none;
}

.header-menu .el-menu-item {
  color: #ccc;
}

.header-menu .el-menu-item:hover,
.header-menu .el-menu-item.is-active {
  background: transparent;
  color: #409eff;
}

#app {
  min-height: 100vh;
  background: #f5f7fa;
}

.el-main {
  padding: 20px;
}
</style>
