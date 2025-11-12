# PhytoOracle 快速开始指南

## 环境准备

### 1️⃣ 激活虚拟环境

**Windows PowerShell / CMD:**
```powershell
cd D:\项目管理\PhytoOracle
venv\Scripts\activate
```

**Git Bash:**
```bash
cd /d/项目管理/PhytoOracle
source venv/Scripts/activate
```

激活后，命令提示符前会显示 `(venv)`。

---

### 2️⃣ 验证环境

```bash
# 检查 Python 版本
python --version
# 输出: Python 3.12.3

# 检查已安装的包
pip list | grep fastapi
# 输出: fastapi 0.121.1

# 验证 FastAPI 应用
cd backend
python -c "from apps.api.main import app; print('FastAPI OK')"
# 输出: FastAPI app imported successfully

# 验证配置加载
python -c "from core.config import settings; print('Config OK')"
# 输出: Config loaded successfully
```

---

## 启动服务

### 🚀 启动 FastAPI 后端 API

```bash
# 确保虚拟环境已激活
cd D:\项目管理\PhytoOracle\backend
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```

**访问地址:**
- API 主页: http://localhost:8000
- Swagger UI 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc

**健康检查:**
```bash
curl http://localhost:8000/health
# 输出: {"status":"ok"}
```

---

### 🎨 启动 Streamlit 管理后台

```bash
# 确保虚拟环境已激活
cd D:\项目管理\PhytoOracle\backend
streamlit run apps/admin/app.py
```

**访问地址:**
- 管理后台: http://localhost:8501

---

### 🌐 启动 Next.js 前端（需要先安装依赖）

```bash
cd D:\项目管理\PhytoOracle\frontend

# 首次运行需要安装依赖
npm install

# 启动开发服务器
npm run dev
```

**访问地址:**
- 前端应用: http://localhost:3000

---

## 常用开发命令

### 运行技术栈验证脚本
```bash
cd D:\项目管理\PhytoOracle
python test_tech_stack.py
```

### 查看项目结构
```bash
tree /F backend  # Windows
tree backend     # Git Bash
```

### 查看已安装的 Python 包
```bash
pip list
```

### 安装新的 Python 包
```bash
pip install <包名>
```

### 生成依赖列表（可选）
```bash
pip freeze > requirements.txt
```

---

## 配置文件

### 环境变量 (.env)
复制模板文件并编辑：
```bash
cd D:\项目管理\PhytoOracle\backend
cp .env.example .env
# 编辑 .env 文件，配置数据库密码等
```

### VLM 配置 (llm_config.json)
**⚠️ 重要**: 真实的 API Key 已在 `backend/config/llm_config.json`，不会上传到 GitHub。

查看配置说明：
```bash
cat backend/config/README.md
```

---

## 项目状态

### ✅ P0 阶段完成项
- [x] 开发环境验证（Python 3.12.3, PostgreSQL, Redis, Node.js）
- [x] 完整目录蓝图（57个目录，23个 __init__.py）
- [x] 技术栈验证（FastAPI, Streamlit, Next.js）
- [x] 虚拟环境配置（核心依赖已安装）
- [x] VLM 配置文件集成
- [x] .gitignore 配置（保护 API Key）

### 📋 下一步: P1 阶段
- [ ] P1.1: API 接口设计（OpenAPI 规范）
- [ ] P1.2: 数据库表设计（DDL 脚本）
- [ ] P1.3: 数据模型设计（Pydantic 模型）

---

## 故障排查

### 问题: 虚拟环境激活失败
**解决**: 参考 `venv/README.md` 中的故障排查章节

### 问题: FastAPI 启动失败
**检查**:
1. 虚拟环境是否已激活（命令提示符前有 `(venv)`）
2. 是否在 `backend/` 目录下运行命令
3. 配置文件是否存在（`.env`, `core/config.py`）

### 问题: 无法连接数据库
**检查**:
1. PostgreSQL 服务是否运行（192.168.0.119:5432）
2. Redis 服务是否运行（192.168.0.119:6379）
3. `.env` 文件中的数据库密码是否正确

---

## 文档索引

- **P0 阶段执行报告**: `docs/reports/P0_执行报告_20251112_094109.md`
- **研发计划**: `docs/plan/研发计划v1.0.md`
- **详细设计文档**: `docs/design/详细设计文档.md`
- **虚拟环境说明**: `venv/README.md`
- **VLM 配置说明**: `backend/config/README.md`

---

**最后更新**: 2025-11-12
**项目状态**: P0 阶段完成 ✅
