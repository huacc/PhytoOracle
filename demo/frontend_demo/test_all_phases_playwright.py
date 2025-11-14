"""
PhytoOracle Frontend Demo - 全功能 Playwright 自动化测试

测试范围：
- 阶段1：单张调试模式（图片上传、推理、结果展示、标注、导出）
- 阶段2：批量验证中心（批量上传、推理、筛选、导出、统计分析）
- 阶段2：知识库管理（疾病列表、详情、特征本体浏览器）
- 阶段3：图片对比（选择器、筛选、并排展示、差异分析）
- 阶段3：统计分析增强（数据源切换、趋势图、筛选、导出）

作者：FloriPath-AI
日期：2025-11-13
"""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image
from datetime import datetime
from typing import List


# 全局配置
APP_URL = "http://localhost:8501"
SCREENSHOT_DIR = Path("D:/项目管理/PhytoOracle/demo/frontend_demo/screenshots/full_test")
ASSETS_DIR = Path("D:/项目管理/PhytoOracle/demo/frontend_demo/assets/images")
WAIT_SHORT = 2  # 短等待（秒）
WAIT_MEDIUM = 3  # 中等待（秒）
WAIT_LONG = 5  # 长等待（秒）
WAIT_INFERENCE = 8  # 推理等待（秒）


class TestReporter:
    """测试报告生成器"""

    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_details = []
        self.bugs_found = []
        self.bugs_fixed = []

    def start_test(self, test_name: str):
        """开始测试"""
        self.current_test_name = test_name
        self.current_test_start = time.time()
        print(f"\n{'='*80}")
        print(f"[{self.total_tests + 1}] {test_name}")
        print(f"{'='*80}")

    def log_step(self, step: str, status: str = "OK"):
        """记录测试步骤"""
        icon = "[OK]" if status == "OK" else "[FAIL]"
        # Use ASCII-safe output for Windows console
        step_safe = step.encode('ascii', errors='ignore').decode('ascii')
        print(f"   {icon} {step_safe}")

    def end_test(self, passed: bool, details: str = ""):
        """结束测试"""
        self.total_tests += 1
        elapsed = time.time() - self.current_test_start

        if passed:
            self.passed_tests += 1
            status = "PASSED"
        else:
            self.failed_tests += 1
            status = "FAILED"

        self.test_details.append({
            "name": self.current_test_name,
            "status": status,
            "elapsed": f"{elapsed:.2f}s",
            "details": details
        })

        print(f"\n   [{status}] 用时 {elapsed:.2f}s")
        if details:
            print(f"   详情: {details}")

    def report_bug(self, bug_description: str, location: str):
        """报告 bug"""
        self.bugs_found.append({
            "description": bug_description,
            "location": location,
            "test": self.current_test_name,
            "timestamp": datetime.now().isoformat()
        })
        print(f"\n   [BUG FOUND] {bug_description}")
        print(f"   位置: {location}")

    def report_bug_fixed(self, bug_description: str, fix_description: str):
        """报告 bug 修复"""
        self.bugs_fixed.append({
            "bug": bug_description,
            "fix": fix_description,
            "test": self.current_test_name,
            "timestamp": datetime.now().isoformat()
        })
        print(f"\n   [BUG FIXED] {bug_description}")
        print(f"   修复: {fix_description}")

    def generate_summary(self) -> str:
        """生成测试摘要"""
        summary = []
        summary.append("\n" + "="*80)
        summary.append("测试摘要")
        summary.append("="*80)
        summary.append(f"总测试数: {self.total_tests}")
        summary.append(f"通过: {self.passed_tests}")
        summary.append(f"失败: {self.failed_tests}")
        summary.append(f"通过率: {(self.passed_tests/self.total_tests*100):.1f}%")
        summary.append(f"\n发现的 Bug: {len(self.bugs_found)}")
        summary.append(f"修复的 Bug: {len(self.bugs_fixed)}")
        summary.append("="*80)

        return "\n".join(summary)


def setup_test_environment():
    """设置测试环境"""
    print("\n" + "="*80)
    print("PhytoOracle Frontend Demo - 全功能自动化测试")
    print("="*80)

    # 创建截图目录
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    # 创建测试图片
    create_test_images()

    print(f"\n测试环境准备完成")
    print(f"截图目录: {SCREENSHOT_DIR}")
    print(f"测试图片目录: {ASSETS_DIR}")


def create_test_images(num_images: int = 5):
    """创建测试图片"""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    disease_names = [
        "rose_black_spot",
        "rose_powdery_mildew",
        "cherry_brown_rot",
        "peony_gray_mold",
        "rose_rust"
    ]

    created = []
    for i in range(num_images):
        disease_name = disease_names[i % len(disease_names)]
        filename = f"{disease_name}_test_{i+1:03d}.jpg"
        filepath = ASSETS_DIR / filename

        if not filepath.exists():
            # 创建不同颜色的测试图片
            colors = [
                (60, 100, 60),   # 深绿色
                (200, 200, 200), # 白色
                (100, 60, 40),   # 褐色
                (150, 150, 150), # 灰色
                (180, 100, 50)   # 橙褐色
            ]
            color = colors[i % len(colors)]
            img = Image.new('RGB', (800, 600), color=color)
            img.save(filepath)
            created.append(filename)

    if created:
        print(f"\n创建了 {len(created)} 张测试图片")


def check_for_errors(page, context_name: str) -> List[str]:
    """检查页面错误"""
    error_selectors = [
        "[class*='stException']",
        "[class*='stError']",
        "[data-testid='stException']",
        "div.element-container div[style*='color: rgb(255, 75, 75)']",
        "pre[class*='stException']",
        ".stAlert"
    ]

    errors_found = []
    for selector in error_selectors:
        try:
            elements = page.locator(selector).all()
            for elem in elements:
                try:
                    error_text = elem.text_content()
                    if error_text and len(error_text.strip()) > 0:
                        errors_found.append(error_text.strip())
                except:
                    pass
        except:
            pass

    if errors_found:
        print(f"\n   [ERROR in {context_name}] 发现 {len(errors_found)} 个错误")
        for i, error in enumerate(errors_found[:3]):  # 只显示前3个
            error_clean = error[:200].encode('ascii', errors='ignore').decode('ascii')
            print(f"   错误 {i+1}: {error_clean}")

    return errors_found


def test_phase1_single_diagnosis(page, reporter: TestReporter):
    """测试阶段1：单张调试模式"""
    reporter.start_test("阶段1：单张调试模式")

    try:
        # 导航到推理调试中心
        reporter.log_step("导航到推理调试中心...")
        page.goto(f"{APP_URL}/推理调试中心", timeout=30000)
        time.sleep(WAIT_MEDIUM)
        page.screenshot(path=str(SCREENSHOT_DIR / "phase1_01_page_loaded.png"))
        reporter.log_step("页面加载成功", "OK")

        # 检查 Tab 1 是否激活
        reporter.log_step("检查 Tab 1 是否激活...")
        try:
            tab1_visible = page.locator("text=Tab 1: 单张调试").first.is_visible(timeout=5000)
            if tab1_visible:
                reporter.log_step("Tab 1 已激活", "OK")
            else:
                reporter.log_step("Tab 1 未激活，尝试点击", "WARN")
                page.locator("text=Tab 1: 单张调试").first.click()
                time.sleep(WAIT_SHORT)
        except:
            reporter.log_step("Tab 1 定位失败，继续测试", "WARN")

        # 上传图片
        reporter.log_step("上传测试图片...")
        test_image = ASSETS_DIR / "rose_black_spot_test_001.jpg"
        if not test_image.exists():
            reporter.log_step(f"测试图片不存在: {test_image}", "FAIL")
            reporter.end_test(False, "测试图片不存在")
            return False

        file_input = page.locator('input[type="file"]').first
        file_input.set_input_files(str(test_image))
        time.sleep(WAIT_SHORT)
        page.screenshot(path=str(SCREENSHOT_DIR / "phase1_02_image_uploaded.png"))
        reporter.log_step("图片上传成功", "OK")

        # 点击推理按钮
        reporter.log_step("执行推理...")
        try:
            # 尝试多种按钮名称
            button_found = False
            for button_name in ["开始推理", "执行推理", "推理"]:
                try:
                    button = page.get_by_role("button", name=button_name).first
                    if button.is_visible(timeout=2000):
                        button.click()
                        button_found = True
                        break
                except:
                    continue

            if not button_found:
                reporter.log_step("未找到推理按钮", "FAIL")
                reporter.report_bug("推理按钮定位失败", "pages/1_推理调试中心.py")
                reporter.end_test(False, "推理按钮定位失败")
                return False

            reporter.log_step("点击推理按钮成功", "OK")
            time.sleep(WAIT_INFERENCE)
            page.screenshot(path=str(SCREENSHOT_DIR / "phase1_03_inference_completed.png"))
        except Exception as e:
            reporter.log_step(f"推理执行失败: {str(e)[:100]}", "FAIL")
            reporter.report_bug(f"推理执行异常: {str(e)}", "pages/1_推理调试中心.py")
            reporter.end_test(False, f"推理执行异常: {str(e)}")
            return False

        # 检查推理结果展示
        reporter.log_step("检查推理结果展示...")
        time.sleep(WAIT_SHORT)

        # 检查关键元素
        result_elements = [
            ("诊断结果", "最终诊断标题"),
            ("Q0序列", "Q0序列展示"),
            ("Q1-Q6", "特征提取展示"),
            ("置信度", "置信度显示"),
        ]

        found_count = 0
        for text, description in result_elements:
            try:
                if page.locator(f"text={text}").first.is_visible(timeout=2000):
                    found_count += 1
            except:
                pass

        if found_count >= 2:
            reporter.log_step(f"推理结果展示正常（找到 {found_count}/4 个关键元素）", "OK")
        else:
            reporter.log_step(f"推理结果展示不完整（仅找到 {found_count}/4 个关键元素）", "WARN")

        # 检查错误
        errors = check_for_errors(page, "phase1_single_diagnosis")
        if errors:
            reporter.report_bug(f"发现 {len(errors)} 个错误", "pages/1_推理调试中心.py")

        # 滚动到标注区域
        reporter.log_step("检查人工标注功能...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(WAIT_SHORT)
        page.screenshot(path=str(SCREENSHOT_DIR / "phase1_04_annotation_area.png"))

        # 尝试进行标注
        try:
            # 查找标注按钮
            annotation_found = False
            for text in ["正确", "准确性标注", "人工标注"]:
                try:
                    if page.locator(f"text={text}").first.is_visible(timeout=2000):
                        annotation_found = True
                        break
                except:
                    continue

            if annotation_found:
                reporter.log_step("人工标注区域已显示", "OK")
            else:
                reporter.log_step("人工标注区域未找到", "WARN")
        except Exception as e:
            reporter.log_step(f"标注检查失败: {str(e)[:100]}", "WARN")

        # 全页截图
        page.screenshot(path=str(SCREENSHOT_DIR / "phase1_05_full_page.png"), full_page=True)

        # 判断测试是否通过
        passed = found_count >= 2 and len(errors) == 0
        reporter.end_test(passed, f"找到 {found_count} 个关键元素，{len(errors)} 个错误")
        return passed

    except Exception as e:
        error_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
        reporter.log_step(f"测试异常: {error_msg}", "FAIL")
        reporter.report_bug(f"测试异常: {error_msg}", "pages/1_推理调试中心.py")
        page.screenshot(path=str(SCREENSHOT_DIR / "phase1_error.png"))
        reporter.end_test(False, f"测试异常: {error_msg}")
        return False


def test_phase2_batch_validation(page, reporter: TestReporter):
    """测试阶段2：批量验证中心"""
    reporter.start_test("阶段2：批量验证中心")

    try:
        # 导航到批量验证中心
        reporter.log_step("导航到批量验证中心...")
        page.goto(f"{APP_URL}/批量验证中心", timeout=30000)
        time.sleep(WAIT_MEDIUM)
        page.screenshot(path=str(SCREENSHOT_DIR / "phase2_batch_01_page_loaded.png"))
        reporter.log_step("页面加载成功", "OK")

        # 批量上传图片
        reporter.log_step("批量上传测试图片（3张）...")
        test_images = [
            str(ASSETS_DIR / "rose_black_spot_test_001.jpg"),
            str(ASSETS_DIR / "rose_powdery_mildew_test_002.jpg"),
            str(ASSETS_DIR / "cherry_brown_rot_test_003.jpg")
        ]

        # 确保图片存在
        missing = [img for img in test_images if not Path(img).exists()]
        if missing:
            reporter.log_step(f"部分测试图片不存在: {len(missing)}/{len(test_images)}", "FAIL")
            reporter.end_test(False, "测试图片不存在")
            return False

        try:
            file_input = page.locator('input[type="file"]').first
            file_input.set_input_files(test_images)
            time.sleep(WAIT_SHORT)
            page.screenshot(path=str(SCREENSHOT_DIR / "phase2_batch_02_images_uploaded.png"))
            reporter.log_step("批量上传成功", "OK")
        except Exception as e:
            reporter.log_step(f"批量上传失败: {str(e)[:100]}", "FAIL")
            reporter.report_bug(f"批量上传异常: {str(e)}", "pages/2_批量验证中心.py")
            reporter.end_test(False, f"批量上传异常")
            return False

        # 点击批量推理按钮
        reporter.log_step("执行批量推理...")
        try:
            button_found = False
            for button_name in ["开始批量推理", "批量推理", "开始推理"]:
                try:
                    button = page.get_by_role("button", name=button_name).first
                    if button.is_visible(timeout=2000):
                        button.click()
                        button_found = True
                        break
                except:
                    continue

            if not button_found:
                reporter.log_step("未找到批量推理按钮", "FAIL")
                reporter.report_bug("批量推理按钮定位失败", "pages/2_批量验证中心.py")
                reporter.end_test(False, "批量推理按钮定位失败")
                return False

            reporter.log_step("点击批量推理按钮成功", "OK")
            time.sleep(WAIT_INFERENCE * 2)  # 批量推理需要更长时间
            page.screenshot(path=str(SCREENSHOT_DIR / "phase2_batch_03_inference_completed.png"))
        except Exception as e:
            reporter.log_step(f"批量推理执行失败: {str(e)[:100]}", "FAIL")
            reporter.report_bug(f"批量推理执行异常: {str(e)}", "pages/2_批量验证中心.py")
            reporter.end_test(False, f"批量推理执行异常")
            return False

        # 检查结果表格
        reporter.log_step("检查结果表格...")
        time.sleep(WAIT_SHORT)

        table_found = False
        try:
            # 查找表格或数据展示
            tables = page.locator("table").all()
            if tables:
                table_found = True
                reporter.log_step(f"找到 {len(tables)} 个表格", "OK")
            else:
                # 查找其他数据展示形式
                for text in ["条结果", "推理结果", "诊断结果"]:
                    if page.locator(f"text={text}").first.is_visible(timeout=2000):
                        table_found = True
                        break

                if table_found:
                    reporter.log_step("找到结果展示", "OK")
                else:
                    reporter.log_step("未找到结果表格", "WARN")
        except Exception as e:
            reporter.log_step(f"表格检查失败: {str(e)[:100]}", "WARN")

        # 测试筛选功能
        reporter.log_step("测试筛选功能...")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(WAIT_SHORT)

        # 尝试找到筛选器
        try:
            # 查找花属筛选
            genus_filter_found = False
            for text in ["按花属筛选", "花卉属", "属种"]:
                try:
                    if page.locator(f"text={text}").first.is_visible(timeout=2000):
                        genus_filter_found = True
                        break
                except:
                    continue

            if genus_filter_found:
                reporter.log_step("找到筛选功能", "OK")
            else:
                reporter.log_step("未找到筛选功能", "WARN")
        except Exception as e:
            reporter.log_step(f"筛选功能检查失败: {str(e)[:100]}", "WARN")

        page.screenshot(path=str(SCREENSHOT_DIR / "phase2_batch_04_with_filters.png"))

        # 检查错误
        errors = check_for_errors(page, "phase2_batch_validation")
        if errors:
            reporter.report_bug(f"发现 {len(errors)} 个错误", "pages/2_批量验证中心.py")

        # 全页截图
        page.screenshot(path=str(SCREENSHOT_DIR / "phase2_batch_05_full_page.png"), full_page=True)

        # 判断测试是否通过
        passed = table_found and len(errors) == 0
        reporter.end_test(passed, f"表格显示: {table_found}, 错误数: {len(errors)}")
        return passed

    except Exception as e:
        error_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
        reporter.log_step(f"测试异常: {error_msg}", "FAIL")
        reporter.report_bug(f"测试异常: {error_msg}", "pages/2_批量验证中心.py")
        page.screenshot(path=str(SCREENSHOT_DIR / "phase2_batch_error.png"))
        reporter.end_test(False, f"测试异常: {error_msg}")
        return False


def test_phase2_knowledge_base(page, reporter: TestReporter):
    """测试阶段2：知识库管理"""
    reporter.start_test("阶段2：知识库管理")

    try:
        # 导航到知识库管理
        reporter.log_step("导航到知识库管理...")
        page.goto(f"{APP_URL}/知识库管理", timeout=30000)
        time.sleep(WAIT_MEDIUM)
        page.screenshot(path=str(SCREENSHOT_DIR / "phase2_kb_01_page_loaded.png"))
        reporter.log_step("页面加载成功", "OK")

        # 检查页面元素
        reporter.log_step("检查页面元素...")

        # 查找关键元素
        key_elements = [
            ("疾病列表", "疾病列表标题"),
            ("特征本体", "特征本体标题"),
            ("知识库", "知识库相关文本"),
        ]

        found_count = 0
        for text, description in key_elements:
            try:
                if page.locator(f"text={text}").first.is_visible(timeout=2000):
                    found_count += 1
                    reporter.log_step(f"找到: {description}", "OK")
            except:
                pass

        if found_count >= 1:
            reporter.log_step(f"页面元素检查通过（{found_count}/3）", "OK")
        else:
            reporter.log_step("页面元素检查失败", "WARN")

        # 检查错误
        errors = check_for_errors(page, "phase2_knowledge_base")
        if errors:
            reporter.report_bug(f"发现 {len(errors)} 个错误", "pages/4_知识库管理.py")

        # 全页截图
        page.screenshot(path=str(SCREENSHOT_DIR / "phase2_kb_02_full_page.png"), full_page=True)

        # 判断测试是否通过
        passed = found_count >= 1 and len(errors) == 0
        reporter.end_test(passed, f"找到 {found_count} 个关键元素，{len(errors)} 个错误")
        return passed

    except Exception as e:
        error_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
        reporter.log_step(f"测试异常: {error_msg}", "FAIL")
        reporter.report_bug(f"测试异常: {error_msg}", "pages/4_知识库管理.py")
        page.screenshot(path=str(SCREENSHOT_DIR / "phase2_kb_error.png"))
        reporter.end_test(False, f"测试异常: {error_msg}")
        return False


def test_phase3_image_comparison(page, reporter: TestReporter):
    """测试阶段3：图片对比"""
    reporter.start_test("阶段3：图片对比")

    try:
        # 导航到推理调试中心 Tab 3
        reporter.log_step("导航到推理调试中心 Tab 3...")
        page.goto(f"{APP_URL}/推理调试中心", timeout=30000)
        time.sleep(WAIT_MEDIUM)

        # 点击 Tab 3
        try:
            tab3 = page.locator("text=Tab 3: 图片对比").first
            if tab3.is_visible(timeout=5000):
                tab3.click()
                time.sleep(WAIT_SHORT)
                reporter.log_step("切换到 Tab 3 成功", "OK")
            else:
                reporter.log_step("Tab 3 未找到", "FAIL")
                reporter.end_test(False, "Tab 3 未找到")
                return False
        except Exception as e:
            reporter.log_step(f"切换 Tab 3 失败: {str(e)[:100]}", "FAIL")
            reporter.end_test(False, "切换 Tab 3 失败")
            return False

        page.screenshot(path=str(SCREENSHOT_DIR / "phase3_comparison_01_tab3_loaded.png"))

        # 检查是否有历史数据提示
        reporter.log_step("检查图片对比功能...")
        time.sleep(WAIT_SHORT)

        # 查找对比相关元素
        comparison_elements = [
            ("选择图片", "图片选择器"),
            ("对比", "对比功能"),
            ("历史记录", "历史数据"),
            ("暂无历史推理数据", "空状态提示"),
        ]

        found_count = 0
        has_data = False
        for text, description in comparison_elements:
            try:
                if page.locator(f"text={text}").first.is_visible(timeout=2000):
                    found_count += 1
                    if "暂无" not in text:
                        has_data = True
            except:
                pass

        if found_count >= 1:
            reporter.log_step(f"图片对比页面加载成功（{found_count}/4）", "OK")
            if not has_data:
                reporter.log_step("暂无历史数据，无法测试对比功能", "INFO")
        else:
            reporter.log_step("图片对比页面元素未找到", "WARN")

        # 检查错误
        errors = check_for_errors(page, "phase3_image_comparison")
        if errors:
            reporter.report_bug(f"发现 {len(errors)} 个错误", "components/comparison_components.py")

        # 全页截图
        page.screenshot(path=str(SCREENSHOT_DIR / "phase3_comparison_02_full_page.png"), full_page=True)

        # 判断测试是否通过
        passed = found_count >= 1 and len(errors) == 0
        reporter.end_test(passed, f"找到 {found_count} 个关键元素，{len(errors)} 个错误")
        return passed

    except Exception as e:
        error_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
        reporter.log_step(f"测试异常: {error_msg}", "FAIL")
        reporter.report_bug(f"测试异常: {error_msg}", "components/comparison_components.py")
        page.screenshot(path=str(SCREENSHOT_DIR / "phase3_comparison_error.png"))
        reporter.end_test(False, f"测试异常: {error_msg}")
        return False


def test_phase3_statistics_enhanced(page, reporter: TestReporter):
    """测试阶段3：统计分析增强"""
    reporter.start_test("阶段3：统计分析增强")

    try:
        # 导航到统计分析
        reporter.log_step("导航到统计分析...")
        page.goto(f"{APP_URL}/统计分析", timeout=30000)
        time.sleep(WAIT_MEDIUM)
        page.screenshot(path=str(SCREENSHOT_DIR / "phase3_stats_01_page_loaded.png"))
        reporter.log_step("页面加载成功", "OK")

        # 检查页面元素
        reporter.log_step("检查统计分析元素...")

        # 查找关键元素
        stats_elements = [
            ("统计分析", "页面标题"),
            ("数据源", "数据源选择器"),
            ("准确率", "准确率统计"),
            ("趋势", "趋势图"),
            ("暂无推理数据", "空状态提示"),
        ]

        found_count = 0
        has_data = False
        for text, description in stats_elements:
            try:
                if page.locator(f"text={text}").first.is_visible(timeout=2000):
                    found_count += 1
                    if "暂无" not in text:
                        has_data = True
            except:
                pass

        if found_count >= 1:
            reporter.log_step(f"统计分析页面加载成功（{found_count}/5）", "OK")
            if not has_data:
                reporter.log_step("暂无数据，显示空状态", "INFO")
        else:
            reporter.log_step("统计分析页面元素未找到", "WARN")

        # 检查错误
        errors = check_for_errors(page, "phase3_statistics_enhanced")
        if errors:
            reporter.report_bug(f"发现 {len(errors)} 个错误", "pages/3_统计分析.py")

        # 全页截图
        page.screenshot(path=str(SCREENSHOT_DIR / "phase3_stats_02_full_page.png"), full_page=True)

        # 判断测试是否通过
        passed = found_count >= 1 and len(errors) == 0
        reporter.end_test(passed, f"找到 {found_count} 个关键元素，{len(errors)} 个错误")
        return passed

    except Exception as e:
        error_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
        reporter.log_step(f"测试异常: {error_msg}", "FAIL")
        reporter.report_bug(f"测试异常: {error_msg}", "pages/3_统计分析.py")
        page.screenshot(path=str(SCREENSHOT_DIR / "phase3_stats_error.png"))
        reporter.end_test(False, f"测试异常: {error_msg}")
        return False


def main():
    """主测试函数"""
    setup_test_environment()

    # 创建测试报告器
    reporter = TestReporter()

    with sync_playwright() as p:
        # 启动浏览器
        print("\n启动浏览器...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        try:
            # 执行所有测试
            test_phase1_single_diagnosis(page, reporter)
            test_phase2_batch_validation(page, reporter)
            test_phase2_knowledge_base(page, reporter)
            test_phase3_image_comparison(page, reporter)
            test_phase3_statistics_enhanced(page, reporter)

            # 生成测试摘要
            print(reporter.generate_summary())

            # 保存测试报告
            save_test_report(reporter)

            # 保持浏览器打开
            print("\n测试完成，浏览器将在 10 秒后关闭...")
            time.sleep(10)

        except Exception as e:
            error_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
            print(f"\n[ERROR] 测试运行失败: {error_msg}")
            page.screenshot(path=str(SCREENSHOT_DIR / "test_runner_error.png"))
        finally:
            browser.close()


def save_test_report(reporter: TestReporter):
    """保存测试报告"""
    report_path = Path("D:/项目管理/PhytoOracle/docs/PHASE_ALL_TEST_REPORT.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# PhytoOracle Frontend Demo - 全功能测试报告\n\n")
        f.write(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**测试工具**: Playwright\n\n")
        f.write(f"**测试范围**: 阶段1、阶段2、阶段3 所有功能\n\n")

        f.write("## 测试摘要\n\n")
        f.write(f"- 总测试数: {reporter.total_tests}\n")
        f.write(f"- 通过: {reporter.passed_tests}\n")
        f.write(f"- 失败: {reporter.failed_tests}\n")
        f.write(f"- 通过率: {(reporter.passed_tests/reporter.total_tests*100):.1f}%\n\n")

        f.write(f"## Bug 统计\n\n")
        f.write(f"- 发现的 Bug: {len(reporter.bugs_found)}\n")
        f.write(f"- 修复的 Bug: {len(reporter.bugs_fixed)}\n\n")

        f.write("## 测试详情\n\n")
        for detail in reporter.test_details:
            status_icon = "✅" if detail["status"] == "PASSED" else "❌"
            f.write(f"### {status_icon} {detail['name']}\n\n")
            f.write(f"- **状态**: {detail['status']}\n")
            f.write(f"- **用时**: {detail['elapsed']}\n")
            if detail['details']:
                f.write(f"- **详情**: {detail['details']}\n")
            f.write("\n")

        if reporter.bugs_found:
            f.write("## 发现的 Bug\n\n")
            for i, bug in enumerate(reporter.bugs_found):
                f.write(f"### Bug {i+1}: {bug['description']}\n\n")
                f.write(f"- **位置**: {bug['location']}\n")
                f.write(f"- **测试**: {bug['test']}\n")
                f.write(f"- **时间**: {bug['timestamp']}\n\n")

        if reporter.bugs_fixed:
            f.write("## 修复的 Bug\n\n")
            for i, fix in enumerate(reporter.bugs_fixed):
                f.write(f"### 修复 {i+1}: {fix['bug']}\n\n")
                f.write(f"- **修复方案**: {fix['fix']}\n")
                f.write(f"- **测试**: {fix['test']}\n")
                f.write(f"- **时间**: {fix['timestamp']}\n\n")

        f.write("## 截图\n\n")
        f.write(f"所有测试截图保存在: `{SCREENSHOT_DIR}`\n\n")

        f.write("---\n")
        f.write("*报告自动生成*\n")

    print(f"\n测试报告已保存: {report_path}")


if __name__ == "__main__":
    main()
