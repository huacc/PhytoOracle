# PhytoOracle 前端 E2E 测试

## 概述

本项目使用 Playwright 进行端到端（E2E）测试，确保前端导航和用户交互功能正常。

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

在运行测试前，确保开发服务器正在运行：

```bash
npm run dev
```

服务器将在 `http://localhost:3000` 启动。

### 3. 运行测试

在新的终端窗口中运行测试：

```bash
# 运行所有测试（无头模式）
npm run test:e2e

# 在浏览器中运行测试（可视化模式）
npm run test:e2e:headed

# 使用 UI 模式运行测试（推荐用于调试）
npm run test:e2e:ui

# 调试模式
npm run test:e2e:debug
```

## 测试脚本

| 命令 | 说明 |
|------|------|
| `npm run test:e2e` | 运行所有测试（无头模式，快速） |
| `npm run test:e2e:headed` | 在浏览器中运行测试（可视化） |
| `npm run test:e2e:ui` | 使用 Playwright UI 模式 |
| `npm run test:e2e:debug` | 调试模式，逐步执行 |

## 测试覆盖范围

当前测试套件包含 13 个测试用例，覆盖以下功能：

### 1. 页面加载
- ✅ 主页正确加载
- ✅ 所有页面无 404 错误

### 2. 导航功能
- ✅ Header 导航菜单链接
- ✅ 功能卡片点击跳转
- ✅ 快速开始按钮

### 3. 路径验证
- ✅ 检查错误路径
- ✅ 验证路由常量

### 4. 错误检查
- ✅ 控制台错误检测
- ✅ 404 错误检测

## 测试文件结构

```
frontend/
├── tests/
│   └── e2e/
│       └── navigation.spec.ts    # 导航测试套件
├── playwright.config.ts           # Playwright 配置
└── package.json                   # 测试脚本定义
```

## 查看测试报告

测试完成后，Playwright 会自动生成 HTML 报告：

```bash
# 查看最近的测试报告
npx playwright show-report
```

报告包含：
- 测试执行摘要
- 失败测试的截图
- 失败测试的视频录制
- 详细的执行日志

## 常见问题

### Q: 测试失败，提示"Timeout waiting for..."

**A**: 确保开发服务器正在运行（`http://localhost:3000`）。

### Q: 如何只运行特定的测试？

**A**: 使用 Playwright 的过滤功能：

```bash
# 运行特定文件
npx playwright test navigation.spec.ts

# 运行包含特定名称的测试
npx playwright test -g "单图诊断"
```

### Q: 如何调试失败的测试？

**A**: 使用 UI 模式或调试模式：

```bash
# UI 模式（推荐）
npm run test:e2e:ui

# 调试模式
npm run test:e2e:debug
```

## 最佳实践

1. **在提交代码前运行测试**：确保所有测试通过
2. **更新路由时更新测试**：添加新页面或修改路由时，相应更新测试
3. **查看失败的截图**：测试失败时，检查自动生成的截图和视频
4. **保持测试简洁**：每个测试应该专注于一个功能点

## 技术栈

- **测试框架**: Playwright v1.56.1
- **前端框架**: Next.js 15.0.0
- **UI 库**: Ant Design 5.28.1
- **语言**: TypeScript

## 更多资源

- [Playwright 官方文档](https://playwright.dev/)
- [Next.js 测试文档](https://nextjs.org/docs/testing)
- [项目测试报告](../docs/reports/)

---

**注意**: 本测试套件专注于前端导航和UI交互，不涉及后端API测试。后端API测试请参考 `backend/tests/` 目录。
