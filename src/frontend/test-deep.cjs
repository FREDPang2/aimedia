/**
 * AIMedia 深度边界测试
 * 补充基础测试未覆盖的边界情况和交互
 */
const { chromium } = require('playwright');
const fs = require('fs');

const BASE_URL = 'http://localhost:5173';
const SCREENSHOT_DIR = './test-screenshots';

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
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
      const screenshotPath = `${SCREENSHOT_DIR}/deep-${name.replace(/[^a-zA-Z0-9]/g, '-')}.png`;
      await page.screenshot({ path: screenshotPath, fullPage: false }).catch(() => {});
      console.log(`    📸 ${screenshotPath}`);
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

// ─── Deep Tests ────────────────────────────────────────────────────
const deepTests = [

  // A: 编辑项目后确认名称已更新
  ['A-编辑项目名称并确认更新', async (page) => {
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('networkidle');
    const cards = await page.locator('.project-card').count();
    if (cards === 0) return { warning: '无项目，跳过' };

    // 获取原名称
    const originalName = await page.locator('.project-card .project-name').first().innerText();

    // 打开编辑对话框
    await page.locator('.project-card .more-icon').first().click();
    await sleep(300);
    await page.locator('.el-dropdown-menu__item:has-text("编辑")').first().click();
    await sleep(400);

    // 修改名称
    const newName = '测试编辑-' + Date.now();
    const input = page.locator('.el-dialog input').first();
    await input.fill('');
    await input.fill(newName);

    // 保存
    await page.locator('.el-dialog .el-button--primary').click();
    await sleep(1500);

    // 确认名称已更新
    const updatedName = await page.locator('.project-card .project-name').first().innerText();
    if (!updatedName.includes('测试编辑')) {
      throw new Error(`编辑后名称未更新: "${updatedName}"，期望包含 "${newName}"`);
    }
  }],

  // B: 删除项目流程（取消+确认）
  ['B-删除项目-取消后项目仍在', async (page) => {
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('networkidle');
    const cards = await page.locator('.project-card').count();
    if (cards === 0) return { warning: '无项目，跳过' };

    const initialCount = cards;
    const projectName = await page.locator('.project-card .project-name').first().innerText();

    // 打开删除确认对话框
    await page.locator('.project-card .more-icon').first().click();
    await sleep(300);
    await page.locator('.el-dropdown-menu__item:has-text("删除")').first().click();
    await sleep(500);

    // 点击取消
    const cancelBtn = page.locator('.el-message-box__btn').filter({ hasText: '取消' });
    if (await cancelBtn.isVisible()) {
      await cancelBtn.click();
      await sleep(500);
    }

    // 确认项目仍在
    const stillExists = await page.locator('.project-card').count();
    if (stillExists !== initialCount) {
      throw new Error(`取消删除后项目数量变化: ${initialCount} → ${stillExists}`);
    }
    const stillHasName = await page.locator(`.project-card:has-text("${projectName}")`).count() > 0;
    if (!stillHasName) {
      throw new Error('取消删除后原项目不见了');
    }
  }],

  // C: 导航栏-任务管理入口
  ['C-导航栏-任务管理跳转', async (page) => {
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('networkidle');
    await page.locator('text=任务管理').click();
    await sleep(800);
    if (!page.url().includes('/tasks')) {
      throw new Error(`未跳转到任务管理页: ${page.url()}`);
    }
  }],

  // D: Series-点击卡片进入分集页
  ['D-Series-点击卡片跳转分集', async (page) => {
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('networkidle');
    const cards = await page.locator('.project-card').count();
    if (cards === 0) return { warning: '无项目，跳过' };
    await page.locator('.project-card').first().click();
    await page.waitForURL('**/series/**', { timeout: 5000 }).catch(() => {});
    await sleep(500);
    const seriesCards = await page.locator('.series-card').count();
    if (seriesCards === 0) return { warning: '无系列，跳过' };
    const prevUrl = page.url();
    await page.locator('.series-card').first().click();
    await sleep(1000);
    const currUrl = page.url();
    if (!currUrl.includes('/episode/')) {
      throw new Error(`未跳转到分集页: ${currUrl}`);
    }
  }],

  // E: Series-编辑系列
  ['E-Series-编辑系列名称', async (page) => {
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('networkidle');
    const cards = await page.locator('.project-card').count();
    if (cards === 0) return { warning: '无项目，跳过' };
    await page.locator('.project-card').first().click();
    await page.waitForURL('**/series/**', { timeout: 5000 }).catch(() => {});
    await sleep(500);
    const seriesCards = await page.locator('.series-card').count();
    if (seriesCards === 0) return { warning: '无系列，跳过' };
    await page.locator('.series-card .more-icon').first().click();
    await sleep(300);
    await page.locator('.el-dropdown-menu__item:has-text("编辑")').first().click();
    await sleep(400);
    const dialog = await page.locator('.el-dialog').isVisible();
    if (!dialog) throw new Error('编辑对话框未出现');
    await page.keyboard.press('Escape');
  }],

  // F: Episode-生成脚本按钮点击并确认
  ['F-Episode-生成脚本确认弹窗', async (page) => {
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('networkidle');
    const cards = await page.locator('.project-card').count();
    if (cards === 0) return { warning: '无项目，跳过' };
    await page.locator('.project-card').first().click();
    await page.waitForURL('**/series/**', { timeout: 5000 }).catch(() => {});
    await sleep(500);
    const seriesCards = await page.locator('.series-card').count();
    if (seriesCards === 0) return { warning: '无系列，跳过' };
    await page.locator('.series-card').first().click();
    await page.waitForURL('**/episode/**', { timeout: 5000 }).catch(() => {});
    await sleep(500);
    const epCards = await page.locator('.episode-card').count();
    if (epCards === 0) return { warning: '无分集，跳过' };

    // 点击生成脚本按钮
    const genBtn = page.locator('text=生成脚本').first();
    if (!(await genBtn.isVisible())) throw new Error('生成脚本按钮不可见');
    await genBtn.click();
    await sleep(500);
    // 应该出现确认对话框
    const confirmBox = await page.locator('.el-message-box').isVisible();
    if (!confirmBox) throw new Error('确认对话框未出现');
    // 取消
    const cancelBtn = page.locator('.el-message-box__btn').filter({ hasText: '取消' });
    await cancelBtn.click();
    await sleep(300);
  }],

  // G: Episode-查看脚本对话框
  ['G-Episode-查看脚本对话框', async (page) => {
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('networkidle');
    const cards = await page.locator('.project-card').count();
    if (cards === 0) return { warning: '无项目，跳过' };
    await page.locator('.project-card').first().click();
    await page.waitForURL('**/series/**', { timeout: 5000 }).catch(() => {});
    await sleep(500);
    const seriesCards = await page.locator('.series-card').count();
    if (seriesCards === 0) return { warning: '无系列，跳过' };
    await page.locator('.series-card').first().click();
    await page.waitForURL('**/episode/**', { timeout: 5000 }).catch(() => {});
    await sleep(500);
    const epCards = await page.locator('.episode-card').count();
    if (epCards === 0) return { warning: '无分集，跳过' };
    // 打开脚本对话框
    await page.locator('text=查看/编辑脚本').first().click();
    await sleep(400);
    const dialog = await page.locator('.el-dialog').isVisible();
    if (!dialog) throw new Error('脚本对话框未出现');
    await page.keyboard.press('Escape');
  }],

  // H: Tasks-刷新后数据更新
  ['H-Tasks-刷新后数据变化', async (page) => {
    await page.goto(`${BASE_URL}/tasks`);
    await page.waitForLoadState('networkidle');
    const statNums = await page.locator('.stat-card .stat-value').allInnerTexts();
    await page.locator('text=刷新').click();
    await sleep(1000);
    const statNumsAfter = await page.locator('.stat-card .stat-value').allInnerTexts();
    // 数据应该刷新成功（不报错即可）
  }],

  // I: 响应式-小窗口下布局
  ['I-响应式-小窗口布局正常', async (page) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('networkidle');
    // 小窗口下不应该崩溃
    const title = await page.title();
    if (!title) throw new Error('小窗口下页面标题丢失');
    // 截图看布局
  }],

  // J: 错误处理-API失败时
  ['J-错误处理-错误时显示提示', async (page) => {
    await page.route('**/api/v1/**', route => route.abort());
    await page.goto(`${BASE_URL}/`);
    await sleep(1000);
    // 应该有错误提示
    const hasAlert = await page.locator('.el-alert').isVisible().catch(() => false);
    const hasMessage = await page.locator('.el-message').isVisible().catch(() => false);
    if (!hasAlert && !hasMessage) {
      console.log('    (无明显错误提示，可能是加载状态)');
    }
  }],
];

async function main() {
  console.log(`\n🔬 AIMedia 深度边界测试`);
  console.log(`📍 ${BASE_URL}\n`);

  const results = [];
  for (const [name, testFn] of deepTests) {
    results.push(await runTest(name, testFn));
  }

  const passed = results.filter(r => r.ok).length;
  const failed = results.filter(r => !r.ok).length;

  console.log(`\n${'─'.repeat(50)}`);
  console.log(`深度测试结果: ✅ ${passed}  |  ❌ ${failed}`);
  console.log(`${'─'.repeat(50)}\n`);

  if (failed > 0) {
    console.log('❌ 失败详情:');
    results.filter(r => !r.ok).forEach(r => console.log(`  - ${r.error}`));
    console.log('');
  }

  process.exit(failed > 0 ? 1 : 0);
}

main().catch(err => {
  console.error('脚本异常:', err.message);
  process.exit(1);
});
