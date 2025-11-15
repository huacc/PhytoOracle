/**
 * Playwright 测试配置文件
 * 配置 E2E 测试环境和参数
 */

import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright 配置
 * 详见：https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  // 测试文件目录
  testDir: './tests/e2e',

  // 单个测试最大执行时间（30秒）
  timeout: 30 * 1000,

  // 并行执行测试
  fullyParallel: true,

  // 在CI环境中，失败时禁止重试
  forbidOnly: !!process.env.CI,

  // 重试次数（CI环境中重试2次）
  retries: process.env.CI ? 2 : 0,

  // 并行工作线程数（CI环境中使用1个）
  workers: process.env.CI ? 1 : undefined,

  // 测试报告配置
  reporter: [
    ['html'],
    ['list'],
  ],

  // 共享配置
  use: {
    // 基础URL
    baseURL: 'http://localhost:3000',

    // 收集失败测试的追踪信息
    trace: 'on-first-retry',

    // 截图设置
    screenshot: 'only-on-failure',

    // 视频录制
    video: 'retain-on-failure',
  },

  // 配置测试项目（浏览器）
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // 开发服务器配置（如果需要自动启动）
  // webServer: {
  //   command: 'npm run dev',
  //   url: 'http://localhost:3000',
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120 * 1000,
  // },
});
