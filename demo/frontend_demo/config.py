"""
PhytoOracle Frontend Demo - 配置文件

包含所有可配置参数，便于统一管理和后期调整。
"""
from typing import Dict, List
from pathlib import Path

# ===== 基础路径配置 =====
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"

# ===== 假数据文件路径 =====
DISEASES_DIR = DATA_DIR / "diseases"
ONTOLOGY_DIR = DATA_DIR / "ontology"
FEATURE_ONTOLOGY_FILE = ONTOLOGY_DIR / "feature_ontology.json"

# ===== 置信度阈值 =====
CONFIDENCE_THRESHOLDS: Dict[str, tuple] = {
    "confirmed": (0.85, 1.0),    # 确诊
    "suspected": (0.65, 0.85),   # 疑似
    "unlikely": (0.0, 0.65),     # 不太可能
}

# ===== 特征重要性权重 =====
FEATURE_IMPORTANCE_WEIGHTS: Dict[str, float] = {
    "major": 0.60,      # 主要特征总权重
    "minor": 0.30,      # 次要特征总权重
    "optional": 0.10,   # 可选特征总权重
}

# ===== 完整性修正系数 =====
COMPLETENESS_MODIFIERS: Dict[str, float] = {
    "whole_plant": 1.0,    # 全株
    "whole_part": 0.8,     # 完整器官
    "close_up": 0.6,       # 特写
}

# ===== 模糊匹配配置 =====
FUZZY_MATCH_THRESHOLD = 0.75  # 模糊匹配最低分数
EXACT_MATCH_SCORE = 1.0        # 精确匹配分数
FUZZY_MATCH_SCORE = 0.85       # 同义词匹配分数

# ===== UI配置 =====
PAGE_TITLE = "PhytoOracle 推理调试中心"
PAGE_ICON = "🌸"
LAYOUT = "wide"

# 支持的图片格式
SUPPORTED_IMAGE_FORMATS: List[str] = ["jpg", "jpeg", "png", "bmp"]

# ===== Q0序列问题配置 =====
Q0_QUESTIONS: Dict[str, Dict[str, any]] = {
    "q0_0_content_type": {
        "label": "Q0.0 内容类型",
        "choices": ["plant", "non_plant", "unclear"],
        "description": "图片中的主要内容是什么？"
    },
    "q0_1_plant_category": {
        "label": "Q0.1 植物类别",
        "choices": ["flower", "tree", "vegetable", "grass"],
        "description": "植物属于哪一类？"
    },
    "q0_2_flower_genus": {
        "label": "Q0.2 花卉种属",
        "choices": ["Rosa", "Paeonia", "Prunus", "Camellia", "Unknown"],
        "description": "花卉的属名是什么？"
    },
    "q0_3_organ_type": {
        "label": "Q0.3 器官类型",
        "choices": ["leaf", "flower", "stem", "root", "fruit"],
        "description": "图片主要展示的器官类型？"
    },
    "q0_4_completeness": {
        "label": "Q0.4 完整性",
        "choices": ["whole_plant", "whole_part", "close_up"],
        "description": "图片的完整性如何？"
    },
    "q0_5_abnormality": {
        "label": "Q0.5 异常判断",
        "choices": ["normal", "abnormal", "unclear"],
        "description": "植物是否有异常症状？"
    }
}

# ===== Q1-Q6特征配置 =====
FEATURE_EXTRACTION_KEYS: List[str] = [
    "symptom_type",
    "color_center",
    "color_border",
    "texture",
    "shape",
    "distribution",
    "size"
]

# ===== 疾病定义模板（用于生成假数据） =====
DISEASE_TEMPLATES: Dict[str, Dict[str, any]] = {
    "rose_black_spot": {
        "disease_id": "rose_black_spot",
        "disease_name": "玫瑰黑斑病",
        "disease_name_en": "Rose Black Spot",
        "version": "v4.2",
        "host_plants": ["Rosa"],
        "pathogen": "Diplocarpon rosae",
        "feature_vector": {
            "major": {
                "symptom_type": "necrosis_spot",
                "color_center": "black",
                "color_border": "yellow_halo"
            },
            "minor": {
                "texture": "smooth",
                "shape": "circular"
            },
            "optional": {
                "distribution": "scattered",
                "size": "small"
            }
        },
        "treatment_suggestions": [
            "移除感染叶片并销毁",
            "喷施杀菌剂（如代森锰锌）",
            "改善通风条件，降低湿度"
        ]
    },
    "rose_powdery_mildew": {
        "disease_id": "rose_powdery_mildew",
        "disease_name": "玫瑰白粉病",
        "disease_name_en": "Rose Powdery Mildew",
        "version": "v3.1",
        "host_plants": ["Rosa"],
        "pathogen": "Podosphaera pannosa",
        "feature_vector": {
            "major": {
                "symptom_type": "powdery_coating",
                "color_center": "white",
                "color_border": "none"
            },
            "minor": {
                "texture": "powdery",
                "shape": "irregular"
            },
            "optional": {
                "distribution": "uniform",
                "size": "small"
            }
        },
        "treatment_suggestions": [
            "喷施硫磺粉或三唑酮",
            "清理病叶，保持植株干燥",
            "避免过度施氮肥"
        ]
    },
    "cherry_brown_rot": {
        "disease_id": "cherry_brown_rot",
        "disease_name": "樱花褐腐病",
        "disease_name_en": "Cherry Brown Rot",
        "version": "v2.0",
        "host_plants": ["Prunus"],
        "pathogen": "Monilinia fructicola",
        "feature_vector": {
            "major": {
                "symptom_type": "necrosis_rot",
                "color_center": "brown",
                "color_border": "black"
            },
            "minor": {
                "texture": "wet",
                "shape": "irregular"
            },
            "optional": {
                "distribution": "clustered",
                "size": "large"
            }
        },
        "treatment_suggestions": [
            "剪除病枝并销毁",
            "喷施多菌灵或甲基托布津",
            "改善通风，减少湿度"
        ]
    }
}

# ===== 置信度生成规则 =====
CONFIDENCE_RANGES: Dict[str, tuple] = {
    "correct_q0": (0.90, 0.98),         # 正确诊断的Q0置信度
    "correct_q1_q6": (0.85, 0.95),      # 正确诊断的Q1-Q6置信度
    "correct_final": (0.85, 0.95),      # 正确诊断的最终置信度
    "incorrect_q1_q6": (0.70, 0.85),    # 误诊的特征置信度
    "incorrect_final": (0.65, 0.82),    # 误诊的最终置信度
}

# ===== 假数据随机种子（保证一致性） =====
RANDOM_SEED = 42

# ===== VLM提供商 =====
VLM_PROVIDER = "Qwen VL Plus (Mock)"

# ===== 本体版本信息 =====
ONTOLOGY_VERSION = "v1.2"
ONTOLOGY_GIT_COMMIT = "abc1234"  # 假数据
