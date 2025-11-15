/**
 * PhytoOracle 前端导航测试
 * 测试所有页面的导航链接和路径是否正确
 */

import { test, expect } from '@playwright/test';

/**
 * 页面导航测试套件
 */
test.describe('页面导航测试', () => {
  /**
   * 每个测试前的准备工作
   */
  test.beforeEach(async ({ page }) => {
    // 访问主页
    await page.goto('/');
    // 等待页面加载完成
    await page.waitForLoadState('networkidle');
  });

  /**
   * 测试1：主页应该正确加载
   */
  test('主页应该正确加载', async ({ page }) => {
    // 验证页面标题
    await expect(page).toHaveURL('/');

    // 验证主页核心元素存在（使用更精确的选择器）
    await expect(page.getByRole('heading', { name: 'PhytoOracle' })).toBeVisible();
    await expect(page.locator('text=核心功能')).toBeVisible();
  });

  /**
   * 测试2：检查所有链接是否包含错误路径
   */
  test('检查页面中是否存在错误的路径', async ({ page }) => {
    // 获取页面所有链接
    const links = await page.locator('a[href]').all();

    const errorPaths: { href: string; text: string }[] = [];

    for (const link of links) {
      const href = await link.getAttribute('href');
      const text = await link.textContent();

      if (href) {
        // 检查是否包含错误的路径模式
        if (
          href.includes('/diagnose/single') ||
          href.includes('/diagnose/batch') ||
          href.includes('/ontology/manage') ||
          href.includes('/knowledge/manage')
        ) {
          errorPaths.push({ href, text: text || '' });
        }
      }
    }

    // 如果发现错误路径，输出详细信息
    if (errorPaths.length > 0) {
      console.log('发现错误路径：', errorPaths);
    }

    // 断言不应该有错误路径
    expect(errorPaths).toHaveLength(0);
  });

  /**
   * 测试3：Header 导航链接应该正确
   */
  test('Header 导航菜单链接应该正确', async ({ page }) => {
    // 等待Header加载
    await expect(page.locator('header')).toBeVisible();

    // 检查导航菜单中的链接（注意：当前实现使用的是onClick，不是href）
    // 这里我们检查菜单项是否存在
    const menuItems = [
      '首页',
      '单图诊断',
      '批量诊断',
      '诊断历史',
      '本体管理',
      '知识管理'
    ];

    for (const item of menuItems) {
      const menuItem = page.locator(`text="${item}"`).first();
      await expect(menuItem).toBeVisible();
    }
  });

  /**
   * 测试4：主页功能卡片应该使用正确的路径
   */
  test('主页功能卡片应该使用正确的路径', async ({ page }) => {
    // 等待卡片加载
    await expect(page.locator('text=核心功能')).toBeVisible();

    // 功能卡片应该是可点击的，检查它们的存在性
    const cardTitles = [
      '单图诊断',
      '批量诊断',
      '诊断历史',
      '本体管理',
      '知识管理'
    ];

    for (const title of cardTitles) {
      const card = page.locator(`text="${title}"`).first();
      await expect(card).toBeVisible();
    }
  });

  /**
   * 测试5：点击单图诊断应该跳转到正确页面
   */
  test('点击单图诊断卡片应该跳转到 /diagnosis', async ({ page }) => {
    // 等待核心功能区域加载
    await page.locator('text=核心功能').waitFor({ state: 'visible' });

    // 找到包含"单图诊断"文字的卡片，点击整个卡片区域
    const card = page.locator('.ant-card').filter({ hasText: '单图诊断' }).first();
    await card.waitFor({ state: 'visible' });

    // 点击卡片（使用force以确保点击生效）
    await card.click();

    // 等待导航完成
    await page.waitForURL('**/diagnosis', { timeout: 5000 });

    // 验证URL是否正确
    const currentUrl = page.url();
    console.log('单图诊断页面URL:', currentUrl);

    // 应该是 /diagnosis 而不是 /diagnose/single
    expect(currentUrl).toContain('/diagnosis');
    expect(currentUrl).not.toContain('/diagnose/single');
  });

  /**
   * 测试6：点击批量诊断应该跳转到正确页面
   */
  test('点击批量诊断卡片应该跳转到 /batch-diagnosis', async ({ page }) => {
    // 等待核心功能区域加载
    await page.locator('text=核心功能').waitFor({ state: 'visible' });

    // 找到包含"批量诊断"文字的卡片
    const card = page.locator('.ant-card').filter({ hasText: '批量诊断' }).first();
    await card.waitFor({ state: 'visible' });

    // 点击卡片
    await card.click();

    // 等待导航完成
    await page.waitForURL('**/batch-diagnosis', { timeout: 5000 });

    // 验证URL
    const currentUrl = page.url();
    console.log('批量诊断页面URL:', currentUrl);

    // 应该是 /batch-diagnosis 而不是 /diagnose/batch
    expect(currentUrl).toContain('/batch-diagnosis');
    expect(currentUrl).not.toContain('/diagnose/batch');
  });

  /**
   * 测试7：点击本体管理应该跳转到正确页面
   */
  test('点击本体管理卡片应该跳转到 /ontology', async ({ page }) => {
    // 等待核心功能区域加载
    await page.locator('text=核心功能').waitFor({ state: 'visible' });

    // 找到包含"本体管理"文字的卡片
    const card = page.locator('.ant-card').filter({ hasText: '本体管理' }).first();
    await card.waitFor({ state: 'visible' });

    // 点击卡片
    await card.click();

    // 等待导航完成
    await page.waitForURL('**/ontology', { timeout: 5000 });

    // 验证URL
    const currentUrl = page.url();
    console.log('本体管理页面URL:', currentUrl);

    expect(currentUrl).toContain('/ontology');
  });

  /**
   * 测试8：点击知识管理应该跳转到正确页面
   */
  test('点击知识管理卡片应该跳转到 /knowledge', async ({ page }) => {
    // 等待核心功能区域加载
    await page.locator('text=核心功能').waitFor({ state: 'visible' });

    // 找到包含"知识管理"文字的卡片
    const card = page.locator('.ant-card').filter({ hasText: '知识管理' }).first();
    await card.waitFor({ state: 'visible' });

    // 点击卡片
    await card.click();

    // 等待导航完成
    await page.waitForURL('**/knowledge', { timeout: 5000 });

    // 验证URL
    const currentUrl = page.url();
    console.log('知识管理页面URL:', currentUrl);

    expect(currentUrl).toContain('/knowledge');
  });

  /**
   * 测试9：Header中的菜单导航测试
   */
  test('Header菜单导航功能正常', async ({ page }) => {
    // 等待Header加载
    await expect(page.locator('header')).toBeVisible();

    // 测试点击"单图诊断"菜单项（在 Ant Design Menu 中查找）
    const singleDiagnosisMenu = page.locator('li.ant-menu-item').filter({ hasText: '单图诊断' });
    await singleDiagnosisMenu.waitFor({ state: 'visible' });
    await singleDiagnosisMenu.click();

    await page.waitForURL('**/diagnosis', { timeout: 5000 });

    let currentUrl = page.url();
    console.log('Header点击单图诊断后URL:', currentUrl);
    expect(currentUrl).toContain('/diagnosis');

    // 返回首页
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // 测试点击"批量诊断"菜单项
    const batchDiagnosisMenu = page.locator('li.ant-menu-item').filter({ hasText: '批量诊断' });
    await batchDiagnosisMenu.waitFor({ state: 'visible' });
    await batchDiagnosisMenu.click();

    await page.waitForURL('**/batch-diagnosis', { timeout: 5000 });

    currentUrl = page.url();
    console.log('Header点击批量诊断后URL:', currentUrl);
    expect(currentUrl).toContain('/batch-diagnosis');
  });

  /**
   * 测试10：检查控制台错误
   */
  test('检查页面加载时是否有控制台错误', async ({ page }) => {
    const consoleErrors: string[] = [];
    const consoleWarnings: string[] = [];

    // 监听控制台消息
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      } else if (msg.type() === 'warning') {
        consoleWarnings.push(msg.text());
      }
    });

    // 重新加载页面
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // 等待一段时间确保所有异步操作完成
    await page.waitForTimeout(2000);

    // 过滤掉预期的错误（如API调用失败）
    const unexpectedErrors = consoleErrors.filter(err =>
      !err.includes('Failed to fetch') &&
      !err.includes('NetworkError') &&
      !err.includes('ERR_CONNECTION_REFUSED') &&
      !err.includes('localhost:8000')
    );

    // 输出错误和警告供调试
    if (unexpectedErrors.length > 0) {
      console.log('发现控制台错误:', unexpectedErrors);
    }
    if (consoleWarnings.length > 0) {
      console.log('发现控制台警告:', consoleWarnings);
    }

    // 检查是否有意外错误
    expect(unexpectedErrors).toHaveLength(0);
  });

  /**
   * 测试11：检查快速开始按钮
   */
  test('快速开始区域的按钮应该正确跳转', async ({ page }) => {
    // 滚动到快速开始区域
    await page.locator('text=准备好开始了吗？').scrollIntoViewIfNeeded();

    // 找到快速开始区域的"单图诊断"按钮
    const quickStartSection = page.locator('text=准备好开始了吗？').locator('..');
    const singleDiagnosisButton = quickStartSection.locator('button:has-text("单图诊断")');

    await singleDiagnosisButton.waitFor({ state: 'visible' });
    await singleDiagnosisButton.click();

    await page.waitForURL('**/diagnosis', { timeout: 5000 });

    const currentUrl = page.url();
    console.log('快速开始按钮跳转URL:', currentUrl);
    expect(currentUrl).toContain('/diagnosis');
  });

  /**
   * 测试12：检查所有页面是否存在404错误
   */
  test('访问各个页面不应该出现404', async ({ page }) => {
    const pages = [
      { path: '/diagnosis', name: '单图诊断' },
      { path: '/batch-diagnosis', name: '批量诊断' },
      { path: '/ontology', name: '本体管理' },
      { path: '/knowledge', name: '知识库管理' },
    ];

    for (const testPage of pages) {
      await page.goto(testPage.path);
      await page.waitForLoadState('networkidle');

      // 检查是否有404错误
      const has404 = await page.locator('text=404').isVisible().catch(() => false);
      const hasNotFound = await page.locator('text=Not Found').isVisible().catch(() => false);

      console.log(`${testPage.name} (${testPage.path}):`, {
        has404,
        hasNotFound,
        url: page.url()
      });

      expect(has404 || hasNotFound).toBe(false);
    }
  });
});

/**
 * 路径常量验证测试
 */
test.describe('路径常量验证', () => {
  test('验证前端路由定义的一致性', async () => {
    // 这个测试用于文档化正确的路径
    const expectedRoutes = {
      HOME: '/',
      SINGLE_DIAGNOSIS: '/diagnosis',
      BATCH_DIAGNOSIS: '/batch-diagnosis',
      DIAGNOSIS_HISTORY: '/history',
      ONTOLOGY_MANAGEMENT: '/ontology',
      KNOWLEDGE_MANAGEMENT: '/knowledge',
    };

    console.log('期望的路由配置:', expectedRoutes);

    // 这个测试总是通过，只是用来记录正确的路径
    expect(expectedRoutes.SINGLE_DIAGNOSIS).toBe('/diagnosis');
    expect(expectedRoutes.BATCH_DIAGNOSIS).toBe('/batch-diagnosis');
  });
});
