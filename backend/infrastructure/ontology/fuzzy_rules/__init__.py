"""
模糊匹配规则配置模块

本模块包含所有模糊匹配规则的JSON配置文件：
- color_rules.json: 颜色别名和相似度规则
- size_rules.json: 尺寸容差规则
- symptom_rules.json: 症状同义词规则
- location_rules.json: 位置近似规则
- distribution_rules.json: 分布模式相似性规则

所有规则文件均为JSON格式,可在运行时动态加载和热重载。
"""

__all__ = []
