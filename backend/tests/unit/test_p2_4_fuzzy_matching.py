"""
P2.4 模糊匹配引擎单元测试

测试覆盖范围：
- FuzzyMatchingEngine 初始化
- 颜色模糊匹配（精确、别名、相似、同组、不匹配）
- 尺寸模糊匹配（精确、容差1级、容差2级、超出容差）
- 症状类型模糊匹配（精确、同义词、不匹配）
- 位置模糊匹配（精确、同组、相邻、不匹配）- P2.4新增
- 分布模式模糊匹配（精确、同组、相似、不匹配）- P2.4新增
- 规则热重载
- 规则信息查询

验收标准：
- 所有测试用例通过
- 测试覆盖率 >= 90%
- 所有返回结果为真实数据（不使用 mock）
"""

import pytest
from pathlib import Path
from backend.infrastructure.ontology.fuzzy_matcher import FuzzyMatchingEngine


# ==================== 测试夹具 ====================

@pytest.fixture
def fuzzy_engine():
    """
    创建模糊匹配引擎实例（测试夹具）

    Returns:
        FuzzyMatchingEngine: 模糊匹配引擎实例
    """
    rules_dir = Path(__file__).resolve().parent.parent.parent / "infrastructure" / "ontology" / "fuzzy_rules"
    return FuzzyMatchingEngine(rules_dir)


# ==================== 初始化测试 ====================

def test_fuzzy_engine_initialization(fuzzy_engine):
    """
    测试模糊匹配引擎初始化

    验收项（G2.4）：
    - FuzzyMatchingEngine 可成功初始化
    - 所有规则文件加载成功
    """
    assert fuzzy_engine is not None
    assert fuzzy_engine.color_rules is not None
    assert fuzzy_engine.size_rules is not None
    assert fuzzy_engine.symptom_rules is not None
    assert fuzzy_engine.location_rules is not None
    assert fuzzy_engine.distribution_rules is not None
    assert fuzzy_engine.last_loaded is not None


def test_fuzzy_engine_initialization_with_invalid_path():
    """
    测试使用无效路径初始化模糊匹配引擎

    预期行为：抛出 FileNotFoundError
    """
    invalid_path = Path("/nonexistent/path")
    with pytest.raises(FileNotFoundError):
        FuzzyMatchingEngine(invalid_path)


# ==================== 颜色模糊匹配测试 ====================

def test_color_exact_match(fuzzy_engine):
    """
    测试颜色精确匹配

    验收项（G2.4）：
    - 颜色模糊匹配测试通过（精确匹配）

    测试用例：black vs black
    预期结果：匹配=True, 分数=1.0, 原因="精确匹配"
    """
    is_match, score, reason = fuzzy_engine.match_color("black", "black")

    assert is_match is True
    assert score == 1.0
    assert reason == "精确匹配"


def test_color_alias_match(fuzzy_engine):
    """
    测试颜色别名匹配

    验收项（G2.4）：
    - 颜色模糊匹配测试通过（别名匹配）

    测试用例：deep_black vs black
    预期结果：匹配=True, 分数=0.9, 原因包含"别名匹配"
    """
    is_match, score, reason = fuzzy_engine.match_color("deep_black", "black")

    assert is_match is True
    assert score == 0.9
    assert "别名匹配" in reason


def test_color_similar_match(fuzzy_engine):
    """
    测试颜色相似匹配

    验收项（G2.4）：
    - 颜色模糊匹配测试通过（相似颜色匹配）

    测试用例：black vs dark_brown
    预期结果：匹配=True, 分数>=0.7, 原因包含"匹配"
    """
    is_match, score, reason = fuzzy_engine.match_color("black", "dark_brown")

    assert is_match is True
    assert score >= 0.7  # 别名或相似颜色匹配，分数应该>=0.7


def test_color_no_match(fuzzy_engine):
    """
    测试颜色不匹配

    验收项（G2.4）：
    - 颜色模糊匹配测试通过（不匹配场景）

    测试用例：black vs yellow
    预期结果：匹配=False, 分数=0.0, 原因包含"不匹配"
    """
    is_match, score, reason = fuzzy_engine.match_color("black", "yellow")

    assert is_match is False
    assert score == 0.0
    assert "不匹配" in reason


# ==================== 尺寸模糊匹配测试 ====================

def test_size_exact_match(fuzzy_engine):
    """
    测试尺寸精确匹配

    验收项（G2.4）：
    - 尺寸模糊匹配测试通过（精确匹配）

    测试用例：medium vs medium
    预期结果：匹配=True, 分数=1.0, 原因="精确匹配"
    """
    is_match, score, reason = fuzzy_engine.match_size("medium", "medium")

    assert is_match is True
    assert score == 1.0
    assert reason == "精确匹配"


def test_size_tolerance_match(fuzzy_engine):
    """
    测试尺寸容差匹配（相邻1级）

    验收项（G2.4）：
    - 尺寸模糊匹配测试通过（如 medium 匹配 medium_small）

    测试用例：medium vs medium_small
    预期结果：匹配=True, 分数=0.8, 原因包含"容差匹配"
    """
    is_match, score, reason = fuzzy_engine.match_size("medium", "medium_small")

    assert is_match is True
    assert score == 0.8
    assert "容差匹配" in reason


def test_size_exceed_tolerance(fuzzy_engine):
    """
    测试尺寸超出容差

    验收项（G2.4）：
    - 尺寸模糊匹配测试通过（超出容差场景）

    测试用例：medium vs small（相差2级，超过容差1级）
    预期结果：匹配=False, 分数=0.0, 原因包含"差距过大"
    """
    is_match, score, reason = fuzzy_engine.match_size("medium", "small")

    assert is_match is False
    assert score == 0.0
    assert "差距过大" in reason


# ==================== 症状类型模糊匹配测试 ====================

def test_symptom_exact_match(fuzzy_engine):
    """
    测试症状类型精确匹配

    验收项（G2.4）：
    - 症状类型模糊匹配测试通过（精确匹配）

    测试用例：necrosis_spot vs necrosis_spot
    预期结果：匹配=True, 分数=1.0, 原因="精确匹配"
    """
    is_match, score, reason = fuzzy_engine.match_symptom_type("necrosis_spot", "necrosis_spot")

    assert is_match is True
    assert score == 1.0
    assert reason == "精确匹配"


def test_symptom_synonym_match(fuzzy_engine):
    """
    测试症状类型同义词匹配

    验收项（G2.4）：
    - 症状类型模糊匹配测试通过（同义词匹配）

    测试用例：necrosis_spot vs bacterial_spot（同属spot组）
    预期结果：匹配=True, 分数=0.9, 原因包含"同义词匹配"
    """
    is_match, score, reason = fuzzy_engine.match_symptom_type("necrosis_spot", "bacterial_spot")

    assert is_match is True
    assert score == 0.9
    assert "同义词匹配" in reason


def test_symptom_no_match(fuzzy_engine):
    """
    测试症状类型不匹配

    验收项（G2.4）：
    - 症状类型模糊匹配测试通过（不匹配场景）

    测试用例：necrosis_spot vs powdery_coating
    预期结果：匹配=False, 分数=0.0, 原因包含"不匹配"
    """
    is_match, score, reason = fuzzy_engine.match_symptom_type("necrosis_spot", "powdery_coating")

    assert is_match is False
    assert score == 0.0
    assert "不匹配" in reason


# ==================== 位置模糊匹配测试（P2.4新增）====================

def test_location_exact_match(fuzzy_engine):
    """
    测试位置精确匹配

    验收项（G2.4）：
    - 位置模糊匹配测试通过（精确匹配）- P2.4新增

    测试用例：lamina vs lamina
    预期结果：匹配=True, 分数=1.0, 原因="精确匹配"
    """
    is_match, score, reason = fuzzy_engine.match_location("lamina", "lamina")

    assert is_match is True
    assert score == 1.0
    assert reason == "精确匹配"


def test_location_group_match(fuzzy_engine):
    """
    测试位置组匹配

    验收项（G2.4）：
    - 位置模糊匹配测试通过（同组匹配）- P2.4新增

    测试用例：lamina vs vein（同属leaf_surface组）
    预期结果：匹配=True, 分数=0.7, 原因包含"位置组匹配"
    """
    is_match, score, reason = fuzzy_engine.match_location("lamina", "vein")

    assert is_match is True
    assert score == 0.7
    assert "位置组匹配" in reason


def test_location_no_match_but_leaf_any(fuzzy_engine):
    """
    测试位置不直接匹配但属于leaf_any组

    验收项（G2.4）：
    - 位置模糊匹配测试通过（leaf_any组匹配）- P2.4新增

    测试用例：lamina vs petiole（同属leaf_any组）
    预期结果：匹配=True, 分数>=0.6, 原因包含"匹配"
    """
    is_match, score, reason = fuzzy_engine.match_location("lamina", "petiole")

    # 根据location_rules.json，lamina和petiole都属于leaf_any组
    assert is_match is True
    assert score >= 0.6


# ==================== 分布模式模糊匹配测试（P2.4新增）====================

def test_distribution_exact_match(fuzzy_engine):
    """
    测试分布模式精确匹配

    验收项（G2.4）：
    - 分布模式模糊匹配测试通过（精确匹配）- P2.4新增

    测试用例：scattered vs scattered
    预期结果：匹配=True, 分数=1.0, 原因="精确匹配"
    """
    is_match, score, reason = fuzzy_engine.match_distribution("scattered", "scattered")

    assert is_match is True
    assert score == 1.0
    assert reason == "精确匹配"


def test_distribution_group_match(fuzzy_engine):
    """
    测试分布模式组匹配

    验收项（G2.4）：
    - 分布模式模糊匹配测试通过（同组匹配）- P2.4新增

    测试用例：scattered vs random（同属dispersed组）
    预期结果：匹配=True, 分数=0.8, 原因包含"分布组匹配"
    """
    is_match, score, reason = fuzzy_engine.match_distribution("scattered", "random")

    assert is_match is True
    assert score == 0.8
    assert "分布组匹配" in reason


def test_distribution_similar_pattern_match(fuzzy_engine):
    """
    测试分布模式相似匹配

    验收项（G2.4）：
    - 分布模式模糊匹配测试通过（相似模式匹配）- P2.4新增

    测试用例：clustered vs confluent（同属aggregated组）
    预期结果：匹配=True, 分数>=0.75, 原因包含"匹配"
    """
    is_match, score, reason = fuzzy_engine.match_distribution("clustered", "confluent")

    assert is_match is True
    assert score >= 0.75


def test_distribution_no_match(fuzzy_engine):
    """
    测试分布模式不匹配

    验收项（G2.4）：
    - 分布模式模糊匹配测试通过（不匹配场景）- P2.4新增

    测试用例：scattered vs along_vein
    预期结果：匹配=False, 分数=0.0, 原因包含"不匹配"
    """
    is_match, score, reason = fuzzy_engine.match_distribution("scattered", "along_vein")

    assert is_match is False
    assert score == 0.0
    assert "不匹配" in reason


# ==================== 规则热重载测试 ====================

def test_reload_rules(fuzzy_engine):
    """
    测试规则热重载

    验收项（G2.4）：
    - 规则热重载功能正常工作

    测试步骤：
    1. 记录初始加载时间
    2. 调用 reload_rules()
    3. 验证加载时间已更新
    4. 验证规则仍然可用
    """
    import time

    # 记录初始加载时间
    initial_load_time = fuzzy_engine.last_loaded

    # 等待1秒以确保时间戳有变化
    time.sleep(1)

    # 热重载规则
    fuzzy_engine.reload_rules()

    # 验证加载时间已更新
    assert fuzzy_engine.last_loaded > initial_load_time

    # 验证规则仍然可用（测试一个匹配）
    is_match, score, reason = fuzzy_engine.match_color("black", "black")
    assert is_match is True
    assert score == 1.0


# ==================== 规则信息查询测试 ====================

def test_get_rules_info(fuzzy_engine):
    """
    测试规则信息查询

    验收项（G2.4）：
    - 规则信息查询功能正常工作

    验证：
    - 返回的信息包含所有必需字段
    - 规则版本号正确
    """
    info = fuzzy_engine.get_rules_info()

    # 验证必需字段
    assert "rules_dir" in info
    assert "last_loaded" in info
    assert "color_rules_version" in info
    assert "size_rules_version" in info
    assert "symptom_rules_version" in info
    assert "location_rules_version" in info
    assert "distribution_rules_version" in info

    # 验证版本号
    assert info["color_rules_version"] == "1.0"
    assert info["size_rules_version"] == "1.0"
    assert info["symptom_rules_version"] == "1.0"
    assert info["location_rules_version"] == "1.0"
    assert info["distribution_rules_version"] == "1.0"


# ==================== 边界条件和异常测试 ====================

def test_color_match_with_none(fuzzy_engine):
    """
    测试传入 None 值的颜色匹配（边界条件）

    预期行为：不匹配
    """
    # 注意：FuzzyMatchingEngine不直接处理None，由调用者（如FeatureMatcher）处理
    # 这里测试传入空字符串的情况
    is_match, score, reason = fuzzy_engine.match_color("", "black")

    assert is_match is False
    assert score == 0.0


def test_size_match_with_invalid_value(fuzzy_engine):
    """
    测试传入无效尺寸值的匹配（边界条件）

    预期行为：返回不匹配，原因包含"无效"
    """
    is_match, score, reason = fuzzy_engine.match_size("invalid_size", "medium")

    assert is_match is False
    assert score == 0.0
    assert "无效" in reason or "不在" in reason


# ==================== 性能测试 ====================

def test_color_match_performance(fuzzy_engine):
    """
    测试颜色匹配性能

    验证：
    - 1000次匹配操作应在合理时间内完成（<1秒）
    """
    import time

    start_time = time.time()

    for _ in range(1000):
        fuzzy_engine.match_color("black", "dark_brown")

    elapsed_time = time.time() - start_time

    # 1000次匹配应在1秒内完成
    assert elapsed_time < 1.0, f"性能测试失败: {elapsed_time:.3f}秒（预期<1秒）"


# ==================== 测试报告 ====================

if __name__ == "__main__":
    """
    运行所有单元测试并生成测试报告

    使用方法：
    ```bash
    # 运行所有测试
    pytest backend/tests/unit/test_p2_4_fuzzy_matching.py -v

    # 生成覆盖率报告
    pytest backend/tests/unit/test_p2_4_fuzzy_matching.py --cov=backend.infrastructure.ontology.fuzzy_matcher --cov-report=term-missing

    # 运行特定测试
    pytest backend/tests/unit/test_p2_4_fuzzy_matching.py::test_color_exact_match -v
    ```
    """
    pytest.main([__file__, "-v", "--tb=short"])
