"""
P2.1 阶段单元测试 - 提示词框架（PROOF Framework + Instructor）

测试范围：
1. PROOF Framework 核心类测试
2. VLM 响应 Schema 测试
3. Q0.0-Q0.5 提示词渲染测试
4. Q1-Q6 动态特征提取测试
5. Instructor 客户端初始化测试
6. LLM 配置管理测试

作者：AI Python Architect
日期：2025-11-12
"""

import pytest
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.infrastructure.llm.prompts import (
    # PROOF Framework 组件
    PROOFPrompt,
    PromptPurpose,
    PromptRole,
    PromptObservation,
    PromptOptions,
    Choice,
    PromptFormat,
    Example,
    # VLM 响应 Schema
    Q00Response,
    Q01Response,
    Q02Response,
    Q03Response,
    Q04Response,
    Q05Response,
    FeatureResponse,
    # Q0 系列提示词
    Q0_0_CONTENT_TYPE_PROMPT,
    Q0_1_PLANT_CATEGORY_PROMPT,
    Q0_2_GENUS_PROMPT,
    Q0_3_ORGAN_PROMPT,
    Q0_4_COMPLETENESS_PROMPT,
    Q0_5_ABNORMALITY_PROMPT,
    # 动态特征提取
    feature_prompt_builder,
)


# ==================== PROOF Framework 核心类测试 ====================

class TestPROOFFramework:
    """测试 PROOF Framework 核心类"""

    def test_prompt_purpose_creation(self):
        """测试 PromptPurpose 创建"""
        purpose = PromptPurpose(
            task="Test task",
            context="Test context",
            why_important="Test importance"
        )
        assert purpose.task == "Test task"
        assert purpose.context == "Test context"
        assert purpose.why_important == "Test importance"

    def test_prompt_role_creation(self):
        """测试 PromptRole 创建"""
        role = PromptRole(
            role="test role",
            expertise=["expertise1", "expertise2"],
            constraints=["constraint1"]
        )
        assert role.role == "test role"
        assert len(role.expertise) == 2
        assert len(role.constraints) == 1

    def test_prompt_options_creation(self):
        """测试 PromptOptions 创建"""
        options = PromptOptions(
            choices=[
                Choice("option1", "Description 1"),
                Choice("option2", "Description 2")
            ],
            allow_unknown=True,
            allow_uncertain=False
        )
        assert len(options.choices) == 2
        assert options.allow_unknown is True
        assert options.allow_uncertain is False

    def test_proof_prompt_render(self):
        """测试 PROOFPrompt 渲染"""
        prompt = PROOFPrompt(
            question_id="TEST",
            purpose=PromptPurpose(task="Test task"),
            role=PromptRole(role="test role", expertise=["test"]),
            observation=PromptObservation(),
            options=PromptOptions(choices=[Choice("a", "test")]),
            format_spec=PromptFormat(response_schema=Q00Response),
            version="v1.0"
        )

        rendered = prompt.render()

        # 验证关键内容存在
        assert "test role" in rendered
        assert "Test task" in rendered
        assert "RESPONSE FORMAT" in rendered
        assert len(rendered) > 100  # 渲染后应该有足够的内容

    def test_proof_prompt_to_dict(self):
        """测试 PROOFPrompt 导出为字典"""
        prompt = PROOFPrompt(
            question_id="TEST",
            purpose=PromptPurpose(task="Test task"),
            role=PromptRole(role="test role", expertise=["test"]),
            observation=PromptObservation(),
            options=PromptOptions(choices=[Choice("a", "test")]),
            format_spec=PromptFormat(response_schema=Q00Response),
            version="v1.0"
        )

        config_dict = prompt.to_dict()

        assert config_dict["question_id"] == "TEST"
        assert config_dict["version"] == "v1.0"
        assert "purpose" in config_dict
        assert "role" in config_dict


# ==================== VLM 响应 Schema 测试 ====================

class TestVLMResponseSchema:
    """测试 VLM 响应 Schema"""

    def test_q00_response_valid(self):
        """测试 Q00Response 有效输入"""
        response = Q00Response(
            choice="plant",
            confidence=0.95,
            reasoning="Test reasoning"
        )
        assert response.choice == "plant"
        assert response.confidence == 0.95
        assert response.reasoning == "Test reasoning"

    def test_q00_response_invalid_choice(self):
        """测试 Q00Response 无效 choice"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Q00Response(choice="invalid", confidence=0.95)

    def test_q00_response_invalid_confidence(self):
        """测试 Q00Response 无效 confidence（超出范围）"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Q00Response(choice="plant", confidence=1.5)  # 超出 [0, 1] 范围

    def test_q02_response_valid(self):
        """测试 Q02Response 有效输入"""
        response = Q02Response(
            choice="Rosa",
            confidence=0.88,
            reasoning="Compound leaves"
        )
        assert response.choice == "Rosa"
        assert response.confidence == 0.88

    def test_q02_response_unknown(self):
        """测试 Q02Response unknown 选项"""
        response = Q02Response(choice="unknown", confidence=0.50)
        assert response.choice == "unknown"

    def test_feature_response_with_alternatives(self):
        """测试 FeatureResponse 带 alternatives"""
        response = FeatureResponse(
            choice="necrosis_spot",
            confidence=0.85,
            alternatives=["chlorosis_spot", "other"]
        )
        assert response.choice == "necrosis_spot"
        assert len(response.alternatives) == 2


# ==================== Q0 系列提示词测试 ====================

class TestQ0Prompts:
    """测试 Q0.0-Q0.5 提示词"""

    def test_q0_0_prompt_exists(self):
        """测试 Q0.0 提示词存在且非空"""
        assert Q0_0_CONTENT_TYPE_PROMPT is not None
        assert len(Q0_0_CONTENT_TYPE_PROMPT) > 100
        assert "plant" in Q0_0_CONTENT_TYPE_PROMPT
        assert "animal" in Q0_0_CONTENT_TYPE_PROMPT

    def test_q0_1_prompt_exists(self):
        """测试 Q0.1 提示词存在且包含关键词"""
        assert Q0_1_PLANT_CATEGORY_PROMPT is not None
        assert "flower" in Q0_1_PLANT_CATEGORY_PROMPT
        assert "vegetable" in Q0_1_PLANT_CATEGORY_PROMPT

    def test_q0_2_prompt_contains_5_genera(self):
        """测试 Q0.2 提示词包含5种花卉"""
        required_genera = ["Rosa", "Prunus", "Tulipa", "Dianthus", "Paeonia"]
        for genus in required_genera:
            assert genus in Q0_2_GENUS_PROMPT, f"Missing genus: {genus}"

    def test_q0_2_prompt_contains_visual_clues(self):
        """测试 Q0.2 提示词包含视觉线索"""
        assert "VISUAL CLUES" in Q0_2_GENUS_PROMPT
        assert "Compound Feature Description" in Q0_2_GENUS_PROMPT

    def test_q0_3_prompt_exists(self):
        """测试 Q0.3 提示词存在且包含器官选项"""
        assert Q0_3_ORGAN_PROMPT is not None
        assert "flower" in Q0_3_ORGAN_PROMPT
        assert "leaf" in Q0_3_ORGAN_PROMPT
        assert "both" in Q0_3_ORGAN_PROMPT

    def test_q0_4_prompt_exists(self):
        """测试 Q0.4 提示词存在且包含完整性选项"""
        assert Q0_4_COMPLETENESS_PROMPT is not None
        assert "complete" in Q0_4_COMPLETENESS_PROMPT
        assert "partial" in Q0_4_COMPLETENESS_PROMPT
        assert "close_up" in Q0_4_COMPLETENESS_PROMPT

    def test_q0_5_prompt_exists(self):
        """测试 Q0.5 提示词存在且包含健康判断"""
        assert Q0_5_ABNORMALITY_PROMPT is not None
        assert "healthy" in Q0_5_ABNORMALITY_PROMPT
        assert "abnormal" in Q0_5_ABNORMALITY_PROMPT


# ==================== Q1-Q6 动态特征提取测试 ====================

class TestFeaturePromptBuilder:
    """测试 Q1-Q6 动态特征提取"""

    def test_build_symptom_type_prompt(self):
        """测试构建 symptom_type（Q1）提示词"""
        prompt = feature_prompt_builder.build_prompt("symptom_type")
        rendered = prompt.render()

        assert "Q1" in prompt.question_id
        assert "symptom type" in rendered.lower()
        assert "necrosis_spot" in rendered
        assert "powdery_coating" in rendered

    def test_build_color_center_prompt(self):
        """测试构建 color_center（Q2）提示词"""
        prompt = feature_prompt_builder.build_prompt("color_center")
        rendered = prompt.render()

        assert "Q2" in prompt.question_id
        assert "black" in rendered
        assert "brown" in rendered
        assert "yellow" in rendered

    def test_build_size_prompt(self):
        """测试构建 size（Q4）提示词"""
        prompt = feature_prompt_builder.build_prompt("size")
        rendered = prompt.render()

        assert "Q4" in prompt.question_id
        assert "small" in rendered
        assert "medium" in rendered
        assert "large" in rendered

    def test_build_location_prompt(self):
        """测试构建 location（Q5）提示词"""
        prompt = feature_prompt_builder.build_prompt("location")
        rendered = prompt.render()

        assert "Q5" in prompt.question_id
        assert "lamina" in rendered
        assert "vein" in rendered

    def test_build_distribution_prompt(self):
        """测试构建 distribution（Q6）提示词"""
        prompt = feature_prompt_builder.build_prompt("distribution")
        rendered = prompt.render()

        assert "Q6" in prompt.question_id
        assert "scattered" in rendered
        assert "clustered" in rendered

    def test_build_invalid_dimension_raises_error(self):
        """测试构建无效维度抛出异常"""
        with pytest.raises(ValueError):
            feature_prompt_builder.build_prompt("invalid_dimension")

    def test_build_all_prompts(self):
        """测试批量构建所有提示词"""
        all_prompts = feature_prompt_builder.build_all_prompts()

        assert len(all_prompts) == 6
        assert "symptom_type" in all_prompts
        assert "color_center" in all_prompts
        assert "distribution" in all_prompts

        # 验证每个提示词都有内容
        for dim, prompt_text in all_prompts.items():
            assert len(prompt_text) > 100, f"{dim} prompt is too short"


# ==================== Instructor 客户端测试（仅测试初始化）====================

class TestInstructorClient:
    """测试 Instructor 客户端（不实际调用 API）"""

    def test_instructor_import(self):
        """测试 Instructor 库导入"""
        try:
            from backend.infrastructure.llm.instructor_client import INSTRUCTOR_AVAILABLE
            # 即使未安装也不应报错
            assert INSTRUCTOR_AVAILABLE in [True, False]
        except ImportError:
            pytest.skip("instructor_client module not available")


# ==================== LLM 配置管理测试 ====================

class TestLLMConfig:
    """测试 LLM 配置管理"""

    def test_get_default_config(self):
        """测试获取默认配置"""
        from backend.infrastructure.llm.llm_config import get_default_config

        config = get_default_config()

        assert config.default_provider == "qwen"
        assert "qwen" in config.providers
        assert "chatgpt" in config.providers
        assert config.cache.enabled is True

    def test_provider_config_access(self):
        """测试访问 Provider 配置"""
        from backend.infrastructure.llm.llm_config import get_default_config

        config = get_default_config()
        qwen_config = config.get_provider_config("qwen")

        assert qwen_config.model == "qwen-vl-plus"
        assert "dashscope" in qwen_config.base_url
        assert qwen_config.timeout > 0
        assert qwen_config.max_retries > 0

    def test_get_api_key_from_env(self):
        """测试从环境变量获取 API Key"""
        import os
        from backend.infrastructure.llm.llm_config import get_default_config

        # 设置测试环境变量
        os.environ["VLM_QWEN_API_KEY"] = "test-api-key"

        config = get_default_config()
        api_key = config.get_api_key("qwen")

        assert api_key == "test-api-key"

        # 清理环境变量
        del os.environ["VLM_QWEN_API_KEY"]


# ==================== 运行所有测试 ====================

if __name__ == "__main__":
    """
    运行单元测试

    使用 pytest 运行所有测试

    执行方式：
    1. 安装 pytest: pip install pytest
    2. 运行测试: pytest backend/tests/unit/test_p2_1_prompts.py -v
    3. 或直接运行本文件: python backend/tests/unit/test_p2_1_prompts.py
    """
    print("=" * 80)
    print("P2.1 阶段单元测试")
    print("=" * 80)

    # 使用 pytest 运行测试
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd=project_root
    )

    sys.exit(result.returncode)
