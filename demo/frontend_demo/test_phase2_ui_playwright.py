"""
PhytoOracle Frontend Demo - Playwright UI 自动化测试（阶段2）

测试范围：
1. 批量验证中心
2. 统计分析
3. 知识库管理

作者：AI Testing Agent
日期：2025-11-13
"""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright


def test_phase2_pages():
    """测试阶段2的所有页面"""

    print("\n" + "=" * 80)
    print("PhytoOracle Frontend Demo - Phase 2 UI 自动化测试")
    print("=" * 80)

    with sync_playwright() as p:
        # 启动浏览器
        print("\n[1/4] 启动浏览器...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # 准备截图目录
        screenshot_dir = Path("d:/项目管理/PhytoOracle/demo/frontend_demo/screenshots/phase2")
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 访问应用主页
            print("[2/4] 访问应用主页...")
            page.goto("http://localhost:8501", timeout=30000)
            time.sleep(3)
            page.screenshot(path=str(screenshot_dir / "00_homepage.png"))
            print("   [OK] 主页加载成功")

            # 测试批量验证中心
            print("\n[3/4] 测试批量验证中心...")
            test_batch_validation_center(page, screenshot_dir)

            # 测试统计分析
            print("\n[4/4] 测试统计分析...")
            test_statistics_analysis(page, screenshot_dir)

            # 测试知识库管理
            print("\n[5/4] 测试知识库管理...")
            test_knowledge_management(page, screenshot_dir)

            print("\n" + "=" * 80)
            print("[OK] 阶段2所有页面测试完成！")
            print(f"截图保存位置: {screenshot_dir}")
            print("=" * 80)

            # 保持浏览器打开5秒
            time.sleep(5)

        except Exception as e:
            error_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
            print(f"\n[ERROR] 测试过程中发生错误: {error_msg}")
            page.screenshot(path=str(screenshot_dir / "error_general.png"))

            # 捕获页面内容以查看错误
            print("\n[DEBUG] 尝试捕获错误信息...")
            try:
                # 查找错误消息
                error_elements = page.locator("[class*='stException']").all()
                if error_elements:
                    print(f"   发现 {len(error_elements)} 个异常")
                    for i, elem in enumerate(error_elements):
                        error_text = elem.text_content()
                        print(f"   异常 {i+1}: {error_text[:200]}")
            except:
                pass

        finally:
            browser.close()


def test_batch_validation_center(page, screenshot_dir):
    """测试批量验证中心页面"""
    try:
        print("   [STEP 1] 导航到批量验证中心...")

        # 尝试多种方式导航
        nav_success = False

        # 方式1: 点击侧边栏链接
        try:
            batch_link = page.locator("text=批量验证中心").first
            if batch_link.is_visible(timeout=5000):
                batch_link.click()
                time.sleep(3)
                nav_success = True
                print("   [OK] 通过侧边栏链接进入")
        except:
            pass

        # 方式2: 直接访问URL
        if not nav_success:
            try:
                page.goto("http://localhost:8501/批量验证中心", timeout=30000)
                time.sleep(3)
                nav_success = True
                print("   [OK] 通过URL进入")
            except:
                pass

        if not nav_success:
            print("   [ERROR] 无法导航到批量验证中心")
            page.screenshot(path=str(screenshot_dir / "01_batch_nav_failed.png"))
            return

        # 截图：初始页面
        page.screenshot(path=str(screenshot_dir / "01_batch_initial.png"))

        # 检查页面标题
        print("   [STEP 2] 检查页面元素...")
        try:
            title_visible = page.locator("text=批量验证").first.is_visible(timeout=5000)
            if title_visible:
                print("   [OK] 找到页面标题")
            else:
                print("   [WARN] 未找到页面标题")
        except Exception as e:
            print(f"   [ERROR] 标题检查失败: {str(e)[:100]}")

        # 检查是否有错误消息
        print("   [STEP 3] 检查错误信息...")
        check_for_errors(page, "batch_validation")

        # 截图：最终状态
        page.screenshot(path=str(screenshot_dir / "01_batch_final.png"), full_page=True)
        print("   [OK] 批量验证中心测试完成")

    except Exception as e:
        error_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
        print(f"   [ERROR] 批量验证中心测试失败: {error_msg}")
        page.screenshot(path=str(screenshot_dir / "01_batch_error.png"))


def test_statistics_analysis(page, screenshot_dir):
    """测试统计分析页面"""
    try:
        print("   [STEP 1] 导航到统计分析...")

        # 尝试多种方式导航
        nav_success = False

        # 方式1: 点击侧边栏链接
        try:
            stats_link = page.locator("text=统计分析").first
            if stats_link.is_visible(timeout=5000):
                stats_link.click()
                time.sleep(3)
                nav_success = True
                print("   [OK] 通过侧边栏链接进入")
        except:
            pass

        # 方式2: 直接访问URL
        if not nav_success:
            try:
                page.goto("http://localhost:8501/统计分析", timeout=30000)
                time.sleep(3)
                nav_success = True
                print("   [OK] 通过URL进入")
            except:
                pass

        if not nav_success:
            print("   [ERROR] 无法导航到统计分析")
            page.screenshot(path=str(screenshot_dir / "02_stats_nav_failed.png"))
            return

        # 截图：初始页面
        page.screenshot(path=str(screenshot_dir / "02_stats_initial.png"))

        # 检查页面标题
        print("   [STEP 2] 检查页面元素...")
        try:
            title_visible = page.locator("text=统计分析").first.is_visible(timeout=5000)
            if title_visible:
                print("   [OK] 找到页面标题")
            else:
                print("   [WARN] 未找到页面标题")
        except Exception as e:
            print(f"   [ERROR] 标题检查失败: {str(e)[:100]}")

        # 检查是否有错误消息
        print("   [STEP 3] 检查错误信息...")
        check_for_errors(page, "statistics_analysis")

        # 截图：最终状态
        page.screenshot(path=str(screenshot_dir / "02_stats_final.png"), full_page=True)
        print("   [OK] 统计分析测试完成")

    except Exception as e:
        error_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
        print(f"   [ERROR] 统计分析测试失败: {error_msg}")
        page.screenshot(path=str(screenshot_dir / "02_stats_error.png"))


def test_knowledge_management(page, screenshot_dir):
    """测试知识库管理页面"""
    try:
        print("   [STEP 1] 导航到知识库管理...")

        # 尝试多种方式导航
        nav_success = False

        # 方式1: 点击侧边栏链接
        try:
            kb_link = page.locator("text=知识库管理").first
            if kb_link.is_visible(timeout=5000):
                kb_link.click()
                time.sleep(3)
                nav_success = True
                print("   [OK] 通过侧边栏链接进入")
        except:
            pass

        # 方式2: 直接访问URL
        if not nav_success:
            try:
                page.goto("http://localhost:8501/知识库管理", timeout=30000)
                time.sleep(3)
                nav_success = True
                print("   [OK] 通过URL进入")
            except:
                pass

        if not nav_success:
            print("   [ERROR] 无法导航到知识库管理")
            page.screenshot(path=str(screenshot_dir / "03_kb_nav_failed.png"))
            return

        # 截图：初始页面
        page.screenshot(path=str(screenshot_dir / "03_kb_initial.png"))

        # 检查页面标题
        print("   [STEP 2] 检查页面元素...")
        try:
            title_visible = page.locator("text=知识库").first.is_visible(timeout=5000)
            if title_visible:
                print("   [OK] 找到页面标题")
            else:
                print("   [WARN] 未找到页面标题")
        except Exception as e:
            print(f"   [ERROR] 标题检查失败: {str(e)[:100]}")

        # 检查是否有错误消息
        print("   [STEP 3] 检查错误信息...")
        check_for_errors(page, "knowledge_management")

        # 截图：最终状态
        page.screenshot(path=str(screenshot_dir / "03_kb_final.png"), full_page=True)
        print("   [OK] 知识库管理测试完成")

    except Exception as e:
        error_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
        print(f"   [ERROR] 知识库管理测试失败: {error_msg}")
        page.screenshot(path=str(screenshot_dir / "03_kb_error.png"))


def check_for_errors(page, page_name):
    """检查页面是否有错误消息"""
    try:
        # 等待页面完全加载
        time.sleep(2)

        # 检查Streamlit错误
        error_selectors = [
            "[class*='stException']",
            "[class*='stError']",
            "[data-testid='stException']",
            "div.element-container div[style*='color: rgb(255, 75, 75)']",
            "pre[class*='stException']"
        ]

        errors_found = []

        for selector in error_selectors:
            try:
                elements = page.locator(selector).all()
                if elements:
                    for elem in elements:
                        try:
                            error_text = elem.text_content()
                            if error_text and len(error_text.strip()) > 0:
                                errors_found.append(error_text)
                        except:
                            pass
            except:
                pass

        if errors_found:
            print(f"   [FOUND] 发现 {len(errors_found)} 个错误信息:")
            for i, error in enumerate(errors_found[:3]):  # 只显示前3个
                # 清理错误文本
                error_clean = error.strip()[:300]
                error_clean = error_clean.encode('ascii', errors='ignore').decode('ascii')
                print(f"   [ERROR {i+1}] {error_clean}")
        else:
            print("   [OK] 未发现错误信息")

        return errors_found

    except Exception as e:
        error_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
        print(f"   [WARN] 错误检查失败: {error_msg}")
        return []


if __name__ == "__main__":
    test_phase2_pages()
