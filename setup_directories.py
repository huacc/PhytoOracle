#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0.2 目录结构初始化脚本
功能：根据详细设计文档第4章，创建完整的项目目录结构和 __init__.py 文件
"""

import sys
import os
from pathlib import Path
from typing import List

# 设置控制台编码为 UTF-8
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

# 获取项目根目录（使用相对路径）
PROJECT_ROOT = Path(__file__).resolve().parent


def create_directories_and_init_files():
    """创建所有目录和 __init__.py 文件"""

    # 定义 backend 目录结构
    backend_dirs = [
        # apps 目录
        "backend/apps",
        "backend/apps/api",
        "backend/apps/api/routers",
        "backend/apps/api/schemas",
        "backend/apps/api/middleware",
        "backend/apps/admin",
        "backend/apps/admin/pages",
        "backend/apps/admin/utils",

        # core 目录
        "backend/core",

        # domain 目录
        "backend/domain",

        # infrastructure 目录
        "backend/infrastructure",
        "backend/infrastructure/llm",
        "backend/infrastructure/llm/providers",
        "backend/infrastructure/llm/prompts",
        "backend/infrastructure/llm/prompts/versions",
        "backend/infrastructure/llm/prompts/versions/v1.0",
        "backend/infrastructure/ontology",
        "backend/infrastructure/persistence",
        "backend/infrastructure/persistence/repositories",
        "backend/infrastructure/storage",

        # services 目录
        "backend/services",

        # tests 目录
        "backend/tests",
        "backend/tests/unit",
        "backend/tests/integration",
        "backend/tests/e2e",
        "backend/tests/fixtures",

        # knowledge_base 目录
        "backend/knowledge_base",
        "backend/knowledge_base/diseases",
        "backend/knowledge_base/features",
        "backend/knowledge_base/plants",
        "backend/knowledge_base/host_disease",
        "backend/knowledge_base/treatments",

        # storage 目录
        "backend/storage",
        "backend/storage/images",
        "backend/storage/images/unlabeled",
        "backend/storage/images/unlabeled/rosa",
        "backend/storage/images/unlabeled/prunus",
        "backend/storage/images/unlabeled/tulipa",
        "backend/storage/images/unlabeled/dianthus",
        "backend/storage/images/unlabeled/paeonia",
        "backend/storage/images/correct",
        "backend/storage/images/incorrect",
        "backend/storage/metadata",

        # scripts 目录
        "backend/scripts",
    ]

    # 定义 frontend 目录结构
    frontend_dirs = [
        "frontend/app",
        "frontend/app/diagnose",
        "frontend/app/history",
        "frontend/app/login",
        "frontend/app/api",
        "frontend/components",
        "frontend/components/ui",
        "frontend/lib",
        "frontend/public",
    ]

    # 定义 docs 目录结构（部分已存在，需要确保reports目录存在）
    docs_dirs = [
        "docs/reports",
        "docs/api",
        "docs/deployment",
        "docs/acceptance",
    ]

    # 合并所有目录
    all_dirs = backend_dirs + frontend_dirs + docs_dirs

    created_dirs = []
    created_init_files = []

    print("=" * 60)
    print("P0.2 目录结构初始化")
    print("=" * 60)
    print()

    # 创建所有目录
    for dir_path in all_dirs:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            print(f"[NEW] 创建目录: {dir_path}")
        else:
            print(f"[OK]  目录已存在: {dir_path}")

    print()
    print("-" * 60)
    print("创建 Python 包 __init__.py 文件")
    print("-" * 60)
    print()

    # 为所有 backend Python 目录创建 __init__.py
    python_package_dirs = [
        "backend/apps",
        "backend/apps/api",
        "backend/apps/api/routers",
        "backend/apps/api/schemas",
        "backend/apps/api/middleware",
        "backend/apps/admin",
        "backend/apps/admin/pages",
        "backend/apps/admin/utils",
        "backend/core",
        "backend/domain",
        "backend/infrastructure",
        "backend/infrastructure/llm",
        "backend/infrastructure/llm/providers",
        "backend/infrastructure/llm/prompts",
        "backend/infrastructure/ontology",
        "backend/infrastructure/persistence",
        "backend/infrastructure/persistence/repositories",
        "backend/infrastructure/storage",
        "backend/services",
        "backend/tests",
        "backend/tests/unit",
        "backend/tests/integration",
        "backend/tests/e2e",
    ]

    for pkg_dir in python_package_dirs:
        init_file = PROJECT_ROOT / pkg_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text(f'"""{pkg_dir.split("/")[-1]} 模块"""\n', encoding="utf-8")
            created_init_files.append(f"{pkg_dir}/__init__.py")
            print(f"[NEW] 创建: {pkg_dir}/__init__.py")
        else:
            print(f"[OK]  已存在: {pkg_dir}/__init__.py")

    print()
    print("=" * 60)
    print("目录结构创建完成")
    print("=" * 60)
    print(f"新创建目录数: {len(created_dirs)}")
    print(f"新创建 __init__.py 文件数: {len(created_init_files)}")
    print()

    return {
        "created_dirs": created_dirs,
        "created_init_files": created_init_files,
        "total_dirs": len(all_dirs),
        "total_init_files": len(python_package_dirs)
    }


if __name__ == "__main__":
    result = create_directories_and_init_files()
    print(f"[SUCCESS] 目录结构初始化完成！")
    print(f"   总目录数: {result['total_dirs']}")
    print(f"   总 __init__.py 文件数: {result['total_init_files']}")
