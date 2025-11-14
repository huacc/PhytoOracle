"""
模糊匹配引擎（P2.4核心模块）

功能：
- 加载和管理模糊匹配规则（从JSON配置文件）
- 提供多维度模糊匹配（颜色、尺寸、症状、位置、分布）
- 返回匹配解释（为什么匹配/不匹配）
- 支持规则热重载

类清单：
- FuzzyMatchingEngine: 模糊匹配引擎（主类）

设计原则：
- 单一职责：只负责模糊匹配逻辑，不涉及评分计算
- 开放封闭：通过配置文件扩展规则，无需修改代码
- 依赖倒置：通过配置文件依赖抽象规则，而非具体实现
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple, Set, List, Optional
from datetime import datetime


class FuzzyMatchingEngine:
    """
    模糊匹配引擎（P2.4核心类）

    负责管理和执行所有模糊匹配逻辑，支持多维度匹配和规则热重载。

    功能特性：
    1. 多维度匹配：颜色、尺寸、症状、位置、分布
    2. 规则配置化：所有规则存储在JSON文件中，便于维护
    3. 匹配解释：返回匹配原因，便于调试和优化
    4. 热重载：支持运行时重新加载规则，无需重启服务

    使用示例：
    ```python
    from pathlib import Path

    # 初始化模糊匹配引擎
    rules_dir = Path(__file__).resolve().parent / "fuzzy_rules"
    engine = FuzzyMatchingEngine(rules_dir)

    # 颜色模糊匹配
    is_match, score, reason = engine.match_color("deep_black", "black")
    print(f"匹配: {is_match}, 分数: {score}, 原因: {reason}")
    # 输出: 匹配: True, 分数: 0.9, 原因: 颜色别名匹配: deep_black → black

    # 尺寸模糊匹配
    is_match, score, reason = engine.match_size("medium", "medium_small")
    print(f"匹配: {is_match}, 分数: {score}, 原因: {reason}")
    # 输出: 匹配: True, 分数: 0.8, 原因: 尺寸容差匹配: medium ≈ medium_small (差距1级)

    # 位置模糊匹配（P2.4新增）
    is_match, score, reason = engine.match_location("lamina", "vein")
    print(f"匹配: {is_match}, 分数: {score}, 原因: {reason}")
    # 输出: 匹配: True, 分数: 0.7, 原因: 位置组匹配: leaf_surface

    # 热重载规则
    engine.reload_rules()
    print("规则已重新加载")
    ```
    """

    def __init__(self, rules_dir: Path):
        """
        初始化模糊匹配引擎

        Args:
            rules_dir: 模糊匹配规则目录（包含所有JSON配置文件）

        Raises:
            FileNotFoundError: 如果规则目录不存在
            json.JSONDecodeError: 如果规则文件格式错误
        """
        self.rules_dir = Path(rules_dir)
        if not self.rules_dir.exists():
            raise FileNotFoundError(f"规则目录不存在: {self.rules_dir}")

        # 加载所有规则
        self.color_rules = self._load_rules("color_rules.json")
        self.size_rules = self._load_rules("size_rules.json")
        self.symptom_rules = self._load_rules("symptom_rules.json")
        self.location_rules = self._load_rules("location_rules.json")
        self.distribution_rules = self._load_rules("distribution_rules.json")

        # 记录最后加载时间
        self.last_loaded = datetime.now()

    def _load_rules(self, filename: str) -> Dict[str, Any]:
        """
        加载单个规则文件

        Args:
            filename: 规则文件名（如 "color_rules.json"）

        Returns:
            Dict[str, Any]: 规则字典

        Raises:
            FileNotFoundError: 如果规则文件不存在
            json.JSONDecodeError: 如果规则文件格式错误
        """
        rule_path = self.rules_dir / filename
        if not rule_path.exists():
            # 如果规则文件不存在，返回空字典（允许部分规则缺失）
            return {}

        try:
            with open(rule_path, "r", encoding="utf-8") as f:
                rules = json.load(f)
                return rules
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"规则文件格式错误 ({filename}): {e.msg}",
                e.doc,
                e.pos
            )

    def reload_rules(self) -> None:
        """
        热重载所有规则

        重新从JSON文件加载所有模糊匹配规则，无需重启服务。
        适用场景：
        - 管理后台修改了模糊匹配规则
        - 规则调优后需要立即生效
        - 测试不同规则配置的效果

        Raises:
            FileNotFoundError: 如果规则文件不存在
            json.JSONDecodeError: 如果规则文件格式错误
        """
        self.color_rules = self._load_rules("color_rules.json")
        self.size_rules = self._load_rules("size_rules.json")
        self.symptom_rules = self._load_rules("symptom_rules.json")
        self.location_rules = self._load_rules("location_rules.json")
        self.distribution_rules = self._load_rules("distribution_rules.json")
        self.last_loaded = datetime.now()

    def match_color(self, color1: str, color2: str) -> Tuple[bool, float, str]:
        """
        颜色模糊匹配

        支持的匹配类型（按优先级）：
        1. 精确匹配：颜色值完全相同（分数1.0）
        2. 别名匹配：通过aliases映射（如deep_black→black，分数0.9）
        3. 相似颜色匹配：通过similar_colors映射（如black→dark_brown，分数0.7）
        4. 同色组匹配：属于同一color_group（如brown和dark_brown，分数0.6）

        Args:
            color1: 颜色1（如 "deep_black"）
            color2: 颜色2（如 "black"）

        Returns:
            Tuple[bool, float, str]: (是否匹配, 相似度分数0-1, 匹配原因)

        示例：
        ```python
        # 精确匹配
        is_match, score, reason = engine.match_color("black", "black")
        # 返回: (True, 1.0, "精确匹配")

        # 别名匹配
        is_match, score, reason = engine.match_color("deep_black", "black")
        # 返回: (True, 0.9, "颜色别名匹配: deep_black → black")

        # 相似颜色匹配
        is_match, score, reason = engine.match_color("black", "dark_brown")
        # 返回: (True, 0.7, "相似颜色匹配: black → dark_brown")

        # 不匹配
        is_match, score, reason = engine.match_color("black", "yellow")
        # 返回: (False, 0.0, "颜色不匹配")
        ```
        """
        # 1. 精确匹配
        if color1 == color2:
            return True, 1.0, "精确匹配"

        # 获取相似度分数配置
        scores = self.color_rules.get("similarity_scores", {
            "exact_match": 1.0,
            "alias_match": 0.9,
            "similar_color_match": 0.7,
            "same_group_match": 0.6
        })

        # 2. 颜色别名匹配
        aliases = self.color_rules.get("aliases", {})
        # 展开color1的所有别名
        color1_set = self._expand_color_aliases(color1, aliases)
        # 展开color2的所有别名
        color2_set = self._expand_color_aliases(color2, aliases)

        # 检查是否有交集
        if color1_set & color2_set:
            return True, scores.get("alias_match", 0.9), f"颜色别名匹配: {color1} <-> {color2}"

        # 3. 相似颜色匹配
        similar_colors = self.color_rules.get("similar_colors", {})
        if color2 in similar_colors.get(color1, []) or color1 in similar_colors.get(color2, []):
            return True, scores.get("similar_color_match", 0.7), f"相似颜色匹配: {color1} -> {color2}"

        # 4. 同色组匹配
        color_groups = self.color_rules.get("color_groups", {})
        for group_name, colors in color_groups.items():
            if color1 in colors and color2 in colors:
                return True, scores.get("same_group_match", 0.6), f"同色组匹配: {group_name}"

        # 5. 不匹配
        return False, 0.0, "颜色不匹配"

    def _expand_color_aliases(self, color: str, aliases: Dict[str, List[str]]) -> Set[str]:
        """
        展开颜色别名

        Args:
            color: 颜色值（如 "deep_black"）
            aliases: 颜色别名映射字典

        Returns:
            Set[str]: 颜色及其所有别名的集合（如 {"deep_black", "black", "dark_brown"}）

        示例：
        ```python
        aliases = {"deep_black": ["black", "dark_brown"]}
        result = self._expand_color_aliases("deep_black", aliases)
        # 返回: {"deep_black", "black", "dark_brown"}
        ```
        """
        color_set = {color}  # 包含自身

        # 检查color是否是某个别名组的key
        if color in aliases:
            color_set.update(aliases[color])

        # 检查color是否出现在某个别名组的values中
        for alias_group, colors in aliases.items():
            if color in colors or alias_group == color:
                color_set.add(alias_group)
                color_set.update(colors)

        return color_set

    def match_size(self, size1: str, size2: str) -> Tuple[bool, float, str]:
        """
        尺寸模糊匹配

        支持的匹配类型：
        1. 精确匹配：尺寸值完全相同（分数1.0）
        2. 容差匹配：相邻N个级别（N由tolerance配置，默认1级，分数0.8）

        Args:
            size1: 尺寸1（如 "medium"）
            size2: 尺寸2（如 "medium_small"）

        Returns:
            Tuple[bool, float, str]: (是否匹配, 相似度分数0-1, 匹配原因)

        示例：
        ```python
        # 精确匹配
        is_match, score, reason = engine.match_size("medium", "medium")
        # 返回: (True, 1.0, "精确匹配")

        # 容差1级匹配
        is_match, score, reason = engine.match_size("medium", "medium_small")
        # 返回: (True, 0.8, "尺寸容差匹配: medium ≈ medium_small (差距1级)")

        # 超出容差
        is_match, score, reason = engine.match_size("medium", "small")
        # 返回: (False, 0.0, "尺寸差距过大 (差距2级，超过容差1级)")
        ```
        """
        # 1. 精确匹配
        if size1 == size2:
            return True, 1.0, "精确匹配"

        # 获取尺寸顺序和容差配置
        size_order = self.size_rules.get("order", [])
        tolerance = self.size_rules.get("tolerance", 1)
        scores = self.size_rules.get("similarity_scores", {
            "exact_match": 1.0,
            "tolerance_1": 0.8,
            "tolerance_2": 0.6
        })

        if not size_order:
            return False, 0.0, "尺寸顺序未配置"

        # 2. 容差匹配
        try:
            idx1 = size_order.index(size1)
            idx2 = size_order.index(size2)
            diff = abs(idx1 - idx2)

            if diff <= tolerance:
                # 根据差距级别选择分数
                if diff == 1:
                    score = scores.get("tolerance_1", 0.8)
                elif diff == 2:
                    score = scores.get("tolerance_2", 0.6)
                else:
                    score = 0.8  # 默认分数

                return True, score, f"尺寸容差匹配: {size1} ~= {size2} (差距{diff}级)"
            else:
                return False, 0.0, f"尺寸差距过大 (差距{diff}级，超过容差{tolerance}级)"

        except ValueError as e:
            # 尺寸值不在size_order中
            return False, 0.0, f"尺寸值无效: {size1}或{size2}不在尺寸顺序中"

    def match_symptom_type(self, symptom1: str, symptom2: str) -> Tuple[bool, float, str]:
        """
        症状类型模糊匹配

        支持的匹配类型：
        1. 精确匹配：症状类型完全相同（分数1.0）
        2. 同义词匹配：属于同一synonym_group（如necrosis_spot和bacterial_spot，分数0.9）

        Args:
            symptom1: 症状类型1（如 "necrosis_spot"）
            symptom2: 症状类型2（如 "bacterial_spot"）

        Returns:
            Tuple[bool, float, str]: (是否匹配, 相似度分数0-1, 匹配原因)

        示例:
        ```python
        # 精确匹配
        is_match, score, reason = engine.match_symptom_type("necrosis_spot", "necrosis_spot")
        # 返回: (True, 1.0, "精确匹配")

        # 同义词匹配
        is_match, score, reason = engine.match_symptom_type("necrosis_spot", "bacterial_spot")
        # 返回: (True, 0.9, "症状同义词匹配: spot组")

        # 不匹配
        is_match, score, reason = engine.match_symptom_type("necrosis_spot", "powdery_coating")
        # 返回: (False, 0.0, "症状类型不匹配")
        ```
        """
        # 1. 精确匹配
        if symptom1 == symptom2:
            return True, 1.0, "精确匹配"

        # 获取同义词组配置
        synonym_groups = self.symptom_rules.get("synonym_groups", {})
        scores = self.symptom_rules.get("similarity_scores", {
            "exact_match": 1.0,
            "synonym_match": 0.9
        })

        # 2. 同义词匹配
        for group_name, group_data in synonym_groups.items():
            members = group_data.get("members", [])
            if symptom1 in members and symptom2 in members:
                return True, scores.get("synonym_match", 0.9), f"症状同义词匹配: {group_name}组"

        # 3. 不匹配
        return False, 0.0, "症状类型不匹配"

    def match_location(self, loc1: str, loc2: str) -> Tuple[bool, float, str]:
        """
        位置模糊匹配（P2.4新增）

        支持的匹配类型：
        1. 精确匹配：位置完全相同（分数1.0）
        2. 同组匹配：属于同一location_group（如lamina和vein都属于leaf_surface，分数0.7）
        3. 相邻匹配：通过adjacent_locations映射（如lamina和margin，分数0.6）

        Args:
            loc1: 位置1（如 "lamina"）
            loc2: 位置2（如 "vein"）

        Returns:
            Tuple[bool, float, str]: (是否匹配, 相似度分数0-1, 匹配原因)

        示例：
        ```python
        # 精确匹配
        is_match, score, reason = engine.match_location("lamina", "lamina")
        # 返回: (True, 1.0, "精确匹配")

        # 同组匹配
        is_match, score, reason = engine.match_location("lamina", "vein")
        # 返回: (True, 0.7, "位置组匹配: leaf_surface")

        # 相邻匹配
        is_match, score, reason = engine.match_location("lamina", "margin")
        # 返回: (True, 0.6, "相邻位置匹配")

        # 不匹配
        is_match, score, reason = engine.match_location("lamina", "petiole")
        # 返回: (False, 0.0, "位置不匹配")
        ```
        """
        # 1. 精确匹配
        if loc1 == loc2:
            return True, 1.0, "精确匹配"

        # 获取配置
        location_groups = self.location_rules.get("location_groups", {})
        adjacent_locations = self.location_rules.get("adjacent_locations", {})
        scores = self.location_rules.get("similarity_scores", {
            "exact_match": 1.0,
            "same_group_match": 0.7,
            "adjacent_match": 0.6
        })

        # 2. 同组匹配
        for group_name, group_data in location_groups.items():
            members = group_data.get("members", [])
            if loc1 in members and loc2 in members:
                return True, scores.get("same_group_match", 0.7), f"位置组匹配: {group_name}"

        # 3. 相邻匹配
        if loc2 in adjacent_locations.get(loc1, []) or loc1 in adjacent_locations.get(loc2, []):
            return True, scores.get("adjacent_match", 0.6), "相邻位置匹配"

        # 4. 不匹配
        return False, 0.0, "位置不匹配"

    def match_distribution(self, dist1: str, dist2: str) -> Tuple[bool, float, str]:
        """
        分布模式模糊匹配（P2.4新增）

        支持的匹配类型：
        1. 精确匹配：分布模式完全相同（分数1.0）
        2. 同组匹配：属于同一distribution_group（如scattered和random，分数0.8）
        3. 相似模式匹配：通过similar_patterns映射（如clustered和confluent，分数0.75）

        Args:
            dist1: 分布模式1（如 "scattered"）
            dist2: 分布模式2（如 "random"）

        Returns:
            Tuple[bool, float, str]: (是否匹配, 相似度分数0-1, 匹配原因)

        示例：
        ```python
        # 精确匹配
        is_match, score, reason = engine.match_distribution("scattered", "scattered")
        # 返回: (True, 1.0, "精确匹配")

        # 同组匹配
        is_match, score, reason = engine.match_distribution("scattered", "random")
        # 返回: (True, 0.8, "分布组匹配: dispersed")

        # 相似模式匹配
        is_match, score, reason = engine.match_distribution("clustered", "confluent")
        # 返回: (True, 0.75, "相似分布模式: clustered → confluent")

        # 不匹配
        is_match, score, reason = engine.match_distribution("scattered", "along_vein")
        # 返回: (False, 0.0, "分布模式不匹配")
        ```
        """
        # 1. 精确匹配
        if dist1 == dist2:
            return True, 1.0, "精确匹配"

        # 获取配置
        distribution_groups = self.distribution_rules.get("distribution_groups", {})
        similar_patterns = self.distribution_rules.get("similar_patterns", {})
        scores = self.distribution_rules.get("similarity_scores", {
            "exact_match": 1.0,
            "same_group_match": 0.8,
            "similar_pattern_match": 0.75
        })

        # 2. 同组匹配
        for group_name, group_data in distribution_groups.items():
            members = group_data.get("members", [])
            if dist1 in members and dist2 in members:
                return True, scores.get("same_group_match", 0.8), f"分布组匹配: {group_name}"

        # 3. 相似模式匹配
        if dist2 in similar_patterns.get(dist1, []) or dist1 in similar_patterns.get(dist2, []):
            return True, scores.get("similar_pattern_match", 0.75), f"相似分布模式: {dist1} -> {dist2}"

        # 4. 不匹配
        return False, 0.0, "分布模式不匹配"

    def get_rules_info(self) -> Dict[str, Any]:
        """
        获取规则信息（用于调试和监控）

        Returns:
            Dict[str, Any]: 规则信息字典，包含：
                - rules_dir: 规则目录路径
                - last_loaded: 最后加载时间
                - color_rules_version: 颜色规则版本
                - size_rules_version: 尺寸规则版本
                - symptom_rules_version: 症状规则版本
                - location_rules_version: 位置规则版本
                - distribution_rules_version: 分布规则版本

        示例：
        ```python
        info = engine.get_rules_info()
        print(f"规则目录: {info['rules_dir']}")
        print(f"最后加载: {info['last_loaded']}")
        print(f"颜色规则版本: {info['color_rules_version']}")
        ```
        """
        return {
            "rules_dir": str(self.rules_dir),
            "last_loaded": self.last_loaded.isoformat(),
            "color_rules_version": self.color_rules.get("version", "unknown"),
            "size_rules_version": self.size_rules.get("version", "unknown"),
            "symptom_rules_version": self.symptom_rules.get("version", "unknown"),
            "location_rules_version": self.location_rules.get("version", "unknown"),
            "distribution_rules_version": self.distribution_rules.get("version", "unknown")
        }


def main():
    """
    FuzzyMatchingEngine 使用示例

    演示如何：
    1. 初始化模糊匹配引擎
    2. 进行颜色模糊匹配
    3. 进行尺寸模糊匹配
    4. 进行症状类型模糊匹配
    5. 进行位置模糊匹配（P2.4新增）
    6. 进行分布模式模糊匹配（P2.4新增）
    7. 热重载规则
    8. 查看规则信息
    """
    print("=" * 80)
    print("FuzzyMatchingEngine 使用示例")
    print("=" * 80)

    # 1. 初始化模糊匹配引擎
    print("\n[示例1] 初始化模糊匹配引擎")
    rules_dir = Path(__file__).resolve().parent / "fuzzy_rules"
    try:
        engine = FuzzyMatchingEngine(rules_dir)
        print(f"  [OK] 模糊匹配引擎初始化成功")
        print(f"  规则目录: {engine.rules_dir}")
        print(f"  加载时间: {engine.last_loaded}")
    except Exception as e:
        print(f"  [FAIL] 初始化失败: {e}")
        return

    # 2. 颜色模糊匹配测试
    print("\n[示例2] 颜色模糊匹配")
    test_cases_color = [
        ("black", "black", "精确匹配"),
        ("deep_black", "black", "别名匹配"),
        ("black", "dark_brown", "相似颜色匹配"),
        ("brown", "dark_brown", "同色组匹配"),
        ("black", "yellow", "不匹配")
    ]

    for color1, color2, expected_type in test_cases_color:
        is_match, score, reason = engine.match_color(color1, color2)
        status = "[OK]" if is_match else "[FAIL]"
        print(f"  {status} {color1:15} vs {color2:15} | 匹配:{is_match:5} | 分数:{score:.2f} | {reason}")

    # 3. 尺寸模糊匹配测试
    print("\n[示例3] 尺寸模糊匹配")
    test_cases_size = [
        ("medium", "medium", "精确匹配"),
        ("medium", "medium_small", "容差1级"),
        ("medium", "small", "超出容差"),
        ("large", "medium_large", "容差1级")
    ]

    for size1, size2, expected_type in test_cases_size:
        is_match, score, reason = engine.match_size(size1, size2)
        status = "[OK]" if is_match else "[FAIL]"
        print(f"  {status} {size1:15} vs {size2:15} | 匹配:{is_match:5} | 分数:{score:.2f} | {reason}")

    # 4. 症状类型模糊匹配测试
    print("\n[示例4] 症状类型模糊匹配")
    test_cases_symptom = [
        ("necrosis_spot", "necrosis_spot", "精确匹配"),
        ("necrosis_spot", "bacterial_spot", "同义词匹配"),
        ("powdery_coating", "downy_coating", "同义词匹配"),
        ("necrosis_spot", "powdery_coating", "不匹配")
    ]

    for symptom1, symptom2, expected_type in test_cases_symptom:
        is_match, score, reason = engine.match_symptom_type(symptom1, symptom2)
        status = "[OK]" if is_match else "[FAIL]"
        print(f"  {status} {symptom1:20} vs {symptom2:20} | 匹配:{is_match:5} | 分数:{score:.2f} | {reason}")

    # 5. 位置模糊匹配测试（P2.4新增）
    print("\n[示例5] 位置模糊匹配（P2.4新增）")
    test_cases_location = [
        ("lamina", "lamina", "精确匹配"),
        ("lamina", "vein", "同组匹配"),
        ("lamina", "margin", "相邻匹配"),
        ("lamina", "petiole", "不匹配")
    ]

    for loc1, loc2, expected_type in test_cases_location:
        is_match, score, reason = engine.match_location(loc1, loc2)
        status = "[OK]" if is_match else "[FAIL]"
        print(f"  {status} {loc1:15} vs {loc2:15} | 匹配:{is_match:5} | 分数:{score:.2f} | {reason}")

    # 6. 分布模式模糊匹配测试（P2.4新增）
    print("\n[示例6] 分布模式模糊匹配（P2.4新增）")
    test_cases_distribution = [
        ("scattered", "scattered", "精确匹配"),
        ("scattered", "random", "同组匹配"),
        ("clustered", "confluent", "相似模式匹配"),
        ("scattered", "along_vein", "不匹配")
    ]

    for dist1, dist2, expected_type in test_cases_distribution:
        is_match, score, reason = engine.match_distribution(dist1, dist2)
        status = "[OK]" if is_match else "[FAIL]"
        print(f"  {status} {dist1:15} vs {dist2:15} | 匹配:{is_match:5} | 分数:{score:.2f} | {reason}")

    # 7. 规则信息查询
    print("\n[示例7] 规则信息查询")
    info = engine.get_rules_info()
    print(f"  规则目录: {info['rules_dir']}")
    print(f"  最后加载: {info['last_loaded']}")
    print(f"  颜色规则版本: {info['color_rules_version']}")
    print(f"  尺寸规则版本: {info['size_rules_version']}")
    print(f"  症状规则版本: {info['symptom_rules_version']}")
    print(f"  位置规则版本: {info['location_rules_version']}")
    print(f"  分布规则版本: {info['distribution_rules_version']}")

    # 8. 热重载规则测试
    print("\n[示例8] 热重载规则")
    try:
        engine.reload_rules()
        print(f"  [OK] 规则重新加载成功")
        print(f"  新的加载时间: {engine.last_loaded}")
    except Exception as e:
        print(f"  [FAIL] 热重载失败: {e}")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
