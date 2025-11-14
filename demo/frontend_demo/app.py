"""
PhytoOracle Frontend Demo - 主入口

阶段1：核心推理展示（P0功能）
"""
import streamlit as st
from config import PAGE_TITLE, PAGE_ICON, LAYOUT


def main():
    """主入口函数"""
    # 页面配置
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=LAYOUT,
        initial_sidebar_state="expanded"
    )

    # 初始化Session State
    init_session_state()

    # 首页内容
    st.title(f"{PAGE_ICON} PhytoOracle 推理调试中心")

    st.markdown("""
    ## 欢迎使用 PhytoOracle MVP Demo

    这是一个**推理引擎验证工具**，专为验证三层渐进式诊断算法和支持知识库快速迭代而设计。

    ### 核心功能

    - **完整推理链路可视化**: Q0序列 → Q1-Q6特征提取 → 候选疾病筛选 → 模糊匹配 + 加权评分 → 最终诊断
    - **本体追溯**: 明确显示每个推理步骤使用的本体定义和知识文件
    - **同义词映射详情**: 模糊匹配时展示同义词来源和映射过程
    - **人工标注**: 对诊断结果进行准确性标注和备注
    - **本体使用导出**: 导出完整的本体使用JSON，便于使用Claude进行代码级调整

    ### 快速开始

    请在左侧导航栏选择"推理调试中心"开始使用。

    ### 测试说明

    - **支持的图片格式**: JPG, JPEG, PNG, BMP
    - **文件命名规则**: 文件名应包含疾病信息（如 `rose_black_spot_001.jpg`）
    - **假数据推理**: 系统会根据文件名解析疾病类型，生成对应的推理结果

    ### 支持的疾病

    | 疾病ID | 疾病名称 | 花属 | 版本 |
    |--------|---------|------|------|
    | rose_black_spot | 玫瑰黑斑病 | Rosa | v4.2 |
    | rose_powdery_mildew | 玫瑰白粉病 | Rosa | v3.1 |
    | cherry_brown_rot | 樱花褐腐病 | Prunus | v2.0 |

    ---

    **提示**: 这是阶段1 MVP demo，使用假数据推理引擎。后续将集成真实后端API。
    """)

    # 侧边栏说明
    with st.sidebar:
        st.markdown("## 📌 导航")
        st.info("请点击上方页面链接进入推理调试中心")

        st.markdown("---")
        st.markdown("### 📖 使用帮助")
        st.markdown("""
        1. 上传图片（支持拖拽）
        2. 查看完整推理过程
        3. 进行人工标注
        4. 导出本体使用数据
        """)

        st.markdown("---")
        st.markdown("### ℹ️ 版本信息")
        st.markdown("**版本**: v1.0 - 阶段1")
        st.markdown("**更新时间**: 2025-11-13")


def init_session_state():
    """初始化Session State"""
    # 当前推理结果
    if "current_diagnosis" not in st.session_state:
        st.session_state.current_diagnosis = None

    # 当前标注数据
    if "current_annotation" not in st.session_state:
        st.session_state.current_annotation = None

    # 图片信息
    if "current_image_name" not in st.session_state:
        st.session_state.current_image_name = None

    # 是否显示推理结果
    if "show_diagnosis" not in st.session_state:
        st.session_state.show_diagnosis = False


if __name__ == "__main__":
    main()
