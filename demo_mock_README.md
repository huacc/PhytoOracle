# PhytoOracle Mock 演示脚本使用指南

## 快速开始（5分钟内跑通）

### 1. 安装依赖

```bash
pip install streamlit pillow
```

### 2. 运行脚本

```bash
streamlit run demo_mock.py
```

浏览器将自动打开 http://localhost:8501

### 3. 演示场景

脚本包含 **5种诊断场景**，完整演示修复后的逻辑：

#### 🟢 场景1：确诊 - 玫瑰黑斑病
- **演示内容**：
  - total_score = 0.92（≥ 0.85）
  - major_matched = 2/2（主要特征全匹配）
  - 置信度级别：`confirmed`
- **验证缺陷修复**：
  - ✅ DiagnosisScore 包含 `major_matched` 和 `major_total` 字段
  - ✅ 医学诊断逻辑：确诊需要主要特征 ≥2/2

#### 🟡 场景2：疑似 - 樱花白粉病
- **演示内容**：
  - total_score = 0.72（0.60 ~ 0.85）
  - major_matched = 1/2（部分主要特征匹配）
  - 置信度级别：`suspected`
  - 返回 Top 3 候选疾病
- **验证缺陷修复**：
  - ✅ 疑似诊断需要 major_matched ≥ 1/2

#### ⚪ 场景3：知识库无数据 - 茉莉花未收录
- **演示内容**：
  - 花卉种属：Jasminum（茉莉花属，未收录）
  - 置信度级别：`unknown`
  - message: "知识库中暂无 Jasminum 的疾病数据"
  - suggestion: "请联系管理员添加该花卉的疾病知识库"
- **验证缺陷修复**：
  - ✅ 兜底逻辑1：候选疾病为空时的处理
  - ✅ 新增 `message` 和 `suggestion` 字段

#### 🔵 场景4：VLM兜底 - 知识库外疾病
- **演示内容**：
  - total_score = 0.18（< 0.30，触发VLM兜底）
  - major_matched = 0/2（主要特征不匹配）
  - 置信度级别：`vlm_fallback`
  - vlm_suggestion: "观察到叶片边缘有不规则褐色斑点..."
- **验证缺陷修复**：
  - ✅ 兜底逻辑2：低分数时调用 `_vlm_open_ended_diagnosis()`
  - ✅ 新增 `vlm_suggestion` 字段存储VLM开放式诊断结果

#### 🔴 场景5：系统错误 - VLM完全失败
- **演示内容**：
  - 所有VLM Provider都失败
  - 置信度级别：`system_error`
  - message: "诊断系统暂时不可用"
  - suggestion: "VLM服务异常: All VLM providers failed，请稍后重试"
- **验证缺陷修复**：
  - ✅ 兜底逻辑3：VLMError异常捕获
  - ✅ ConfidenceLevel 新增 `system_error` 状态

---

## 修复内容对照表

| 缺陷 | 修复内容 | 演示场景 | 文档位置 |
|------|---------|---------|---------|
| **缺陷1: DiagnosisScore置信度逻辑不完整** | 新增 `major_matched`/`major_total` 字段，实现医学诊断逻辑 | 场景1-5 | 详细设计文档 3.3节、7章 |
| **缺陷2: VLM响应协议缺失** | 定义 Pydantic Schema + ResponseValidator + 完整Q0-Q6模板 | 所有场景 | 详细设计文档 5.6节 |
| **缺陷3: 兜底逻辑缺失** | 3种兜底场景（unknown/vlm_fallback/system_error） | 场景3-5 | 详细设计文档 5.1节、7章 |

---

## 技术实现

### 数据模型（符合设计文档第7章）

```python
class ConfidenceLevel(str, Enum):
    CONFIRMED = "confirmed"          # 确诊
    SUSPECTED = "suspected"          # 疑似
    UNLIKELY = "unlikely"            # 不太可能
    UNKNOWN = "unknown"              # 知识库无数据（新增）
    VLM_FALLBACK = "vlm_fallback"   # VLM兜底（新增）
    SYSTEM_ERROR = "system_error"    # 系统错误（新增）

class DiagnosisResult:
    # ... 原有字段 ...
    message: Optional[str]            # 新增：兜底场景说明
    suggestion: Optional[str]         # 新增：给用户的建议
    vlm_suggestion: Optional[str]     # 新增：VLM开放式诊断
    feature_vector: Optional[FeatureVector]  # 修改：改为Optional
    scores: Optional[DiagnosisScore]         # 修改：改为Optional
```

### 诊断流程（符合设计文档5.1节）

```python
# 兜底逻辑1：无候选疾病
if not candidate_diseases:
    return DiagnosisResult(level="unknown", message="知识库无数据")

# 兜底逻辑2：分数过低
if best_match.total_score < 0.30:
    try:
        vlm_diagnosis = await _vlm_open_ended_diagnosis(image_bytes)
        return DiagnosisResult(level="vlm_fallback", vlm_suggestion=vlm_diagnosis)
    except VLMError as e:
        # 兜底逻辑3：VLM完全失败
        return DiagnosisResult(level="system_error", error=str(e))
```

---

## 运行截图说明

运行脚本后，您将看到：

1. **左侧边栏**：选择5种演示场景
2. **左侧主区域**：上传图片区（Mock演示中可不上传）
3. **右侧主区域**：诊断结果展示
   - 诊断ID和执行时间
   - 诊断级别（彩色标签）
   - 主要诊断结果
   - 兜底逻辑特殊字段（message/suggestion/vlm_suggestion）
   - 候选疾病列表（疑似诊断时）
   - 诊断评分详情（含医学诊断逻辑验证）
   - 特征向量（可展开查看）

---

## 下一步

此 Mock 脚本演示了修复后的逻辑，实际开发时需要：

1. **实现真实VLM调用**：
   - 集成 Qwen VL Plus / ChatGPT-4o / Grok Vision / Claude Sonnet
   - 实现 ResponseValidator（5.6.2节）
   - 使用 5.6.3节的完整提示词模板

2. **实现知识库加载**：
   - 从 `backend/knowledge_base/` 加载JSON本体
   - 实现 `KnowledgeBaseAggregate.get_diseases_by_genus()`
   - 实现模糊匹配引擎（5.3节）

3. **实现评分引擎**：
   - 实现 `DiagnosisScorer.calculate_score()`（5.4节）
   - 包含 `_count_major_matched()` 方法

4. **集成数据库**：
   - PostgreSQL 存储诊断记录
   - Redis 缓存VLM响应

---

## 故障排除

### 问题1：streamlit command not found
```bash
# 解决方法
pip install --upgrade streamlit
```

### 问题2：端口8501被占用
```bash
# 解决方法：指定其他端口
streamlit run demo_mock.py --server.port 8502
```

### 问题3：浏览器未自动打开
手动访问：http://localhost:8501

---

**版本**: Mock Demo v1.0
**最后更新**: 2025-11-11
**适配设计文档**: 详细设计文档 v1.3
