"""
测试批量处理功能 - 捕获点击批量处理后的错误

作者：AI Testing Agent
日期：2025-11-13
"""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image


def create_test_images(num_images=3):
    """创建测试图片"""
    assets_dir = Path("d:/项目管理/PhytoOracle/demo/frontend_demo/assets/images")
    assets_dir.mkdir(parents=True, exist_ok=True)

    test_images = []
    disease_names = ["rose_black_spot", "rose_powdery_mildew", "cherry_brown_rot"]

    for i in range(num_images):
        disease_name = disease_names[i % len(disease_names)]
        filename = f"{disease_name}_test_{i+1:03d}.jpg"
        filepath = assets_dir / filename

        # 创建简单的测试图片
        img = Image.new('RGB', (800, 600), color=(100 + i*20, 150 + i*20, 100 + i*20))
        img.save(filepath)

        test_images.append(str(filepath))
        print(f"   创建测试图片: {filename}")

    return test_images


def test_batch_processing():
    """测试批量处理功能"""

    print("\n" + "=" * 80)
    print("批量处理功能测试")
    print("=" * 80)

    # 创建测试图片
    print("\n[1/6] 创建测试图片...")
    test_images = create_test_images(3)
    print(f"   [OK] 创建了 {len(test_images)} 张测试图片")

    with sync_playwright() as p:
        # 启动浏览器
        print("\n[2/6] 启动浏览器...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # 准备截图目录
        screenshot_dir = Path("d:/项目管理/PhytoOracle/demo/frontend_demo/screenshots/batch_test")
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 访问批量验证中心
            print("\n[3/6] 访问批量验证中心...")
            page.goto("http://localhost:8501/批量验证中心", timeout=30000)
            time.sleep(3)
            page.screenshot(path=str(screenshot_dir / "01_page_loaded.png"))
            print("   [OK] 页面加载完成")

            # 上传图片
            print("\n[4/6] 上传测试图片...")
            try:
                file_input = page.locator('input[type="file"]').first
                file_input.set_input_files(test_images)
                time.sleep(2)
                page.screenshot(path=str(screenshot_dir / "02_images_uploaded.png"))
                print(f"   [OK] 上传了 {len(test_images)} 张图片")
            except Exception as e:
                print(f"   [ERROR] 上传失败: {str(e)[:100]}")
                page.screenshot(path=str(screenshot_dir / "02_upload_error.png"))
                raise

            # 点击批量推理按钮
            print("\n[5/6] 点击批量推理按钮...")
            try:
                # 查找批量推理按钮
                inference_button = page.get_by_role("button", name="开始批量推理").first
                if not inference_button.is_visible(timeout=5000):
                    # 尝试其他可能的按钮名称
                    inference_button = page.locator("text=批量推理").first

                inference_button.click()
                print("   [OK] 点击推理按钮")

                # 等待推理完成
                print("   等待推理完成...")
                time.sleep(8)

                page.screenshot(path=str(screenshot_dir / "03_inference_started.png"))

            except Exception as e:
                print(f"   [ERROR] 点击推理按钮失败: {str(e)[:100]}")
                page.screenshot(path=str(screenshot_dir / "03_button_error.png"))
                raise

            # 检查推理结果和错误
            print("\n[6/6] 检查推理结果和错误信息...")
            time.sleep(2)

            # 滚动页面查看所有内容
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            page.screenshot(path=str(screenshot_dir / "04_scrolled_down.png"), full_page=True)

            # 检查是否有错误
            errors = check_for_errors(page, screenshot_dir)

            if errors:
                print(f"\n   [FOUND] 发现 {len(errors)} 个错误:")
                for i, error in enumerate(errors[:5]):  # 显示前5个
                    print(f"   [ERROR {i+1}]:")
                    print(f"      {error[:500]}")
                    print()
            else:
                print("   [OK] 未发现错误信息")

            # 检查结果表格
            check_results_table(page, screenshot_dir)

            print("\n" + "=" * 80)
            print("[OK] 批量处理测试完成")
            print(f"截图保存位置: {screenshot_dir}")
            print("=" * 80)

            # 保持浏览器打开10秒
            time.sleep(10)

        except Exception as e:
            error_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
            print(f"\n[ERROR] 测试失败: {error_msg}")
            page.screenshot(path=str(screenshot_dir / "error_final.png"))

        finally:
            browser.close()


def check_for_errors(page, screenshot_dir):
    """检查页面是否有错误消息"""
    errors_found = []

    # 多种错误选择器
    error_selectors = [
        "[class*='stException']",
        "[class*='stError']",
        "[data-testid='stException']",
        "div.element-container div[style*='color: rgb(255, 75, 75)']",
        "pre[class*='stException']",
        ".stAlert",
    ]

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

    # 截图错误位置
    if errors_found:
        page.screenshot(path=str(screenshot_dir / "05_errors_detected.png"), full_page=True)

    return errors_found


def check_results_table(page, screenshot_dir):
    """检查结果表格"""
    print("\n   检查结果表格...")

    try:
        # 查找结果相关文本
        result_texts = [
            "条结果",
            "结果表格",
            "推理结果",
            "0/3",
        ]

        for text in result_texts:
            try:
                elements = page.locator(f"text={text}").all()
                if elements:
                    print(f"   [FOUND] 找到文本: '{text}' ({len(elements)} 处)")
            except:
                pass

        # 检查表格
        try:
            tables = page.locator("table").all()
            if tables:
                print(f"   [FOUND] 找到 {len(tables)} 个表格")
            else:
                print("   [WARN] 未找到表格元素")
        except:
            pass

    except Exception as e:
        error_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
        print(f"   [ERROR] 表格检查失败: {error_msg}")


if __name__ == "__main__":
    test_batch_processing()
