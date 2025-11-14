# 测试图片说明

## 图片命名规则

测试图片文件名必须包含疾病信息，格式为：`{disease_id}_{序号}.jpg`

示例：
- `rose_black_spot_001.jpg` - 玫瑰黑斑病（第1张）
- `rose_black_spot_002.jpg` - 玫瑰黑斑病（第2张）
- `rose_powdery_mildew_001.jpg` - 玫瑰白粉病（第1张）
- `cherry_brown_rot_001.jpg` - 樱花褐腐病（第1张）
- `unknown_flower_001.jpg` - 未知疾病（用于测试异常情况）

## 支持的疾病ID

| 疾病ID | 疾病名称 | 花属 |
|--------|---------|------|
| rose_black_spot | 玫瑰黑斑病 | Rosa |
| rose_powdery_mildew | 玫瑰白粉病 | Rosa |
| cherry_brown_rot | 樱花褐腐病 | Prunus |

## 获取测试图片

您可以：
1. 使用真实的植物病害图片（重命名为上述格式）
2. 使用任意图片进行测试（假数据推理引擎会根据文件名生成推理结果）

## 占位图片

由于Git不适合存储二进制图片文件，请手动添加测试图片到此目录。

如果没有图片，可以直接上传任意图片，只要文件名符合规则即可。
