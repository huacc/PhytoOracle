# PhytoOracle Frontend Demo - 快速启动指南

## 目录结构

当前实现的文件清单：

```
d:\项目管理\PhytoOracle\demo\frontend_demo\
├── app.py                                    ✅ 主入口
├── config.py                                 ✅ 配置文件
├── requirements.txt                          ✅ 依赖清单
├── README.md                                 ✅ 使用说明
├── test_functionality.py                     ✅ 功能测试脚本
├── DELIVERY_REPORT.md                        ✅ 验收报告
│
├── pages/
│   └── 1_推理调试中心.py                      ✅ 核心页面
│
├── components/                               ✅ UI组件
│   ├── __init__.py
│   ├── diagnosis_visualizer.py
│   ├── ontology_tracer.py
│   └── annotation_panel.py
│
├── services/                                 ✅ 业务逻辑
│   ├── __init__.py
│   ├── mock_diagnosis_engine.py
│   └── mock_knowledge_service.py
│
├── models/                                   ✅ 数据模型
│   ├── __init__.py
│   ├── diagnosis_result.py
│   ├── ontology_usage.py
│   └── annotation.py
│
├── data/                                     ✅ 假数据
│   ├── diseases/
│   │   ├── rose_black_spot_v4.2.json
│   │   ├── rose_powdery_mildew_v3.1.json
│   │   └── cherry_brown_rot_v2.0.json
│   └── ontology/
│       └── feature_ontology.json
│
├── assets/                                   ✅ 静态资源
│   └── images/
│       └── README.md
│
└── utils/                                    ✅ 工具函数
    ├── __init__.py
    └── export_helper.py
```

## 快速启动（3步）

### 1. 安装依赖

```bash
cd d:\项目管理\PhytoOracle\demo\frontend_demo
pip install -r requirements.txt
```

### 2. 运行测试（可选）

```bash
python test_functionality.py
```

应该看到所有测试通过的消息。

### 3. 启动应用

```bash
streamlit run app.py
```

浏览器自动打开 `http://localhost:8501`

## 使用流程

1. **访问推理调试中心**
   - 点击侧边栏"推理调试中心"

2. **上传图片**
   - 拖拽或点击上传图片
   - 文件名应包含疾病信息（如 `rose_black_spot_001.jpg`）

3. **执行推理**
   - 点击"开始推理"按钮
   - 查看完整推理过程

4. **查看本体追溯**
   - 每个步骤都有"📖 查看本体定义"按钮
   - 点击展开查看本体引用详情

5. **进行人工标注**
   - 选择诊断准确性
   - 如果错误，选择实际疾病
   - 填写备注

6. **导出数据**
   - 下载推理结果JSON
   - 下载本体使用清单JSON

## 支持的测试图片

由于文件名包含疾病信息，您可以使用任意图片，只需命名为：

- `rose_black_spot_001.jpg` → 识别为玫瑰黑斑病
- `rose_powdery_mildew_001.jpg` → 识别为玫瑰白粉病
- `cherry_brown_rot_001.jpg` → 识别为樱花褐腐病

## 核心功能演示

### 推理链路完整性

推理过程包含以下环节：

1. **Q0序列（6步分类）**
   - Q0.0: content_type → plant
   - Q0.1: plant_category → flower
   - Q0.2: flower_genus → Rosa
   - Q0.3: organ_type → leaf
   - Q0.4: completeness → close_up
   - Q0.5: abnormality → abnormal

2. **Q1-Q6特征提取（7个特征）**
   - symptom_type, color_center, color_border
   - texture, shape, distribution, size

3. **候选疾病筛选**
   - 基于花属筛选（Rosa → 2个候选）

4. **模糊匹配 + 加权评分**
   - 精确匹配 / 模糊匹配 / 不匹配
   - 同义词映射详情展示

5. **最终诊断**
   - 疾病名称、置信度、治疗建议

### 本体追溯展示

每个推理步骤都明确显示：
- ✅ 本体文件路径
- ✅ 版本号
- ✅ 可选值列表
- ✅ 同义词映射详情（如有）
- ✅ 不匹配原因（如有）

## 疑难解答

### 问题1：启动时报错 "No module named 'streamlit'"

**解决方案**：
```bash
pip install streamlit>=1.38.0
```

### 问题2：启动时报错 "No module named 'pydantic'"

**解决方案**：
```bash
pip install pydantic>=2.0.0
```

### 问题3：中文显示乱码

**原因**：Windows控制台编码问题
**解决方案**：不影响Streamlit应用，浏览器中中文显示正常

### 问题4：没有测试图片

**解决方案**：使用任意图片，只需文件名包含疾病ID即可：
```
rose_black_spot_001.jpg
rose_powdery_mildew_001.jpg
cherry_brown_rot_001.jpg
```

## 阶段2功能（已实现）

### 新增页面

阶段2新增了以下3个页面：

1. **批量验证中心** (`pages/2_批量验证中心.py`)
   - 批量上传图片（5-50张）
   - 批量执行推理
   - 结果表格展示和筛选
   - 批量标注功能
   - 统计分析和混淆矩阵

2. **统计分析** (`pages/3_统计分析.py`)
   - 全局统计卡片
   - 分布分析图表（置信度、花卉属）
   - 混淆矩阵热力图
   - 置信度分数直方图
   - 误诊分析和优化建议

3. **知识库管理** (`pages/4_知识库管理.py`)
   - 疾病列表浏览
   - 疾病详情查看
   - 特征本体浏览
   - 疾病特征对比

### 阶段2使用流程

#### 批量验证

1. 访问「批量验证中心」页面
2. 上传多张图片（建议10-20张）
3. 点击「开始批量推理」
4. 在「结果列表」查看推理结果
5. 在「批量标注」完成人工标注
6. 在「统计分析」查看混淆矩阵

#### 统计分析

1. 完成批量推理后访问「统计分析」页面
2. 查看全局统计（准确率、误诊数）
3. 查看分布分析图表
4. 查看混淆矩阵
5. 查看误诊案例和优化建议

#### 知识库管理

1. 访问「知识库管理」页面
2. 在「疾病列表」查看所有疾病
3. 选择疾病查看详情
4. 在「特征本体」浏览完整本体定义
5. 在「疾病对比」对比两个疾病的特征差异

### 阶段2测试

运行阶段2功能测试：

```bash
python test_phase2_functionality.py
```

应该看到以下测试通过：
- ✅ 批量推理服务
- ✅ 统计计算功能
- ✅ 混淆矩阵生成
- ✅ 知识库服务
- ✅ 数据模型结构

## 下一步

### 与真实后端集成

替换假数据服务为真实API调用：
- `services/mock_diagnosis_engine.py` → 真实API
- `services/mock_knowledge_service.py` → 真实API
- `services/batch_diagnosis_service.py` → 批量推理API
- 界面结构保持不变

## 联系方式

如有问题，请参考：
- **README.md**: 详细使用说明
- **DELIVERY_REPORT.md**: 阶段1验收报告
- **PHASE2_DELIVERY_REPORT.md**: 阶段2交付报告
- **test_functionality.py**: 阶段1功能测试脚本
- **test_phase2_functionality.py**: 阶段2功能测试脚本

---

**祝使用愉快！**
