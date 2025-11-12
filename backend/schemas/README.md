# JSON Schema定义

本目录存放PhytoOracle项目的所有JSON Schema定义文件。

## 目录说明

- **disease_schema.json**: 疾病本体JSON Schema（Draft 7）
- **feature_schema.json**: 特征本体JSON Schema（Draft 7）
- **host_disease_schema.json**: 宿主-疾病关系JSON Schema（Draft 7）

## 用途

这些JSON Schema用于验证知识库JSON文件的结构和格式，确保：
1. 所有必需字段存在
2. 字段类型正确
3. 枚举值在允许范围内
4. 格式符合规范（如版本号格式）

## 使用方法

```python
import json
import jsonschema
from pathlib import Path

# 加载Schema
schema_path = Path(__file__).parent / "disease_schema.json"
schema = json.loads(schema_path.read_text(encoding="utf-8"))

# 验证JSON文件
disease_json = {...}  # 疾病JSON数据
jsonschema.validate(instance=disease_json, schema=schema)
```

## 验证脚本

完整的验证脚本见 `backend/tests/test_knowledge_base_validation.py`
