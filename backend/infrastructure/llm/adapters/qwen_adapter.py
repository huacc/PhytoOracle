"""
千问VL API适配器

千问VL使用完全不同于OpenAI的API格式，需要专门的adapter处理。

作者：AI Python Architect
日期：2025-11-13
"""

import os
import base64
import requests
import sys
from typing import Optional, Type, TypeVar
from pathlib import Path
from pydantic import BaseModel

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from backend.infrastructure.llm.vlm_exceptions import (
        VLMException,
        ProviderUnavailableException,
        TimeoutException
    )
except ModuleNotFoundError:
    # 如果相对导入失败，尝试绝对导入（用于单独运行时）
    sys.path.insert(0, str(project_root))
    from backend.infrastructure.llm.vlm_exceptions import (
        VLMException,
        ProviderUnavailableException,
        TimeoutException
    )

T = TypeVar('T', bound=BaseModel)


class QwenVLAdapter:
    """
    千问VL API适配器

    千问VL使用阿里云DashScope API，格式与OpenAI完全不同：
    - 请求格式: {"model": "...", "input": {"messages": [...]}}
    - 响应格式: {"output": {"choices": [{"message": {"content": [...]}}]}}
    - 需要禁用代理（中国服务器）

    使用示例：
    ```python
    from backend.infrastructure.llm.adapters.qwen_adapter import QwenVLAdapter
    from backend.infrastructure.llm.prompts.response_schema import Q02Response

    # 初始化adapter
    adapter = QwenVLAdapter(
        api_key="sk-your-qwen-api-key",
        base_url="https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
        model="qwen-vl-plus"
    )

    # 调用API
    response = adapter.query(
        prompt="Identify the genus",
        response_model=Q02Response,
        image_bytes=image_bytes
    )
    ```
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str = "qwen-vl-plus",
        timeout: int = 60,
        max_retries: int = 3
    ):
        """
        初始化千问VL适配器

        Args:
            api_key: 千问API密钥
            base_url: API endpoint（完整URL，不需要追加路径）
            model: 模型名称（默认：qwen-vl-plus）
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

        # 千问是中国服务器，需要禁用代理
        self.proxies = {
            "http": None,
            "https": None
        }

    def query(
        self,
        prompt: str,
        response_model: Type[T],
        image_bytes: bytes
    ) -> T:
        """
        调用千问VL API并返回结构化响应

        Args:
            prompt: 提示词
            response_model: Pydantic响应模型（用于解析JSON）
            image_bytes: 图片字节数据

        Returns:
            T: 解析后的Pydantic模型实例

        Raises:
            ProviderUnavailableException: API不可用
            TimeoutException: 请求超时
            VLMException: 其他VLM错误
        """
        # 1. 编码图片为base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        # 2. 构造千问API请求格式
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "image": f"data:image/jpeg;base64,{image_base64}"
                            },
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
        }

        # 3. 重试机制
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout,
                    proxies=self.proxies
                )
                response.raise_for_status()

                # 4. 解析千问API响应
                result = response.json()

                # 千问返回格式: output.choices[0].message.content是数组
                if "output" in result and "choices" in result["output"]:
                    content_array = result["output"]["choices"][0]["message"]["content"]

                    # 提取text内容
                    if isinstance(content_array, list) and len(content_array) > 0:
                        text_content = content_array[0].get("text", "")
                    else:
                        text_content = str(content_array)

                    # 5. 解析为Pydantic模型
                    # 尝试直接解析JSON
                    try:
                        import json
                        # 如果文本包含JSON代码块，先提取
                        if "```json" in text_content:
                            import re
                            json_match = re.search(r'```json\s*\n(.*?)\n```', text_content, re.DOTALL)
                            if json_match:
                                text_content = json_match.group(1)

                        # 解析JSON并创建Pydantic模型
                        json_data = json.loads(text_content)
                        return response_model(**json_data)

                    except json.JSONDecodeError:
                        # 如果不是JSON格式，尝试从文本中提取字段值
                        # 这里可以添加更复杂的解析逻辑
                        raise VLMException(
                            f"Failed to parse Qwen response as JSON: {text_content}",
                            provider="qwen"
                        )

                else:
                    raise VLMException(
                        f"Unexpected Qwen API response format: {result}",
                        provider="qwen"
                    )

            except requests.exceptions.Timeout as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    continue
                else:
                    raise TimeoutException(
                        f"Qwen API timeout after {self.max_retries} attempts",
                        provider="qwen",
                        timeout=self.timeout
                    ) from e

            except requests.exceptions.HTTPError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    continue
                else:
                    raise ProviderUnavailableException(
                        f"Qwen API error: {e.response.text}",
                        provider="qwen"
                    ) from e

            except Exception as e:
                if "VLMException" in type(e).__name__:
                    raise
                raise VLMException(
                    f"Unexpected error calling Qwen VL API: {str(e)}",
                    provider="qwen"
                ) from e

        if last_error:
            raise last_error


# ==================== 测试示例 ====================

if __name__ == "__main__":
    """
    千问VL适配器测试

    需要：
    1. 设置环境变量：VLM_QWEN_VL_API_KEY
    2. 准备测试图片
    """
    import sys
    from pathlib import Path

    # 添加项目根目录到路径
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    from backend.infrastructure.llm.prompts.response_schema import Q02Response

    print("=" * 80)
    print("千问VL适配器测试")
    print("=" * 80)

    # 1. 检查API密钥
    api_key = os.getenv("VLM_QWEN_VL_API_KEY")
    if not api_key:
        print("\n[ERROR] 环境变量 VLM_QWEN_VL_API_KEY 未设置")
        print("请设置: set VLM_QWEN_VL_API_KEY=your-api-key")
        exit(1)

    print(f"\n[OK] API Key: {api_key[:20]}...")

    # 2. 初始化adapter
    adapter = QwenVLAdapter(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
        model="qwen-vl-plus"
    )
    print("[OK] Adapter initialized")

    # 3. 准备测试图片（使用streamlit的favicon作为测试）
    # Qwen要求图片尺寸 >10 pixels
    # 从backend/infrastructure/llm/adapters向上4级到达项目根目录
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    test_image_path = project_root / "venv" / "Lib" / "site-packages" / "streamlit" / "static" / "favicon.png"
    if not test_image_path.exists():
        print(f"\n[ERROR] Test image not found: {test_image_path}")
        exit(1)

    with open(test_image_path, 'rb') as f:
        test_image = f.read()

    print(f"[OK] Test image loaded: {len(test_image)} bytes")

    # 4. 调用API
    print("\n[CALL] Querying Qwen VL API...")
    try:
        response = adapter.query(
            prompt="Identify the genus of this flower: Rosa, Prunus, Tulipa, Dianthus, Paeonia, or unknown. Please respond ONLY with a JSON object in this exact format: {\"choice\": \"value\", \"confidence\": 0.0, \"reasoning\": \"brief explanation\"}",
            response_model=Q02Response,
            image_bytes=test_image
        )

        print(f"[SUCCESS] API call completed!")
        print(f"   Response type: {type(response).__name__}")
        print(f"   Genus: {response.choice}")
        print(f"   Confidence: {response.confidence}")
        print(f"   Reasoning: {response.reasoning}")

    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {str(e)}")

    print("\n" + "=" * 80)
