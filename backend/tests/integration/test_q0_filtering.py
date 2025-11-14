"""
Q0 逐级过滤集成测试

功能：
- 测试 DiagnosisService 的 Q0 逐级过滤序列
- 验证早期退出机制
- 验证候选疾病剪枝能力
- 使用真实的 VLM API 调用（非 mock）

测试数据：
- 需要准备以下测试图像：
  - rose_black_spot.jpg: 玫瑰黑斑病图片（正常流程）
  - animal.jpg: 动物图片（测试早期退出）
  - vegetable.jpg: 蔬菜图片（测试早期退出）

作者：AI Python Architect
日期：2025-11-13
"""

import pytest
import asyncio
from pathlib import Path

from backend.services.diagnosis_service import (
    DiagnosisService,
    UnsupportedImageException,
    DiagnosisException,
)
from backend.infrastructure.llm.vlm_exceptions import VLMException


class TestQ0Filtering:
    """
    Q0 逐级过滤集成测试类

    测试范围：
    1. 正常流程：花卉图片完整通过 Q0 序列
    2. 早期退出：非植物图片在 Q0.0 被拒绝
    3. 早期退出：非花卉植物在 Q0.1 被拒绝
    4. 种属识别：Q0.2 返回的 flower_genus 可用于候选疾病剪枝
    5. 置信度检查：验证 VLM 置信度是否合理
    """

    @pytest.fixture
    def service(self):
        """
        创建 DiagnosisService 实例

        Returns:
            DiagnosisService: 诊断服务实例
        """
        return DiagnosisService()

    @pytest.fixture
    def test_images_dir(self):
        """
        获取测试图像目录

        Returns:
            Path: 测试图像目录路径
        """
        return Path(__file__).resolve().parent.parent / "fixtures"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_q0_sequence_with_rose_image(self, service, test_images_dir):
        """
        测试 Q0 序列（玫瑰图片）

        验证项：
        1. Q0 序列完整执行通过
        2. 返回的 content_type 为 "plant"
        3. 返回的 plant_category 为 "flower"
        4. 返回的 flower_genus 在支持的种属列表中
        5. 返回的 organ 在 ["flower", "leaf", "both"] 中
        6. 返回的 completeness 在 ["complete", "partial", "close_up"] 中
        7. 返回的 has_abnormality 在 ["healthy", "abnormal"] 中
        8. 平均置信度 >= 0.6
        """
        # 加载测试图像
        image_path = test_images_dir / "rose_black_spot.jpg"

        # 跳过测试如果图像不存在
        if not image_path.exists():
            pytest.skip(f"测试图像不存在: {image_path}")

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # 执行 Q0 序列
        q0_responses = await service.execute_q0_sequence(image_bytes)

        # 验证返回字段
        assert "content_type" in q0_responses, "缺少 content_type 字段"
        assert "plant_category" in q0_responses, "缺少 plant_category 字段"
        assert "flower_genus" in q0_responses, "缺少 flower_genus 字段"
        assert "organ" in q0_responses, "缺少 organ 字段"
        assert "completeness" in q0_responses, "缺少 completeness 字段"
        assert "has_abnormality" in q0_responses, "缺少 has_abnormality 字段"
        assert "q0_confidence" in q0_responses, "缺少 q0_confidence 字段"

        # 验证内容类型
        assert q0_responses["content_type"] == "plant", \
            f"内容类型应为 plant，实际: {q0_responses['content_type']}"

        # 验证植物类别
        assert q0_responses["plant_category"] == "flower", \
            f"植物类别应为 flower，实际: {q0_responses['plant_category']}"

        # 验证花卉种属
        supported_genera = ["Rosa", "Prunus", "Tulipa", "Dianthus", "Paeonia", "unknown"]
        assert q0_responses["flower_genus"] in supported_genera, \
            f"花卉种属应在 {supported_genera} 中，实际: {q0_responses['flower_genus']}"

        # 验证器官类型
        assert q0_responses["organ"] in ["flower", "leaf", "both"], \
            f"器官类型应在 ['flower', 'leaf', 'both'] 中，实际: {q0_responses['organ']}"

        # 验证完整性
        assert q0_responses["completeness"] in ["complete", "partial", "close_up"], \
            f"完整性应在 ['complete', 'partial', 'close_up'] 中，实际: {q0_responses['completeness']}"

        # 验证异常状态
        assert q0_responses["has_abnormality"] in ["healthy", "abnormal"], \
            f"异常状态应在 ['healthy', 'abnormal'] 中，实际: {q0_responses['has_abnormality']}"

        # 验证置信度
        assert q0_responses["q0_confidence"] >= 0.6, \
            f"平均置信度应 >= 0.6，实际: {q0_responses['q0_confidence']:.2f}"

        # 打印诊断信息（用于调试）
        print(f"\n[诊断信息]")
        print(f"  内容类型: {q0_responses['content_type']}")
        print(f"  植物类别: {q0_responses['plant_category']}")
        print(f"  花卉种属: {q0_responses['flower_genus']}")
        print(f"  器官类型: {q0_responses['organ']}")
        print(f"  完整性: {q0_responses['completeness']}")
        print(f"  异常状态: {q0_responses['has_abnormality']}")
        print(f"  平均置信度: {q0_responses['q0_confidence']:.2f}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_early_exit_non_plant(self, service, test_images_dir):
        """
        测试早期退出机制（非植物图片）

        验证项：
        1. 非植物图片在 Q0.0 被拒绝
        2. 抛出 UnsupportedImageException 异常
        3. 异常消息包含正确的错误信息
        """
        # 加载测试图像（动物图片）
        image_path = test_images_dir / "animal.jpg"

        # 如果没有动物图片，跳过测试
        if not image_path.exists():
            pytest.skip(f"测试图像不存在: {image_path}")

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # 验证抛出异常
        with pytest.raises(UnsupportedImageException) as exc_info:
            await service.execute_q0_sequence(image_bytes)

        # 验证异常消息
        error_message = str(exc_info.value)
        assert "不支持的图片类型" in error_message or "不支持" in error_message, \
            f"异常消息应包含'不支持的图片类型'，实际: {error_message}"

        print(f"\n[早期退出测试] 非植物图片被正确拒绝: {error_message}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_early_exit_non_flower(self, service, test_images_dir):
        """
        测试早期退出机制（非花卉植物）

        验证项：
        1. 非花卉植物在 Q0.1 被拒绝
        2. 抛出 UnsupportedImageException 异常
        3. 异常消息包含正确的错误信息
        """
        # 加载测试图像（蔬菜图片）
        image_path = test_images_dir / "vegetable.jpg"

        # 如果没有蔬菜图片，跳过测试
        if not image_path.exists():
            pytest.skip(f"测试图像不存在: {image_path}")

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # 验证抛出异常
        with pytest.raises(UnsupportedImageException) as exc_info:
            await service.execute_q0_sequence(image_bytes)

        # 验证异常消息
        error_message = str(exc_info.value)
        assert "不支持的植物类别" in error_message or "仅支持观赏花卉" in error_message, \
            f"异常消息应包含'不支持的植物类别'或'仅支持观赏花卉'，实际: {error_message}"

        print(f"\n[早期退出测试] 非花卉植物被正确拒绝: {error_message}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_genus_pruning_capability(self, service, test_images_dir):
        """
        测试种属剪枝能力

        验证项：
        1. Q0.2 返回的 flower_genus 可用于候选疾病剪枝
        2. flower_genus 不为空
        3. flower_genus 是支持的种属之一
        """
        # 加载测试图像
        image_path = test_images_dir / "rose_black_spot.jpg"

        # 跳过测试如果图像不存在
        if not image_path.exists():
            pytest.skip(f"测试图像不存在: {image_path}")

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # 执行 Q0 序列
        q0_responses = await service.execute_q0_sequence(image_bytes)

        # 验证 flower_genus 可用于剪枝
        flower_genus = q0_responses["flower_genus"]

        assert flower_genus is not None, "flower_genus 不应为 None"
        assert isinstance(flower_genus, str), f"flower_genus 应为字符串，实际类型: {type(flower_genus)}"
        assert len(flower_genus) > 0, "flower_genus 不应为空字符串"

        # 验证是否在支持的种属列表中
        supported_genera = ["Rosa", "Prunus", "Tulipa", "Dianthus", "Paeonia", "unknown"]
        assert flower_genus in supported_genera, \
            f"flower_genus 应在 {supported_genera} 中，实际: {flower_genus}"

        print(f"\n[种属剪枝测试] flower_genus = {flower_genus}，可用于候选疾病剪枝")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_confidence_values(self, service, test_images_dir):
        """
        测试置信度值

        验证项：
        1. 平均置信度在合理范围内（0.0-1.0）
        2. 平均置信度 >= 0.6（VLM 应该对明确的图像有较高置信度）
        """
        # 加载测试图像
        image_path = test_images_dir / "rose_black_spot.jpg"

        # 跳过测试如果图像不存在
        if not image_path.exists():
            pytest.skip(f"测试图像不存在: {image_path}")

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # 执行 Q0 序列
        q0_responses = await service.execute_q0_sequence(image_bytes)

        # 验证置信度
        confidence = q0_responses["q0_confidence"]

        assert 0.0 <= confidence <= 1.0, \
            f"置信度应在 [0.0, 1.0] 范围内，实际: {confidence:.2f}"

        assert confidence >= 0.6, \
            f"平均置信度应 >= 0.6，实际: {confidence:.2f}"

        print(f"\n[置信度测试] 平均置信度 = {confidence:.2f}，符合预期")


async def main():
    """
    集成测试手动执行入口

    注意：正常情况下应使用 pytest 运行测试
    此 main 函数仅用于快速验证
    """
    print("=" * 80)
    print("Q0 逐级过滤集成测试手动执行")
    print("=" * 80)

    # 创建服务实例
    service = DiagnosisService()

    # 获取测试图像目录
    test_images_dir = Path(__file__).resolve().parent.parent / "fixtures"

    print(f"\n测试图像目录: {test_images_dir}")

    # 测试1: 正常流程
    print("\n[测试1] 正常流程测试（玫瑰图片）")
    image_path = test_images_dir / "rose_black_spot.jpg"

    if image_path.exists():
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        try:
            q0_responses = await service.execute_q0_sequence(image_bytes)
            print("  [OK] Q0 序列执行成功")
            print(f"  - 花卉种属: {q0_responses['flower_genus']}")
            print(f"  - 平均置信度: {q0_responses['q0_confidence']:.2f}")
        except Exception as e:
            print(f"  [ERROR] 测试失败: {e}")
    else:
        print(f"  [SKIP] 测试图像不存在: {image_path}")

    print("\n" + "=" * 80)
    print("手动测试执行完毕")
    print("提示: 建议使用 pytest 运行完整测试套件")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
