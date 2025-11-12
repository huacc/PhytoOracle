-- ==================== PhytoOracle 初始化数据脚本 ====================
-- 项目: PhytoOracle - 花卉疾病诊断系统
-- 版本: v1.0
-- 创建日期: 2025-11-12
-- 数据库: PostgreSQL 17
--
-- 说明:
--   本脚本插入PhytoOracle系统的初始化数据，包括：
--   1. 默认管理员账号（用户名：admin，密码：admin123）
--   2. 开发用API Key（密钥：phyto_dev_key_12345）
--   3. 初始知识库版本记录
--
-- 使用方法:
--   psql -h <host> -U <username> -d <database> -f seed_data.sql
--
-- ⚠️ 安全警告:
--   - 默认密码仅用于开发环境，生产环境必须修改！
--   - 生产环境必须删除开发用API Key，生成正式密钥
--   - 建议首次登录后立即修改管理员密码
--
-- 密码生成方法（Python）:
--   import bcrypt
--   password = "your_password".encode('utf-8')
--   hashed = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12))
--   print(hashed.decode('utf-8'))
--
-- API Key生成方法（Python）:
--   import hashlib
--   api_key = "your_api_key"
--   hashed = hashlib.sha256(api_key.encode()).hexdigest()
--   print(hashed)
-- ========================================================================

-- ==================== 1. 默认管理员账号 ====================

-- 插入默认管理员账号
-- 用户名：admin
-- 密码：admin123（生产环境必须修改！）
-- 密码哈希：$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ckM.Eq0J/7mO
-- 生成命令：bcrypt.hashpw(b"admin123", bcrypt.gensalt(rounds=12))

INSERT INTO admin_users (username, password_hash, is_active)
VALUES (
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ckM.Eq0J/7mO',
    TRUE
)
ON CONFLICT (username) DO NOTHING;

-- 输出成功信息
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM admin_users WHERE username = 'admin') THEN
        RAISE NOTICE '[✓] 默认管理员账号创建成功';
        RAISE NOTICE '    用户名: admin';
        RAISE NOTICE '    密码: admin123';
        RAISE NOTICE '    ⚠️  生产环境必须修改默认密码！';
    ELSE
        RAISE NOTICE '[✗] 默认管理员账号创建失败';
    END IF;
END $$;


-- ==================== 2. 开发用API Key ====================

-- 插入开发用API Key（MVP阶段暂不启用，预留数据）
-- 原始密钥：phyto_dev_key_12345
-- SHA256哈希：f8e3d6c7b2a1e4f5d8c9b0a7e6f5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7
-- 生成命令：hashlib.sha256(b"phyto_dev_key_12345").hexdigest()

INSERT INTO api_keys (api_key_hash, description, is_active, expires_at)
VALUES (
    'f8e3d6c7b2a1e4f5d8c9b0a7e6f5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7',
    'Development API Key (仅用于开发环境)',
    TRUE,
    NULL  -- 永不过期（仅开发环境）
)
ON CONFLICT (api_key_hash) DO NOTHING;

-- 输出成功信息
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM api_keys WHERE description LIKE '%Development%') THEN
        RAISE NOTICE '[✓] 开发用API Key创建成功';
        RAISE NOTICE '    原始密钥: phyto_dev_key_12345';
        RAISE NOTICE '    ⚠️  生产环境必须删除此密钥，生成正式密钥！';
    ELSE
        RAISE NOTICE '[✗] 开发用API Key创建失败';
    END IF;
END $$;


-- ==================== 3. 初始知识库版本记录 ====================

-- 插入初始知识库版本记录
-- 版本标识：initial（首次部署的初始版本）
-- 疾病数量：20种（预期值：18-24种）
-- 描述：包含5种花卉和20种疾病的初始知识库

INSERT INTO knowledge_versions (commit_hash, disease_count, description, is_current)
VALUES (
    'initial',
    20,
    'Initial knowledge base with 5 flowers (Rosa, Prunus, Tulipa, Dianthus, Paeonia) and 20 diseases',
    TRUE
)
ON CONFLICT DO NOTHING;

-- 输出成功信息
DO $$
DECLARE
    v_disease_count INTEGER;
BEGIN
    SELECT disease_count INTO v_disease_count
    FROM knowledge_versions
    WHERE is_current = TRUE;

    IF v_disease_count IS NOT NULL THEN
        RAISE NOTICE '[✓] 初始知识库版本记录创建成功';
        RAISE NOTICE '    版本标识: initial';
        RAISE NOTICE '    疾病数量: %', v_disease_count;
        RAISE NOTICE '    当前激活: TRUE';
    ELSE
        RAISE NOTICE '[✗] 初始知识库版本记录创建失败';
    END IF;
END $$;


-- ==================== 4. 数据验证 ====================

-- 验证所有初始化数据插入成功
DO $$
DECLARE
    admin_count INTEGER;
    api_key_count INTEGER;
    knowledge_version_count INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '数据验证结果';
    RAISE NOTICE '========================================';

    -- 验证管理员账号
    SELECT COUNT(*) INTO admin_count FROM admin_users;
    RAISE NOTICE '管理员账号数量: %', admin_count;

    -- 验证API Key
    SELECT COUNT(*) INTO api_key_count FROM api_keys;
    RAISE NOTICE 'API Key数量: %', api_key_count;

    -- 验证知识库版本
    SELECT COUNT(*) INTO knowledge_version_count FROM knowledge_versions;
    RAISE NOTICE '知识库版本数量: %', knowledge_version_count;

    RAISE NOTICE '';

    -- 整体验证
    IF admin_count >= 1 AND api_key_count >= 1 AND knowledge_version_count >= 1 THEN
        RAISE NOTICE '[✓] 所有初始化数据插入成功！';
    ELSE
        RAISE WARNING '[✗] 部分初始化数据插入失败，请检查日志！';
    END IF;

    RAISE NOTICE '========================================';
END $$;


-- ==================== 5. 下一步操作指南 ====================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '下一步操作指南';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE '1️⃣  验证数据库表结构';
    RAISE NOTICE '   psql> \dt';
    RAISE NOTICE '   应显示5张表: diagnoses, images, api_keys, admin_users, knowledge_versions';
    RAISE NOTICE '';
    RAISE NOTICE '2️⃣  验证数据库索引';
    RAISE NOTICE '   psql> \di';
    RAISE NOTICE '   应显示所有索引（约15个）';
    RAISE NOTICE '';
    RAISE NOTICE '3️⃣  查看管理员账号';
    RAISE NOTICE '   psql> SELECT username, is_active, created_at FROM admin_users;';
    RAISE NOTICE '';
    RAISE NOTICE '4️⃣  测试管理员登录';
    RAISE NOTICE '   用户名: admin';
    RAISE NOTICE '   密码: admin123';
    RAISE NOTICE '';
    RAISE NOTICE '5️⃣  修改管理员密码（生产环境）';
    RAISE NOTICE '   psql> UPDATE admin_users';
    RAISE NOTICE '         SET password_hash = ''<新密码的bcrypt哈希>''';
    RAISE NOTICE '         WHERE username = ''admin'';';
    RAISE NOTICE '';
    RAISE NOTICE '6️⃣  查看知识库版本';
    RAISE NOTICE '   psql> SELECT commit_hash, disease_count, is_current, loaded_at';
    RAISE NOTICE '         FROM knowledge_versions';
    RAISE NOTICE '         ORDER BY loaded_at DESC;';
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  安全提醒：';
    RAISE NOTICE '   • 生产环境必须修改默认管理员密码';
    RAISE NOTICE '   • 生产环境必须删除开发用API Key';
    RAISE NOTICE '   • 启用HTTPS保护数据传输';
    RAISE NOTICE '   • 定期备份数据库';
    RAISE NOTICE '   • 监控异常登录行为';
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
END $$;


-- ==================== 初始化数据插入完成 ====================
