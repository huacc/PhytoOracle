# PhytoOracle Frontend Demo 实现计划

**版本**: v1.0
**创建时间**: 2025-11-13
**目标**: 使用假数据快速搭建可演示的 Streamlit 管理后台
**参考文档**: `docs/requirements/界面需求文档.md`

---

## 1. 功能优先级划分

### P0 - 核心展示功能（必须实现）
- 推理调试中心 - 单张调试模式（Tab 1）
  - 图片上传与推理结果展示
  - 推理过程可视化（含本体追溯）
  - 人工标注界面
  - 本体使用导出功能
- 假数据推理引擎（模拟完整推理链路）

### P1 - 增强展示功能（建议实现）
- 推理调试中心 - 多张验证模式（Tab 2）
  - 批量结果汇总表格
  - 基础统计分析
  - 混淆矩阵可视化
- 知识库管理界面（只读展示）
  - 疾病列表展示
  - 疾病详情查看

### P2 - 辅助展示功能（可选实现）
- 推理调试中心 - 图片对比（Tab 3）
- 统计分析界面
  - 全局统计
  - 准确率趋势图

---

## 2. 假数据准备清单

### 2.1 植物疾病本体数据

**Feature Ontology 数据**（feature_ontology_demo.json）:
```json
{
  "symptom_type": {
    "values": ["necrosis_spot", "chlorosis", "wilting", "powdery_coating", "rust"],
    "synonyms": {
      "necrosis_spot": ["dark_spot", "black_spot", "necrotic_lesion"]
    }
  },
  "color_center": {
    "values": ["black", "brown", "white", "yellow", "red"],
    "synonyms": {
      "black": ["dark_brown", "very_dark"]
    }
  },
  "color_border": {
    "values": ["yellow", "brown", "black", "white", "none"],
    "synonyms": {
      "yellow_halo": ["yellow", "yellowish", "light_yellow"]
    }
  }
}
```

**疾病定义数据**（3-5种疾病）:
- rose_black_spot (玫瑰黑斑病)
- rose_powdery_mildew (玫瑰白粉病)
- cherry_blossom_powdery_mildew (樱花白粉病)

### 2.2 推理结果数据

**单张推理结果模板**（包含完整链路）:
- Q0 序列结果（6个问题）
- Q1-Q6 特征提取结果（7个特征）
- 候选疾病列表（2-3个候选）
- 加权评分结果（含匹配详情和本体引用）
- 最终诊断结果

**批量推理结果数据**（10-15张图片）:
- 不同花属：Rosa (6张), Prunus (4张), Paeonia (3张)
- 不同诊断结果：正确 (8张), 错误 (3张), 未标注 (4张)
- 不同置信度级别：confirmed (7张), suspected (5张), unlikely (3张)

### 2.3 测试图片素材

**图片来源**（使用占位图或真实植物病害图片）:
- 玫瑰黑斑病图片：6张（rose_001.jpg ~ rose_006.jpg）
- 玫瑰白粉病图片：3张
- 樱花白粉病图片：3张
- 正常植物图片：3张

**图片存储**:
```
demo/
  assets/
    images/
      rose_black_spot_001.jpg
      rose_black_spot_002.jpg
      rose_powdery_mildew_001.jpg
      cherry_blossom_001.jpg
      ...
```

### 2.4 标注数据

**标注记录**（10条）:
- 正确标注：6条
- 错误标注：3条（附带实际疾病ID和备注）
- 未标注：1条

---

## 3. 技术方案决策

### 3.1 Streamlit 架构

**多页面应用结构**:
```
frontend_demo/
  app.py                          # 主入口（Home页）
  pages/
    1_推理调试中心.py              # 核心功能
    2_知识库管理.py                # P1功能
    3_统计分析.py                  # P2功能
  components/
    diagnosis_visualizer.py       # 推理过程可视化组件
    confusion_matrix.py           # 混淆矩阵组件
    ontology_explorer.py          # 本体浏览器组件
  data/
    fake_data_generator.py        # 假数据生成器
    feature_ontology_demo.json    # 特征本体
    diseases_demo.json            # 疾病定义
  assets/
    images/                        # 测试图片
  utils/
    diagnosis_engine.py           # 假数据推理引擎
    data_loader.py                # 数据加载工具
```

### 3.2 假数据推理引擎设计

**核心原则**: 逻辑一致性 > 随机性

**实现方式**:
1. 根据图片文件名解析疾病类型（如 `rose_black_spot_001.jpg`）
2. 基于疾病类型生成对应的推理链路数据
3. 使用预定义的模板 + 随机扰动（confidence score 浮动 ±0.05）
4. 确保同一疾病的不同图片推理结果高度相似

**关键函数**:
```python
def generate_diagnosis_result(image_path, disease_type):
    """根据疾病类型生成一致的推理结果"""
    # 1. Q0 序列生成
    q0_sequence = generate_q0_sequence(disease_type)

    # 2. 特征提取生成
    feature_extraction = generate_feature_extraction(disease_type)

    # 3. 候选疾病筛选
    candidates = filter_candidates(q0_sequence["q0_2_flower_genus"])

    # 4. 加权评分（含本体引用）
    scoring_results = calculate_scoring(
        feature_extraction,
        candidates,
        disease_type
    )

    # 5. 最终诊断
    final_diagnosis = scoring_results[0]  # 取最高分

    return {
        "q0_sequence": q0_sequence,
        "feature_extraction": feature_extraction,
        "scoring_results": scoring_results,
        "final_diagnosis": final_diagnosis
    }
```

### 3.3 本体追溯展示方案

**展示层次**:
```
[Q0.0 内容类型] → plant (置信度: 0.98)
  📖 本体定义: Q0.0_content_type
      可选值: ["plant", "non_plant", "unclear"]
```

**实现组件**:
```python
def render_ontology_reference(step_name, choice, ontology_info):
    """渲染本体引用信息"""
    st.markdown(f"**[{step_name}]** → {choice}")
    with st.expander("📖 查看本体定义"):
        st.json(ontology_info)
```

### 3.4 Session State 管理

**状态变量**:
- `current_diagnosis`: 当前推理结果
- `annotation_data`: 标注信息
- `uploaded_images`: 已上传图片列表
- `batch_results`: 批量推理结果

**状态初始化**:
```python
def init_session_state():
    if "current_diagnosis" not in st.session_state:
        st.session_state.current_diagnosis = None
    if "annotation_data" not in st.session_state:
        st.session_state.annotation_data = {}
```

---

## 4. 分阶段实现计划

### 阶段 1：核心推理展示（P0功能）

**阶段目标**:
- 实现单张图片上传与推理结果展示
- 完整展示推理链路（Q0 → Q1-Q6 → 匹配 → 评分）
- 明确显示本体追溯信息
- 实现人工标注和本体使用导出功能

**实现的界面**:
- 主页（app.py）：应用介绍和快速导航
- 推理调试中心 - Tab 1：单张调试模式

**实现的功能**:

1. **图片上传模块**
   - 使用 `st.file_uploader` 支持拖拽上传
   - 显示图片预览（`st.image`）
   - 显示图片尺寸和文件大小

2. **假数据推理引擎**
   - 实现 `fake_data_generator.py`
   - 根据图片文件名解析疾病类型
   - 生成完整推理链路数据（含本体引用）

3. **推理过程可视化**（components/diagnosis_visualizer.py）
   - Q0 序列展示（6个问题，使用 `st.expander`）
   - 特征提取展示（7个特征，表格形式）
   - 候选疾病列表（卡片形式）
   - 加权评分详情（含本体引用，使用 `st.columns` 并排展示）
   - 最终诊断结果（突出显示）

4. **本体追溯展示**
   - 每个推理步骤显示 "📖 查看本体定义" 按钮
   - 展开显示本体来源、可选值、同义词列表
   - 模糊匹配时展示同义词映射过程

5. **人工标注界面**
   - 准确性标注：单选框（正确/错误/不确定）
   - 实际疾病标注：下拉选择框（当标注为错误时显示）
   - 标注备注：文本输入框
   - 保存标注按钮

6. **本体使用导出功能**
   - 生成本体使用 JSON
   - 显示使用的本体文件清单
   - 显示关键同义词映射
   - 提供下载按钮（`st.download_button`）

**检查标准**:

- [ ] 上传任意图片后能看到完整的推理链路展示
- [ ] 推理链路包含以下所有环节：
  - [ ] Q0.0 ~ Q0.5 的结果和本体引用
  - [ ] Q1-Q6 特征提取结果和本体引用
  - [ ] 候选疾病列表（2-3个候选）
  - [ ] 加权评分详情（每个疾病的匹配详情）
  - [ ] 最终诊断结果（疾病名称、置信度、治疗建议）
- [ ] 本体追溯功能正常：
  - [ ] 每个步骤都能查看本体定义
  - [ ] 模糊匹配时显示同义词映射
  - [ ] 本体引用信息准确（文件路径、版本号）
- [ ] 人工标注功能正常：
  - [ ] 可以选择准确性
  - [ ] 标注为错误时显示实际疾病选择框
  - [ ] 可以输入备注
  - [ ] 点击保存后显示成功提示
- [ ] 本体使用导出功能正常：
  - [ ] 显示完整的本体使用清单
  - [ ] 可以下载 JSON 文件
  - [ ] JSON 内容包含所有本体引用信息
- [ ] 界面响应流畅，无卡顿

**实现时间**: 2-3天

---

### 阶段 2：批量验证与知识库展示（P1功能）

**阶段目标**:
- 实现批量图片上传与推理
- 展示批量推理结果汇总表格
- 实现基础统计分析和混淆矩阵
- 实现知识库管理界面（只读展示）

**实现的界面**:
- 推理调试中心 - Tab 2：多张验证模式
- 知识库管理页面（pages/2_知识库管理.py）

**实现的功能**:

1. **批量上传模块**（Tab 2）
   - 支持一次上传多张图片（5-20张）
   - 显示上传进度条（`st.progress`）
   - 缩略图列表预览

2. **批量推理功能**
   - 一键触发批量推理（使用 `st.spinner`）
   - 遍历所有图片生成推理结果
   - 模拟异步处理（延迟 0.5秒/张）

3. **结果汇总表格**
   - 使用 `st.dataframe` 展示结果
   - 包含字段：图片名、花属、诊断结果、置信度、准确性标注、操作按钮
   - 支持排序和筛选

4. **统计分析模块**
   - 总诊断量、准确率、未标注数
   - 按置信度级别统计（confirmed/suspected/unlikely）
   - 按花属统计（Rosa/Prunus/Paeonia）
   - 使用 `st.metrics` 展示关键指标

5. **混淆矩阵可视化**（components/confusion_matrix.py）
   - 使用 `plotly.express.imshow` 绘制热力图
   - 显示实际疾病 vs 预测疾病
   - 支持交互（悬停显示数值）

6. **知识库管理界面**
   - 疾病列表表格（只读）
   - 疾病详情查看器（JSON展示）
   - Feature Ontology 浏览器（树形展示）

**检查标准**:

- [ ] 批量上传功能正常：
  - [ ] 可以一次上传多张图片
  - [ ] 显示上传进度
  - [ ] 所有图片成功加载
- [ ] 批量推理功能正常：
  - [ ] 点击推理按钮后显示进度
  - [ ] 所有图片都生成推理结果
  - [ ] 推理结果逻辑一致（同类疾病结果相似）
- [ ] 结果汇总表格正确：
  - [ ] 显示所有必需字段
  - [ ] 准确性标注正确关联
  - [ ] 点击"查看详情"可以跳转到单张调试模式
- [ ] 统计分析准确：
  - [ ] 总诊断量 = 上传图片数
  - [ ] 准确率计算正确（正确数 / 已标注数）
  - [ ] 按置信度和花属统计数据正确
- [ ] 混淆矩阵正确：
  - [ ] 仅包含已标注的图片
  - [ ] 矩阵数值与标注数据一致
  - [ ] 热力图颜色区分明显
- [ ] 知识库管理界面正常：
  - [ ] 疾病列表展示正确
  - [ ] 点击疾病可以查看完整 JSON
  - [ ] Feature Ontology 树形结构清晰

**实现时间**: 2-3天

---

### 阶段 3（可选）：图片对比与统计分析（P2功能）

**阶段目标**:
- 实现图片对比功能
- 实现统计分析界面（全局统计、趋势图）

**实现的界面**:
- 推理调试中心 - Tab 3：图片对比
- 统计分析页面（pages/3_统计分析.py）

**实现的功能**:

1. **图片选择模块**（Tab 3）
   - 从历史记录中选择 2-4 张图片
   - 支持按花属、诊断结果、准确性筛选
   - 多选框（`st.multiselect`）

2. **并排展示**
   - 使用 `st.columns` 并排显示图片
   - 显示关键推理信息（Q0.2、Q0.5、Q1-Q6、诊断结果）
   - 差异高亮（使用颜色标记）

3. **差异分析**
   - 自动计算特征值差异
   - 生成差异分析报告（文本）
   - 提供优化建议（假数据）

4. **统计分析界面**
   - 全局统计卡片（`st.metrics`）
   - 准确率趋势图（`st.line_chart`）
   - 误诊案例列表（`st.dataframe`）
   - 导出功能（CSV/JSON）

**检查标准**:

- [ ] 图片对比功能正常：
  - [ ] 可以选择 2-4 张图片
  - [ ] 并排展示清晰
  - [ ] 差异高亮准确
- [ ] 差异分析正确：
  - [ ] 自动识别特征差异
  - [ ] 分析报告合理
- [ ] 统计分析界面完整：
  - [ ] 全局统计数据准确
  - [ ] 趋势图展示正常
  - [ ] 误诊案例列表正确
  - [ ] 导出功能正常

**实现时间**: 1-2天

---

## 5. 假数据逻辑一致性规则

### 5.1 疾病特征映射表

确保同一疾病的推理结果高度一致：

| 疾病类型 | Q0.2 花属 | Q1 症状类型 | Q2 中心颜色 | Q3 边缘颜色 | Q4 质地 | Q5 形状 | Q6 分布 | 大小 |
|---------|----------|------------|------------|------------|---------|---------|---------|------|
| rose_black_spot | Rosa | necrosis_spot | black | yellow | smooth | circular | scattered | medium |
| rose_powdery_mildew | Rosa | powdery_coating | white | none | powdery | irregular | uniform | small |
| cherry_blossom_powdery_mildew | Prunus | powdery_coating | white | none | powdery | irregular | clustered | small |

### 5.2 置信度生成规则

**正确诊断**（标注为 correct）:
- Q0 置信度: 0.90 ~ 0.98
- Q1-Q6 置信度: 0.85 ~ 0.95
- 最终诊断置信度: 0.85 ~ 0.95（confirmed）

**误诊案例**（标注为 incorrect）:
- 某个特征识别错误（如 Q2 颜色识别为 dark_brown 而非 black）
- 导致加权分数降低: 0.70 ~ 0.82（suspected）
- 或完全错误诊断: 0.50 ~ 0.68（suspected）

**未标注案例**:
- 随机分布在 confirmed 和 suspected 之间

### 5.3 同义词映射示例

**精确匹配**:
- VLM 识别: "necrosis_spot" → 疾病定义: "necrosis_spot"

**模糊匹配**（生成同义词映射详情）:
- VLM 识别: "yellow" → 疾病定义: "yellow_halo"
- 同义词来源: feature_ontology.json → color_border → synonyms → yellow_halo
- 模糊分数: 0.85

### 5.4 批量推理数据分布

**总数**: 15张图片

**按花属分布**:
- Rosa: 7张（玫瑰黑斑病 4张，玫瑰白粉病 3张）
- Prunus: 5张（樱花白粉病 5张）
- Paeonia: 3张（牡丹褐斑病 3张）

**按标注分布**:
- 正确: 8张（准确率 80%）
- 错误: 2张（误诊案例）
- 未标注: 5张

**按置信度分布**:
- confirmed (0.85-0.95): 7张（准确率 85.7%）
- suspected (0.70-0.84): 5张（准确率 60%）
- unlikely (<0.70): 3张（准确率 0%）

---

## 6. 开发注意事项

### 6.1 Streamlit 最佳实践

1. **缓存使用**:
   - 使用 `@st.cache_data` 缓存假数据加载
   - 使用 `@st.cache_resource` 缓存推理引擎初始化

2. **Session State 管理**:
   - 在 `app.py` 中统一初始化
   - 避免跨页面状态丢失

3. **组件复用**:
   - 推理可视化组件封装为独立函数
   - 使用 `st.components` 组织代码

4. **性能优化**:
   - 避免不必要的重跑（使用 `st.form`）
   - 图片加载使用懒加载

### 6.2 假数据质量要求

1. **逻辑一致性**:
   - 同一疾病的特征必须一致
   - 推理链路必须符合算法逻辑

2. **数据完整性**:
   - 每个推理结果包含所有必需字段
   - 本体引用信息完整

3. **可读性**:
   - JSON 格式化输出
   - 中英文名称对照

### 6.3 界面交互设计

1. **反馈及时**:
   - 使用 `st.success` / `st.error` 提示操作结果
   - 长时间操作显示 `st.spinner`

2. **信息分层**:
   - 使用 `st.expander` 折叠次要信息
   - 使用 `st.tabs` 组织多个视图

3. **导航清晰**:
   - 侧边栏显示页面导航
   - 使用 `st.page_link` 跨页面跳转

---

## 7. 验收标准总结

### 阶段 1 验收标准（P0 必须）

- [ ] 单张调试模式完全可用
- [ ] 推理链路完整展示（Q0 → Q1-Q6 → 匹配 → 评分）
- [ ] 本体追溯信息清晰（每个步骤都有本体引用）
- [ ] 同义词映射详情正确展示
- [ ] 人工标注功能正常
- [ ] 本体使用导出功能正常（JSON 格式）
- [ ] 假数据逻辑一致（同类疾病结果相似）

### 阶段 2 验收标准（P1 建议）

- [ ] 批量验证模式完全可用
- [ ] 结果汇总表格准确
- [ ] 统计分析数据正确（准确率、混淆矩阵）
- [ ] 知识库管理界面可浏览

### 阶段 3 验收标准（P2 可选）

- [ ] 图片对比功能正常
- [ ] 统计分析界面完整

### 整体验收标准

- [ ] 界面美观、操作流畅
- [ ] 无明显 bug 和错误提示
- [ ] 假数据质量高（逻辑一致、信息完整）
- [ ] 代码结构清晰、易于维护
- [ ] 有基本的注释和文档

---

## 8. 后续计划

### 与真实后端集成

**替换点**:
1. 将 `fake_data_generator.py` 替换为真实 API 调用
2. 将 `utils/diagnosis_engine.py` 替换为后端 `/api/v1/diagnose` 接口
3. 将本地 JSON 文件替换为后端 API 数据源

**保持不变**:
- 界面结构和组件
- 用户交互流程
- 数据展示逻辑

### Demo 演示脚本

**演示流程**（5-8 分钟）:
1. **介绍应用定位**（1 分钟）
   - MVP 目标：推理引擎验证工具
   - 核心价值：可视化推理链路 + 知识库迭代

2. **单张调试演示**（3 分钟）
   - 上传玫瑰黑斑病图片
   - 展示完整推理过程（Q0 → Q1-Q6 → 匹配 → 评分）
   - 突出本体追溯功能（点击查看本体定义）
   - 展示同义词映射详情
   - 演示人工标注
   - 导出本体使用 JSON

3. **批量验证演示**（2 分钟）
   - 上传 10 张图片
   - 展示批量推理结果
   - 查看统计分析和混淆矩阵
   - 导出误诊案例

4. **知识库管理演示**（1 分钟）
   - 浏览疾病列表
   - 查看疾病详情 JSON
   - 浏览 Feature Ontology

5. **总结与后续计划**（1 分钟）
   - Demo 实现的功能
   - 与真实后端集成计划
   - MVP 交付时间表

---

**计划结束**
