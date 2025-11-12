-- ==================== PhytoOracle 数据库初始化脚本 ====================
-- 项目: PhytoOracle - 花卉疾病诊断系统
-- 版本: v1.0
-- 创建日期: 2025-11-12
-- 数据库: PostgreSQL 17
-- 编码: UTF-8
--
-- 说明:
--   本脚本创建PhytoOracle系统的核心数据表，包括：
--   1. diagnoses - 诊断记录表（存储每次诊断的完整信息）
--   2. images - 图片元数据表（存储图片文件信息和准确率标签）
--   3. api_keys - API密钥表（存储用户认证密钥）
--   4. admin_users - 管理员账号表（存储管理后台登录账号）
--   5. knowledge_versions - 知识库版本表（存储知识库加载历史）
--
-- 使用方法:
--   psql -h <host> -U <username> -d <database> -f init_db.sql
--
-- 注意事项:
--   - 执行前请确保数据库已创建
--   - 如果表已存在，请先备份数据后再删除重建
--   - 生产环境请修改seed_data.sql中的默认密码
-- ========================================================================

-- ==================== 1. 诊断记录表 ====================

-- 功能说明：
--   存储每次诊断的完整信息，包括特征向量、诊断结果、评分详情等
--
-- 关键字段：
--   - feature_vector: JSONB类型，存储Q0-Q6问诊序列的所有回答
--   - diagnosis_result: JSONB类型，存储诊断状态和疾病信息
--   - scores: JSONB类型，存储候选疾病的评分明细
--   - reasoning: JSONB类型，存储推理过程和VLM原始回答
--
-- 数据保留周期：1年（可通过定时任务清理历史数据）

CREATE TABLE IF NOT EXISTS diagnoses (
    -- 主键：诊断唯一标识符（UUID自动生成）
    diagnosis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 诊断时间戳（带时区，默认当前时间）
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 图片存储路径（相对路径，如：backend/storage/images/unlabeled/diag_20250111_001.jpg）
    image_path TEXT NOT NULL,

    -- 特征向量（JSONB存储，包含Q0-Q6所有问题的回答）
    -- 示例结构：
    -- {
    --   "content_type": "plant",
    --   "plant_category": "flower",
    --   "flower_genus": "Rosa",
    --   "organ": "leaf",
    --   "completeness": "intact",
    --   "has_abnormality": "yes",
    --   "symptom_type": "spot",
    --   "colors": ["black", "brown"],
    --   "location": "leaf_surface",
    --   "size": "medium",
    --   "distribution": "scattered"
    -- }
    feature_vector JSONB NOT NULL,

    -- 诊断结果（JSONB存储，包含status/confirmed_disease/suspected_diseases）
    -- 示例结构：
    -- {
    --   "status": "confirmed",
    --   "confirmed_disease": {
    --     "disease_id": "rose_black_spot",
    --     "disease_name": "玫瑰黑斑病",
    --     "confidence": 0.92
    --   }
    -- }
    diagnosis_result JSONB NOT NULL,

    -- 评分详情（JSONB存储，包含每个候选疾病的得分明细）
    -- 示例结构：
    -- {
    --   "total_score": 92.5,
    --   "major_features": {"spot_color": 30, "spot_shape": 25},
    --   "minor_features": {"leaf_yellowing": 15},
    --   "optional_features": {"stem_affected": 5}
    -- }
    scores JSONB,

    -- 推理过程（JSONB存储，包含诊断推理步骤）
    -- 示例结构：
    -- {
    --   "steps": [
    --     "检测到叶片表面黑色斑点（主要特征匹配）",
    --     "斑点呈圆形，边缘清晰（形态匹配）"
    --   ],
    --   "vlm_responses": {
    --     "Q1": "症状类型为斑点",
    --     "Q2": "颜色为黑色和棕色"
    --   }
    -- }
    reasoning JSONB,

    -- VLM提供商（记录使用的模型，如：qwen_vl, gemini, doubao）
    vlm_provider VARCHAR(50) NOT NULL,

    -- 执行时间（毫秒，用于性能监控）
    execution_time_ms INTEGER,

    -- 约束：诊断结果必须包含status字段，且值在枚举范围内
    CONSTRAINT valid_diagnosis_result CHECK (
        diagnosis_result ? 'status' AND
        diagnosis_result->>'status' IN ('confirmed', 'suspected', 'unlikely')
    )
);

-- 注释说明
COMMENT ON TABLE diagnoses IS '诊断记录表：存储每次诊断的完整信息';
COMMENT ON COLUMN diagnoses.diagnosis_id IS '诊断唯一标识符（UUID）';
COMMENT ON COLUMN diagnoses.timestamp IS '诊断时间戳（带时区）';
COMMENT ON COLUMN diagnoses.image_path IS '图片存储路径（相对路径）';
COMMENT ON COLUMN diagnoses.feature_vector IS '特征向量（Q0-Q6问诊结果，JSONB格式）';
COMMENT ON COLUMN diagnoses.diagnosis_result IS '诊断结果（包含status、confirmed_disease、suspected_diseases）';
COMMENT ON COLUMN diagnoses.scores IS '评分详情（候选疾病得分明细）';
COMMENT ON COLUMN diagnoses.reasoning IS '推理过程（诊断逻辑和VLM回答）';
COMMENT ON COLUMN diagnoses.vlm_provider IS 'VLM提供商（qwen_vl/gemini/doubao等）';
COMMENT ON COLUMN diagnoses.execution_time_ms IS '执行耗时（毫秒）';

-- 索引设计：优化查询性能，避免全表扫描

-- 索引1：按时间倒序查询（诊断历史查询的主要场景）
CREATE INDEX idx_diagnoses_timestamp ON diagnoses(timestamp DESC);

-- 索引2：按VLM提供商查询（用于性能分析和成本统计）
CREATE INDEX idx_diagnoses_vlm_provider ON diagnoses(vlm_provider);

-- 索引3：按诊断状态查询（筛选确诊/疑似/未知记录）
-- 使用函数索引提取JSONB字段
CREATE INDEX idx_diagnoses_result_status ON diagnoses((diagnosis_result->>'status'));

-- 索引4：按花卉种属查询（筛选特定花卉的诊断记录）
-- 使用函数索引提取JSONB字段
CREATE INDEX idx_diagnoses_feature_vector_genus ON diagnoses((feature_vector->>'flower_genus'));

-- 索引5：组合索引（时间+种属，优化历史查询性能）
CREATE INDEX idx_diagnoses_timestamp_genus ON diagnoses(timestamp DESC, (feature_vector->>'flower_genus'));


-- ==================== 2. 图片元数据表 ====================

-- 功能说明：
--   存储图片文件信息和准确率标签，用于：
--   1. 图片文件管理（上传时间、存储路径）
--   2. 人工标注（正确/错误标签，用于模型优化）
--   3. 数据追溯（关联诊断记录）
--
-- 关键字段：
--   - accuracy_label: 准确率标签（unlabeled/correct/incorrect）
--   - notes: 人工标注备注
--
-- 数据保留周期：
--   - unlabeled: 1年
--   - correct/incorrect: 永久保留（用于模型训练和评估）

CREATE TABLE IF NOT EXISTS images (
    -- 主键：图片唯一标识符（UUID自动生成）
    image_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 外键：关联诊断记录（级联删除：删除诊断记录时同时删除图片元数据）
    diagnosis_id UUID REFERENCES diagnoses(diagnosis_id) ON DELETE CASCADE,

    -- 文件存储路径（相对路径，唯一约束，如：backend/storage/images/unlabeled/img_001.jpg）
    file_path TEXT NOT NULL UNIQUE,

    -- 上传时间（带时区，默认当前时间）
    upload_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 植物种属（从诊断结果中提取，如：Rosa, Prunus）
    plant_genus VARCHAR(100),

    -- 器官类型（leaf/flower/unknown）
    organ VARCHAR(20),

    -- 准确率标签（用于人工标注和质量评估）
    -- - unlabeled: 未标注（默认值）
    -- - correct: 诊断正确
    -- - incorrect: 诊断错误
    accuracy_label VARCHAR(20) DEFAULT 'unlabeled',

    -- 备注（人工标注时填写，如：误判原因、图片质量问题等）
    notes TEXT,

    -- 约束：器官类型枚举
    CONSTRAINT valid_organ CHECK (organ IN ('leaf', 'flower', 'unknown')),

    -- 约束：准确率标签枚举
    CONSTRAINT valid_accuracy_label CHECK (
        accuracy_label IN ('unlabeled', 'correct', 'incorrect')
    )
);

-- 注释说明
COMMENT ON TABLE images IS '图片元数据表：存储图片文件信息和准确率标签';
COMMENT ON COLUMN images.image_id IS '图片唯一标识符（UUID）';
COMMENT ON COLUMN images.diagnosis_id IS '关联诊断记录ID（外键）';
COMMENT ON COLUMN images.file_path IS '文件存储路径（相对路径，唯一）';
COMMENT ON COLUMN images.upload_time IS '上传时间（带时区）';
COMMENT ON COLUMN images.plant_genus IS '植物种属（从诊断结果提取）';
COMMENT ON COLUMN images.organ IS '器官类型（leaf/flower/unknown）';
COMMENT ON COLUMN images.accuracy_label IS '准确率标签（unlabeled/correct/incorrect）';
COMMENT ON COLUMN images.notes IS '备注（人工标注说明）';

-- 索引设计

-- 索引1：按诊断ID查询（外键索引，关联查询优化）
CREATE INDEX idx_images_diagnosis_id ON images(diagnosis_id);

-- 索引2：按上传时间倒序查询（最近上传的图片）
CREATE INDEX idx_images_upload_time ON images(upload_time DESC);

-- 索引3：按植物种属查询（筛选特定花卉的图片）
CREATE INDEX idx_images_plant_genus ON images(plant_genus);

-- 索引4：按准确率标签查询（筛选待标注/正确/错误的图片）
CREATE INDEX idx_images_accuracy_label ON images(accuracy_label);

-- 索引5：组合索引（准确率标签+种属，优化标注数据筛选）
CREATE INDEX idx_images_label_genus ON images(accuracy_label, plant_genus);


-- ==================== 3. API密钥表 ====================

-- 功能说明：
--   存储API密钥，用于：
--   1. 认证授权（API Key认证）
--   2. 访问控制（激活/禁用密钥）
--   3. 密钥管理（创建时间、过期时间、最后使用时间）
--
-- 安全注意事项：
--   - 密钥使用SHA256哈希存储，原始密钥只在生成时显示一次
--   - 生产环境必须启用HTTPS，防止密钥在传输中泄露
--   - 定期轮换密钥，过期密钥自动禁用
--
-- MVP阶段状态：暂不启用（预留表结构）

CREATE TABLE IF NOT EXISTS api_keys (
    -- 主键：密钥唯一标识符（UUID自动生成）
    key_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- API Key哈希值（SHA256哈希存储，原始密钥只在生成时显示一次）
    -- 存储格式：64位十六进制字符串
    api_key_hash VARCHAR(64) NOT NULL UNIQUE,

    -- 创建时间（带时区，默认当前时间）
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 过期时间（带时区，NULL表示永不过期）
    expires_at TIMESTAMPTZ,

    -- 是否激活（用于密钥管理，禁用后无法使用）
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- 描述（用于标识密钥用途，如：Development API Key, Production Key等）
    description TEXT,

    -- 最后使用时间（每次API调用时更新，用于监控密钥活跃度）
    last_used_at TIMESTAMPTZ
);

-- 注释说明
COMMENT ON TABLE api_keys IS 'API密钥表：存储用户认证密钥（MVP阶段暂不启用）';
COMMENT ON COLUMN api_keys.key_id IS '密钥唯一标识符（UUID）';
COMMENT ON COLUMN api_keys.api_key_hash IS 'API Key哈希值（SHA256，64位十六进制）';
COMMENT ON COLUMN api_keys.created_at IS '创建时间（带时区）';
COMMENT ON COLUMN api_keys.expires_at IS '过期时间（NULL=永不过期）';
COMMENT ON COLUMN api_keys.is_active IS '是否激活（禁用后无法使用）';
COMMENT ON COLUMN api_keys.description IS '描述（标识密钥用途）';
COMMENT ON COLUMN api_keys.last_used_at IS '最后使用时间（用于监控活跃度）';

-- 索引设计

-- 索引1：按哈希值查询（认证时的主要查询，仅索引激活的密钥）
-- 使用部分索引优化查询性能
CREATE INDEX idx_api_keys_hash ON api_keys(api_key_hash) WHERE is_active = TRUE;

-- 索引2：按过期时间查询（用于定时任务清理过期密钥）
-- 使用部分索引，仅索引有过期时间的密钥
CREATE INDEX idx_api_keys_expires_at ON api_keys(expires_at) WHERE expires_at IS NOT NULL;


-- ==================== 4. 管理员账号表 ====================

-- 功能说明：
--   存储管理后台登录账号，用于：
--   1. 管理员登录认证（用户名+密码）
--   2. 账号管理（激活/禁用账号）
--   3. 登录审计（最后登录时间）
--
-- 安全注意事项：
--   - 密码使用bcrypt哈希存储（成本因子12）
--   - 生产环境必须修改默认密码
--   - 实施密码复杂度策略（最小长度、特殊字符等）
--   - 实施登录失败锁定策略（防止暴力破解）
--
-- 默认管理员账号：
--   - 用户名：admin
--   - 密码：admin123（见seed_data.sql，生产环境必须修改）

CREATE TABLE IF NOT EXISTS admin_users (
    -- 主键：用户唯一标识符（UUID自动生成）
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 用户名（唯一约束，长度限制：3-50字符）
    username VARCHAR(50) NOT NULL UNIQUE,

    -- 密码哈希值（bcrypt哈希存储，格式：$2b$12$...）
    -- bcrypt哈希长度固定为60字符，预留255字符空间
    password_hash VARCHAR(255) NOT NULL,

    -- 创建时间（带时区，默认当前时间）
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 最后登录时间（带时区，每次登录成功后更新）
    last_login_at TIMESTAMPTZ,

    -- 是否激活（用于账号管理，禁用后无法登录）
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- 约束：用户名长度限制（3-50字符）
    CONSTRAINT valid_username_length CHECK (LENGTH(username) >= 3 AND LENGTH(username) <= 50)
);

-- 注释说明
COMMENT ON TABLE admin_users IS '管理员账号表：存储管理后台登录账号';
COMMENT ON COLUMN admin_users.user_id IS '用户唯一标识符（UUID）';
COMMENT ON COLUMN admin_users.username IS '用户名（唯一，3-50字符）';
COMMENT ON COLUMN admin_users.password_hash IS '密码哈希值（bcrypt，60字符）';
COMMENT ON COLUMN admin_users.created_at IS '创建时间（带时区）';
COMMENT ON COLUMN admin_users.last_login_at IS '最后登录时间（带时区）';
COMMENT ON COLUMN admin_users.is_active IS '是否激活（禁用后无法登录）';

-- 索引设计

-- 索引1：按用户名查询（登录认证的主要查询，唯一索引已自动创建）
-- 无需额外创建索引（UNIQUE约束已自动创建唯一索引）

-- 索引2：按激活状态查询（用于管理后台列表展示）
CREATE INDEX idx_admin_users_is_active ON admin_users(is_active);


-- ==================== 5. 知识库版本表 ====================

-- 功能说明：
--   存储知识库加载历史，用于：
--   1. 版本管理（记录每次知识库加载的版本信息）
--   2. 版本回滚（出现问题时回滚到上一稳定版本）
--   3. 完整性验证（通过疾病数量快速验证知识库是否完整）
--   4. 审计追踪（记录知识库变更历史）
--
-- 版本号规则：
--   - 开发阶段：使用Git Commit Hash（40位）
--   - 生产阶段：使用语义化版本号（v1.0.0, v1.1.0等）
--
-- 当前版本标识：
--   - is_current字段标识当前激活的版本
--   - 同一时刻只能有一个版本为当前版本（唯一索引保证）

CREATE TABLE IF NOT EXISTS knowledge_versions (
    -- 主键：版本唯一标识符（UUID自动生成）
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 版本标识（Git Commit Hash或语义化版本号）
    -- 开发阶段：40位Git Commit Hash（如：a1b2c3d4e5f6...）
    -- 生产阶段：语义化版本号（如：v1.0.0）
    commit_hash VARCHAR(40) NOT NULL,

    -- 加载时间（带时区，默认当前时间）
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 疾病数量（用于快速验证知识库完整性）
    -- 当前版本预期值：18-24种疾病（5种花卉 × 3-6种疾病）
    disease_count INTEGER NOT NULL,

    -- 版本描述（记录本次更新的内容，如：新增樱花锈病，修复玫瑰黑斑病特征）
    description TEXT,

    -- 是否为当前激活版本（同一时刻只能有一个版本为TRUE）
    is_current BOOLEAN NOT NULL DEFAULT FALSE,

    -- 约束：疾病数量必须为正数
    CONSTRAINT valid_disease_count CHECK (disease_count > 0)
);

-- 注释说明
COMMENT ON TABLE knowledge_versions IS '知识库版本表：存储知识库加载历史和版本管理';
COMMENT ON COLUMN knowledge_versions.version_id IS '版本唯一标识符（UUID）';
COMMENT ON COLUMN knowledge_versions.commit_hash IS '版本标识（Git Commit Hash或语义化版本号）';
COMMENT ON COLUMN knowledge_versions.loaded_at IS '加载时间（带时区）';
COMMENT ON COLUMN knowledge_versions.disease_count IS '疾病数量（用于完整性验证）';
COMMENT ON COLUMN knowledge_versions.description IS '版本描述（记录更新内容）';
COMMENT ON COLUMN knowledge_versions.is_current IS '是否为当前激活版本';

-- 索引设计

-- 索引1：按加载时间倒序查询（版本历史列表展示）
CREATE INDEX idx_knowledge_versions_loaded_at ON knowledge_versions(loaded_at DESC);

-- 索引2：当前版本唯一索引（确保同一时刻只有一个版本为当前版本）
-- 使用部分唯一索引，仅对is_current=TRUE的记录生效
CREATE UNIQUE INDEX idx_knowledge_versions_current ON knowledge_versions(is_current) WHERE is_current = TRUE;


-- ==================== 数据库初始化完成 ====================

-- 输出成功信息
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'PhytoOracle 数据库初始化完成！';
    RAISE NOTICE '========================================';
    RAISE NOTICE '创建的表：';
    RAISE NOTICE '  1. diagnoses - 诊断记录表';
    RAISE NOTICE '  2. images - 图片元数据表';
    RAISE NOTICE '  3. api_keys - API密钥表';
    RAISE NOTICE '  4. admin_users - 管理员账号表';
    RAISE NOTICE '  5. knowledge_versions - 知识库版本表';
    RAISE NOTICE '';
    RAISE NOTICE '下一步：';
    RAISE NOTICE '  1. 执行 seed_data.sql 插入初始化数据';
    RAISE NOTICE '  2. 使用 \dt 命令查看所有表';
    RAISE NOTICE '  3. 使用 \di 命令查看所有索引';
    RAISE NOTICE '';
    RAISE NOTICE '注意事项：';
    RAISE NOTICE '  - 生产环境必须修改默认管理员密码';
    RAISE NOTICE '  - 定期备份数据库';
    RAISE NOTICE '  - 监控索引使用情况，优化查询性能';
    RAISE NOTICE '========================================';
END $$;
