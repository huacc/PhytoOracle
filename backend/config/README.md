# 配置文件说明

## llm_config.json

**⚠️ 重要**: 此文件包含敏感的 API Key，已被 `.gitignore` 排除，不会上传到 GitHub。

### 如何配置

1. 复制模板文件创建真实配置：
   ```bash
   cp llm_config.json.example llm_config.json
   ```

2. 编辑 `llm_config.json`，将占位符替换为真实的 API Key：
   - `YOUR_GEMINI_API_KEY_HERE` → 你的 Google Gemini API Key
   - `YOUR_QWEN_API_KEY_HERE` → 你的通义千问 API Key
   - `YOUR_DOUBAO_API_KEY_HERE` → 你的豆包 API Key
   - `YOUR_GLM_API_KEY_HERE` → 你的智谱 GLM API Key
   - `YOUR_GROK_API_KEY_HERE` → 你的 Grok API Key

3. 设置激活的 Provider：
   ```json
   "active_provider": "qwen_vl"
   ```

### 配置结构

```json
{
  "version": "2.0",
  "active_provider": "qwen_vl",  // 当前激活的 VLM Provider
  "providers": {
    "qwen_vl": {
      "name": "通义千问 VL Plus",
      "model": "qwen-vl-plus",
      "api_key": "YOUR_API_KEY_HERE",  // ⚠️ 替换为真实 API Key
      "base_url": "https://dashscope.aliyuncs.com/...",
      "timeout": 30,
      "max_retries": 3,
      ...
    }
  },
  "fallback_strategy": {
    "enabled": true,
    "order": ["gemini", "qwen_vl", "doubao"]  // Fallback 顺序
  }
}
```

### 支持的 VLM Provider

| Provider | 名称 | 费用 | 免费额度 | 推荐场景 |
|----------|------|------|---------|---------|
| Gemini 2.0 Flash | Google Gemini | 免费 | 1500次/天 | 主力推荐 |
| Qwen VL Plus | 通义千问 | 免费 | 1000次/天 | 国内备用 |
| Doubao Vision | 豆包视觉版 | 付费 | - | 超额时使用 |
| GLM-4V | 智谱AI | 免费 | 10000次/天 | 高额度需求 |
| Grok Vision | xAI Grok | 免费 | - | 实验性 |

### Fallback 机制

当前激活的 Provider 失败时，会按照 `fallback_strategy.order` 中定义的顺序自动切换到下一个可用的 Provider。

### 安全注意事项

1. ❌ **绝对不要** 将 `llm_config.json` 上传到 GitHub
2. ✅ 确保 `.gitignore` 包含 `backend/config/llm_config.json`
3. ✅ 仅在本地开发环境使用，不要分享给他人
4. ✅ 定期更换 API Key（如怀疑泄露）

### 获取 API Key

- **Gemini**: https://aistudio.google.com/app/apikey
- **Qwen VL Plus**: https://dashscope.console.aliyun.com/
- **Doubao**: https://console.volcengine.com/ark
- **GLM-4V**: https://open.bigmodel.cn/
- **Grok**: https://console.x.ai/

---

**文档更新时间**: 2025-11-12
