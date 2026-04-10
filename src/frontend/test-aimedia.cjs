/**
 * AIMedia 前端自动化测试脚本
 * 用法: node test-aimedia.cjs [projects|series|episode|tasks|all]
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:4001';
const SCREENSHOT_DIR = './test-screenshots';
const SCREENSHOT_MODE = process.env.SCREENSHOT !== '0';
const testModule = process.argv[2] || 'all';

if (SCREENSHOT_MODE && !fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

function screenshotName(name) {
  return SCREENSHOT_MODE ? `${SCREENSHOT_DIR}/${testModule}-${name}.png` : null;
}

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function withBrowser(testFn) {
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });
  try {
    return await testFn(browser);
  } finally {
    await browser.close();
  }
}

async function runTest(name, testFn) {
  process.stdout.write(`  ▶ ${name}... `);
  const start = Date.now();
  try {
    const result = await withBrowser(async (browser) => {
      const page = await browser.newPage();
      await page.setViewportSize({ width: 1280, height: 800 });
      const r = await testFn(page);
      if (screenshotName(name)) {
        await page.screenshot({ path: screenshotName(name), fullPage: false }).catch(() => {});
      }
      return r;
    });
    const ms = Date.now() - start;
    console.log(`✅ (${ms}ms)`);
    if (result && result.warning) console.log(`    ⚠ ${result.warning}`);
    return { ok: true, ...result };
  } catch (err) {
    const ms = Date.now() - start;
    console.log(`❌ (${ms}ms) ${err.message}`);
    return { ok: false, error: err.message };
  }
}

async function navigateToSeries(page) {
  await page.goto(`${BASE_URL}/`);
  await page.waitForLoadState('networkidle');
  const cards = await page.locator('.project-card').count();
  if (cards > 0) {
    await page.locator('.project-card').first().click();
    await page.waitForURL('**/series/**', { timeout: 5000 }).catch(() => {});
    await sleep(500);
    return true;
  }
  return false;
}

async function navigateToEpisode(page) {
  await page.goto(`${BASE_URL}/`);
  await page.waitForLoadState('networkidle');
  const cards = await page.locator('.project-card').count();
  if (cards > 0) {
    await page.locator('.project-card').first().click();
    await page.waitForURL('**/series/**', { timeout: 5000 }).catch(() => {});
    await sleep(500);
    const seriesCards = await page.locator('.series-card').count();
    if (seriesCards > 0) {
      await page.locator('.series-card').first().click();
      await page.waitForURL('**/episode/**', { timeout: 5000 }).catch(() => {});
      await sleep(500);
      return true;
    }
  }
  return false;
}

// ─── Projects ─────────────────────────────────────────────────────
const projectTests = [
  ['P1-页面标题', async (page) => {
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('networkidle');
    const title = await page.title();
    if (!title.includes('AIMedia')) throw new Error(`标题异常: ${title}`);
  }],
  ['P2-项目卡片渲染', async (page) => {
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('networkidle');
    const n = await page.locator('.project-card').count();
    if (n === 0) throw new Error('没有项目卡片（正常则跳过）');
  }],
  ['P3-新建项目按钮打开对话框', async (page) => {
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('networkidle');
    await page.locator('text=新建项目').click();
    await sleep(400);
    if (!(await page.locator('.el-dialog').isVisible())) throw new Error('对话框未出现');
    await page.keyboard.press('Escape');
  }],
  ['P4-新建项目表单提交', async (page) => {
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('networkidle');
    await page.locator('text=新建项目').click();
    await sleep(400);
    const input = page.locator('.el-dialog input').first();
    await input.fill('自动化测试-' + Date.now());
    await page.locator('.el-dialog .el-button--primary').click();
    await sleep(1500);
    const stillOpen = await page.locator('.el-dialog').isVisible().catch(() => false);
    if (stillOpen) {
      await page.keyboard.press('Escape');
      throw new Error('对话框仍然打开，提交可能失败');
    }
  }],
  ['P5-编辑项目下拉菜单', async (page) => {
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('networkidle');
    const n = await page.locator('.project-card').count();
    if (n === 0) return { warning: '无项目，跳过' };
    await page.locator('.project-card .more-icon').first().click();
    await sleep(300);
    const editItem = page.locator('.el-dropdown-menu__item:has-text("编辑")').first();
    if (!(await editItem.isVisible())) throw new Error('编辑菜单项未出现');
  }],
  ['P6-点击项目卡片跳转系列页', async (page) => {
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('networkidle');
    const n = await page.locator('.project-card').count();
    if (n === 0) return { warning: '无项目，跳过' };
    const prevUrl = page.url();
    await page.locator('.project-card').first().click();
    await sleep(1000);
    const currUrl = page.url();
    if (currUrl === prevUrl) throw new Error('URL 未变化');
    if (!currUrl.includes('/series/')) throw new Error(`未跳转到系列页: ${currUrl}`);
  }],
  ['P7-项目状态标签显示', async (page) => {
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('networkidle');
    const tags = await page.locator('.project-card .el-tag').count();
    if (tags === 0) throw new Error('状态标签未显示');
  }],
];

// ─── Series ───────────────────────────────────────────────────────
const seriesTests = [
  ['S1-系列页加载', async (page) => {
    const ok = await navigateToSeries(page);
    if (!ok) return { warning: '无数据，跳过' };
    if (!page.url().includes('/series/')) throw new Error(`不在系列页: ${page.url()}`);
  }],
  ['S2-返回按钮', async (page) => {
    const ok = await navigateToSeries(page);
    if (!ok) return { warning: '无数据，跳过' };
    const back = page.locator('text=返回').first();
    if (!(await back.isVisible())) throw new Error('返回按钮不可见');
  }],
  ['S3-新建系列对话框', async (page) => {
    const ok = await navigateToSeries(page);
    if (!ok) return { warning: '无数据，跳过' };
    await page.locator('text=新建系列').click();
    await sleep(400);
    if (!(await page.locator('.el-dialog').isVisible())) throw new Error('对话框未出现');
    await page.keyboard.press('Escape');
  }],
  ['S4-生成大纲按钮', async (page) => {
    const ok = await navigateToSeries(page);
    if (!ok) return { warning: '无数据，跳过' };
    const btns = await page.locator('text=生成大纲').count();
    if (btns === 0) throw new Error('未找到生成大纲按钮');
  }],
  ['S5-新建系列并创建', async (page) => {
    const ok = await navigateToSeries(page);
    if (!ok) return { warning: '无数据，跳过' };
    await page.locator('text=新建系列').click();
    await sleep(400);
    await page.locator('.el-dialog input').first().fill('自动化系列-' + Date.now());
    await page.locator('.el-dialog .el-button--primary').click();
    await sleep(1500);
    const stillOpen = await page.locator('.el-dialog').isVisible().catch(() => false);
    if (stillOpen) {
      await page.keyboard.press('Escape');
      throw new Error('对话框仍然打开');
    }
  }],
];

// ─── Episode ──────────────────────────────────────────────────────
const episodeTests = [
  ['E1-分集页加载', async (page) => {
    const ok = await navigateToEpisode(page);
    if (!ok) return { warning: '无数据，跳过' };
    if (!page.url().includes('/episode/')) throw new Error(`不在分集页: ${page.url()}`);
  }],
  ['E2-新建分集对话框', async (page) => {
    const ok = await navigateToEpisode(page);
    if (!ok) return { warning: '无数据，跳过' };
    await page.locator('text=新建分集').click();
    await sleep(400);
    if (!(await page.locator('.el-dialog').isVisible())) throw new Error('对话框未出现');
    await page.keyboard.press('Escape');
  }],
  ['E3-生成脚本按钮', async (page) => {
    const ok = await navigateToEpisode(page);
    if (!ok) return { warning: '无数据，跳过' };
    const btn = page.locator('text=生成脚本').first();
    if (!(await btn.isVisible())) throw new Error('生成脚本按钮不可见');
  }],
  ['E4-任务队列概览', async (page) => {
    const ok = await navigateToEpisode(page);
    if (!ok) return { warning: '无数据，跳过' };
    // 等待队列卡片出现（fetchData 需要时间加载 queueStatus）
    const queue = page.locator('.queue-card');
    try {
      await queue.waitFor({ timeout: 5000 });
    } catch {
      // 截图调试
      await page.screenshot({ path: './test-screenshots/debug-e4.png' });
      throw new Error('任务队列概览不存在 (等待超时)');
    }
  }],
  ['E5-创建分集并提交', async (page) => {
    const ok = await navigateToEpisode(page);
    if (!ok) return { warning: '无数据，跳过' };
    await page.locator('text=新建分集').click();
    await sleep(400);
    await page.locator('.el-dialog input').first().fill('自动化分集-' + Date.now());
    await page.locator('.el-dialog .el-button--primary').click();
    await sleep(1500);
    const stillOpen = await page.locator('.el-dialog').isVisible().catch(() => false);
    if (stillOpen) {
      await page.keyboard.press('Escape');
      throw new Error('对话框仍然打开');
    }
  }],
];

// ─── Tasks ────────────────────────────────────────────────────────
const taskTests = [
  ['T1-任务管理页加载', async (page) => {
    await page.goto(`${BASE_URL}/tasks`);
    await page.waitForLoadState('networkidle');
    if (!page.url().includes('/tasks')) throw new Error(`不在任务页: ${page.url()}`);
  }],
  ['T2-队列统计卡片', async (page) => {
    await page.goto(`${BASE_URL}/tasks`);
    await page.waitForLoadState('networkidle');
    const cards = page.locator('.stat-card');
    const n = await cards.count();
    if (n < 4) throw new Error(`统计卡片数量: ${n}，期望4个`);
  }],
  ['T3-Tabs切换', async (page) => {
    await page.goto(`${BASE_URL}/tasks`);
    await page.waitForLoadState('networkidle');
    await page.locator('.el-tabs__item:has-text("进行中")').click();
    await sleep(200);
    await page.locator('.el-tabs__item:has-text("失败")').click();
    await sleep(200);
    await page.locator('.el-tabs__item:has-text("全部")').click();
    await sleep(200);
  }],
  ['T4-刷新按钮', async (page) => {
    await page.goto(`${BASE_URL}/tasks`);
    await page.waitForLoadState('networkidle');
    await page.locator('text=刷新').click();
    await sleep(600);
  }],
  ['T5-空状态提示', async (page) => {
    await page.goto(`${BASE_URL}/tasks`);
    await page.waitForLoadState('networkidle');
    // 有任务或空状态都应该正常显示，不报错即可
  }],
];

// ─── 主入口 ────────────────────────────────────────────────────────
async function main() {
  console.log(`\n🎬 AIMedia 前端自动化测试`);
  console.log(`📍 目标: ${BASE_URL}`);
  console.log(`📸 截图: ${SCREENSHOT_MODE ? '开启' : '关闭'}`);
  console.log(`🔧 模块: ${testModule}`);
  console.log('');

  let allResults = [];
  const allTests = {
    projects: projectTests,
    series: seriesTests,
    episode: episodeTests,
    tasks: taskTests,
  };

  const toRun = testModule === 'all'
    ? Object.entries(allTests)
    : [[testModule, allTests[testModule] || []]];

  for (const [name, tests] of toRun) {
    console.log(`\n━━ ${name.toUpperCase()} ━━`);
    const results = [];
    for (const [testName, testFn] of tests) {
      results.push(await runTest(testName, testFn));
    }
    allResults.push(...results);
  }

  const passed = allResults.filter(r => r.ok).length;
  const failed = allResults.filter(r => !r.ok).length;
  const warnings = allResults.filter(r => r.ok && r.warning).map(r => r.warning);

  console.log(`\n${'─'.repeat(50)}`);
  console.log(`结果: ✅ ${passed}  |  ❌ ${failed} 失败  |  ⚠ ${warnings.length} 警告`);
  console.log(`${'─'.repeat(50)}\n`);

  if (warnings.length > 0) {
    console.log('⚠ 警告（数据不足，正常）:');
    warnings.forEach(w => console.log(`  - ${w}`));
    console.log('');
  }

  if (failed > 0) {
    console.log('❌ 失败详情:');
    allResults.filter(r => !r.ok).forEach(r => {
      console.log(`  - ${r.error}`);
    });
    console.log('');
  }

  process.exit(failed > 0 ? 1 : 0);
}

main().catch(err => {
  console.error('脚本异常:', err.message);
  process.exit(1);
});
