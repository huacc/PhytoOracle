"""
VLM 提供商API密钥验证脚本

目的：使用从FlowerSpecialist项目读取的真实API密钥测试不同的VLM提供商
测试提供商：Qwen VL、Gemini、GLM-4V、Grok

作者：AI Python Architect
日期：2025-11-13
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.infrastructure.llm.vlm_client import MultiProviderVLMClient
from backend.infrastructure.llm.prompts.response_schema import Q02Response


def load_api_keys_from_flower_specialist():
    """从FlowerSpecialist项目读取API密钥"""
    config_path = Path(r"D:\项目管理\NewBloomCheck\FlowerSpecialist\config\llm_config.json")

    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    api_keys = {}
    providers = config.get('providers', {})

    # 提取API密钥
    if 'qwen_vl' in providers:
        api_keys['qwen'] = providers['qwen_vl'].get('api_key')
    if 'gemini' in providers:
        api_keys['gemini'] = providers['gemini'].get('api_key')
    if 'glm_4v' in providers:
        api_keys['glm'] = providers['glm_4v'].get('api_key')
    if 'grok_vision' in providers:
        api_keys['grok'] = providers['grok_vision'].get('api_key')

    return api_keys


def test_provider(provider_name: str, api_key: str):
    """测试单个VLM提供商"""
    print(f"\n{'='*60}")
    print(f"[TEST] Provider: {provider_name}")
    print(f"{'='*60}")

    # 构造测试图片（最小PNG）
    test_image = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )

    # 设置环境变量（根据FlowerSpecialist配置中的api_key_env映射）
    # 从FlowerSpecialist配置到PhytoOracle环境变量的映射
    # 注意：PhytoOracle使用 VLM_{PROVIDER}_API_KEY 格式（PROVIDER全大写）
    env_key_mapping = {
        'qwen': 'VLM_QWEN_VL_API_KEY',      # PhytoOracle provider名: qwen_vl
        'gemini': 'VLM_GEMINI_API_KEY',     # PhytoOracle provider名: gemini
        'glm': 'VLM_GLM_4V_API_KEY',        # PhytoOracle provider名: glm_4v
        'grok': 'VLM_GROK_VISION_API_KEY'   # PhytoOracle provider名: grok_vision
    }

    # Provider名称映射（FlowerSpecialist名称 -> PhytoOracle名称）
    provider_name_mapping = {
        'qwen': 'qwen_vl',
        'gemini': 'gemini',
        'glm': 'glm_4v',
        'grok': 'grok_vision'
    }

    env_key = env_key_mapping.get(provider_name)
    if not env_key:
        print(f"[ERROR] Unknown provider: {provider_name}")
        return False

    # 设置API密钥到环境变量
    os.environ[env_key] = api_key
    print(f"[OK] Set environment variable: {env_key}")
    print(f"  API Key: {api_key[:20]}..." if len(api_key) > 20 else f"  API Key: {api_key}")

    # 获取实际的Provider名称（在PhytoOracle配置中的名称）
    actual_provider_name = provider_name_mapping.get(provider_name, provider_name)
    print(f"  Actual provider name: {actual_provider_name}")

    try:
        # 初始化客户端，只使用这一个提供商（不使用fallback）
        client = MultiProviderVLMClient(providers=[actual_provider_name])
        print(f"[OK] Client initialized with single provider: {actual_provider_name}")

        # 调用VLM
        print(f"[CALL] Calling {provider_name} API...")
        response = client.query_structured(
            prompt="Identify the genus of this flower: Rosa, Prunus, Tulipa, Dianthus, Paeonia, or unknown",
            response_model=Q02Response,
            image_bytes=test_image
        )

        # 验证响应
        if isinstance(response, Q02Response):
            print(f"[PASS] Test passed!")
            print(f"   Response type: {type(response).__name__}")
            print(f"   Result: genus={response.genus}")
            return True
        else:
            print(f"[WARN] Wrong response type: {type(response)}")
            return False

    except Exception as e:
        print(f"[FAIL] Test failed")
        print(f"   Error type: {type(e).__name__}")
        error_msg = str(e)
        if len(error_msg) > 500:
            print(f"   Error message (first 500 chars): {error_msg[:500]}...")
        else:
            print(f"   Error message: {error_msg}")
        return False
    finally:
        # 清理环境变量
        if env_key in os.environ:
            del os.environ[env_key]


def main():
    """主测试流程"""
    print("="*60)
    print("VLM Provider API Key Validation")
    print("="*60)

    # 加载API密钥
    try:
        api_keys = load_api_keys_from_flower_specialist()
        print(f"\n[OK] Successfully loaded config from FlowerSpecialist project")
        print(f"  Found {len(api_keys)} API keys")
    except Exception as e:
        print(f"\n[ERROR] Failed to load config: {e}")
        return

    # 测试每个提供商
    results = {}
    for provider, api_key in api_keys.items():
        if api_key:
            results[provider] = test_provider(provider, api_key)
        else:
            print(f"\n[WARN] {provider}: API key is empty, skipping test")
            results[provider] = False

    # 总结
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    working_providers = [name for name, status in results.items() if status]
    failed_providers = [name for name, status in results.items() if not status]

    if working_providers:
        print(f"\n[SUCCESS] Working providers ({len(working_providers)}):")
        for provider in working_providers:
            print(f"   - {provider}")

    if failed_providers:
        print(f"\n[FAILED] Non-working providers ({len(failed_providers)}):")
        for provider in failed_providers:
            print(f"   - {provider}")

    print(f"\nPass rate: {len(working_providers)}/{len(results)} ({len(working_providers)/len(results)*100:.1f}%)")
    print("="*60)


if __name__ == "__main__":
    main()
