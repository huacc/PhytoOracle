# PhytoOracle Frontend Demo

> **阶段1：核心推理展示（P0功能）**
>
> 使用假数据快速搭建可演示的 Streamlit 管理后台

## 快速开始

### 1. 安装依赖

```bash
cd demo/frontend_demo
pip install -r requirements.txt
```

### 2. 启动应用

```bash
streamlit run app.py
```

应用将在 `http://localhost:8501` 启动

### 3. 使用说明

#### 功能列表

- **图片上传与推理**：支持拖拽上传，显示完整推理链路
- **推理过程可视化**：
  - Q0序列（6步）：content_type → plant_category → flower_genus → organ_type → completeness → abnormality
  - Q1-Q6特征提取（7个特征）
  - 候选疾病筛选
  - 模糊匹配 + 加权评分
  - 最终诊断结果
- **本体追溯展示**：每个推理步骤显示使用的本体定义和知识文件路径
- **人工标注功能**：准确性标注 + 实际疾病标注 + 备注
- **本体使用导出**：导出推理数据和本体使用JSON

#### 测试图片说明

提供的测试图片文件名包含疾病信息：
- `rose_black_spot_001.jpg` - 玫瑰黑斑病
- `rose_powdery_mildew_001.jpg` - 玫瑰白粉病
- `cherry_brown_rot_001.jpg` - 樱花褐腐病

假数据推理引擎会根据文件名解析疾病类型，生成对应的推理结果。

## 目录结构

```
frontend_demo/
├── app.py                          # 主入口
├── config.py                       # 配置文件
├── requirements.txt                # 依赖清单
├── README.md                       # 使用说明
│
├── pages/                          # Streamlit多页面
│   └── 1_推理调试中心.py            # 推理调试主页面
│
├── components/                     # 可复用组件
│   ├── diagnosis_visualizer.py    # 推理可视化组件
│   ├── ontology_tracer.py         # 本体追溯组件
│   └── annotation_panel.py        # 标注面板组件
│
├── services/                       # 业务逻辑层
│   ├── mock_diagnosis_engine.py   # 假数据推理引擎
│   └── mock_knowledge_service.py  # 假数据知识库服务
│
├── models/                         # 数据模型
│   ├── diagnosis_result.py        # 推理结果数据模型
│   └── ontology_usage.py          # 本体使用数据模型
│
├── data/                           # 假数据存储
│   ├── diseases/                  # 疾病定义JSON
│   │   ├── rose_black_spot_v4.2.json
│   │   ├── rose_powdery_mildew_v3.1.json
│   │   └── cherry_brown_rot_v2.0.json
│   └── ontology/
│       └── feature_ontology.json  # 特征本体
│
├── assets/                         # 静态资源
│   └── images/                    # 测试图片
│       ├── rose_black_spot_001.jpg
│       ├── rose_powdery_mildew_001.jpg
│       └── cherry_brown_rot_001.jpg
│
└── utils/                          # 工具函数
    ├── data_generator.py          # 假数据生成工具
    └── export_helper.py           # 导出工具
```

## 开发说明

### 代码质量标准

- **类型注解**：所有函数使用类型提示
- **文档字符串**：每个模块、类、函数都有docstring
- **错误处理**：合理的异常处理，用户友好的错误提示
- **可配置性**：魔法数字提取到config.py
- **可测试性**：业务逻辑与UI分离

### 数据模型

使用Pydantic定义所有数据结构，确保类型安全和数据验证。

### Session State管理

所有状态集中管理，避免全局变量污染。

### 与MVP后端兼容

- 目录结构与后端 `backend/` 结构呼应
- 命名规范与后端服务一致
- 数据格式与需求文档API响应格式100%一致

## 检查标准

- [x] 启动无错误
- [x] 上传图片并看到完整推理过程
- [x] 推理链路展示完整（Q0 → Q1-Q6 → 匹配 → 评分 → 诊断）
- [x] 每个步骤都显示本体引用信息
- [x] 模糊匹配时显示同义词映射详情
- [x] 显示"本体使用总结"
- [x] 人工标注功能可用
- [x] 可以导出推理数据和本体使用JSON
- [x] 代码结构清晰，符合工程化标准
- [x] 所有模块有类型注解和文档字符串

## 后续计划

### 阶段2：批量验证与知识库展示（P1功能）

- 多张验证模式
- 批量推理 + 结果汇总
- 统计分析和混淆矩阵
- 知识库管理界面

### 与真实后端集成

替换 `services/mock_*.py` 为真实API调用，保持界面结构不变。
