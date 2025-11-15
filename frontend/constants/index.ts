/**
 * PhytoOracle 常量定义
 * 定义全局常量，避免硬编码
 */

import { FlowerGenus, PathogenType, DiagnosisStatus } from '@/types';

/**
 * API 相关常量
 */
export const API_CONFIG = {
  /** API 基础 URL */
  BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  /** API 版本 */
  VERSION: process.env.NEXT_PUBLIC_API_VERSION || 'v1',
  /** 请求超时时间（毫秒） */
  TIMEOUT: 60000,
  /** 重试次数 */
  RETRY_COUNT: 3,
  /** 重试延迟（毫秒） */
  RETRY_DELAY: 1000,
} as const;

/**
 * 存储相关常量
 */
export const STORAGE_KEYS = {
  /** 认证Token */
  AUTH_TOKEN: process.env.NEXT_PUBLIC_TOKEN_KEY || 'phyto_auth_token',
  /** 用户信息 */
  USER_INFO: 'phyto_user_info',
  /** 语言设置 */
  LANGUAGE: 'phyto_language',
  /** 主题设置 */
  THEME: 'phyto_theme',
} as const;

/**
 * 文件上传相关常量
 */
export const UPLOAD_CONFIG = {
  /** 最大文件大小（MB） */
  MAX_SIZE: Number(process.env.NEXT_PUBLIC_MAX_IMAGE_SIZE) || 10,
  /** 支持的图片格式 */
  ALLOWED_FORMATS: (process.env.NEXT_PUBLIC_ALLOWED_IMAGE_FORMATS || 'jpg,jpeg,png,heic,webp').split(','),
  /** 批量上传最大数量 */
  MAX_BATCH_COUNT: Number(process.env.NEXT_PUBLIC_MAX_BATCH_UPLOAD) || 50,
  /** 支持的MIME类型 */
  MIME_TYPES: {
    jpg: 'image/jpeg',
    jpeg: 'image/jpeg',
    png: 'image/png',
    heic: 'image/heic',
    webp: 'image/webp',
  } as const,
} as const;

/**
 * 花卉种属选项
 */
export const FLOWER_GENUS_OPTIONS = [
  { label: '玫瑰/月季 (Rosa)', value: 'Rosa' as FlowerGenus },
  { label: '樱花/李属 (Prunus)', value: 'Prunus' as FlowerGenus },
  { label: '郁金香 (Tulipa)', value: 'Tulipa' as FlowerGenus },
  { label: '康乃馨 (Dianthus)', value: 'Dianthus' as FlowerGenus },
  { label: '牡丹 (Paeonia)', value: 'Paeonia' as FlowerGenus },
] as const;

/**
 * 病原体类型选项
 */
export const PATHOGEN_TYPE_OPTIONS = [
  { label: '真菌性', value: 'fungal' as PathogenType },
  { label: '细菌性', value: 'bacterial' as PathogenType },
  { label: '病毒性', value: 'viral' as PathogenType },
  { label: '虫害', value: 'pest' as PathogenType },
  { label: '非生物性', value: 'abiotic' as PathogenType },
] as const;

/**
 * 诊断状态选项
 */
export const DIAGNOSIS_STATUS_OPTIONS = [
  { label: '确诊', value: 'confirmed' as DiagnosisStatus, color: '#52c41a' },
  { label: '疑似', value: 'suspected' as DiagnosisStatus, color: '#faad14' },
  { label: '未知', value: 'unlikely' as DiagnosisStatus, color: '#ff4d4f' },
] as const;

/**
 * 置信度阈值
 */
export const CONFIDENCE_THRESHOLDS = {
  /** 确诊阈值（≥0.85） */
  CONFIRMED: 0.85,
  /** 疑似阈值（≥0.60） */
  SUSPECTED: 0.60,
  /** 未知阈值（<0.60） */
  UNLIKELY: 0.60,
} as const;

/**
 * 分页默认配置
 */
export const PAGINATION_DEFAULTS = {
  /** 默认每页数量 */
  PAGE_SIZE: 20,
  /** 每页数量选项 */
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
  /** 最大每页数量 */
  MAX_PAGE_SIZE: 100,
} as const;

/**
 * 日期格式
 */
export const DATE_FORMATS = {
  /** 日期格式（YYYY-MM-DD） */
  DATE: 'YYYY-MM-DD',
  /** 时间格式（HH:mm:ss） */
  TIME: 'HH:mm:ss',
  /** 日期时间格式（YYYY-MM-DD HH:mm:ss） */
  DATETIME: 'YYYY-MM-DD HH:mm:ss',
  /** ISO格式 */
  ISO: 'YYYY-MM-DDTHH:mm:ssZ',
} as const;

/**
 * 路由路径
 */
export const ROUTES = {
  /** 首页 */
  HOME: '/',
  /** 单图诊断 */
  SINGLE_DIAGNOSIS: '/diagnosis',
  /** 批量诊断 */
  BATCH_DIAGNOSIS: '/batch-diagnosis',
  /** 诊断历史 */
  DIAGNOSIS_HISTORY: '/history',
  /** 本体管理 */
  ONTOLOGY_MANAGEMENT: '/ontology',
  /** 知识管理 */
  KNOWLEDGE_MANAGEMENT: '/knowledge',
  /** 登录 */
  LOGIN: '/login',
} as const;

/**
 * 导航菜单项
 */
export const MENU_ITEMS = [
  { key: 'home', label: '首页', path: ROUTES.HOME, icon: 'HomeOutlined' },
  { key: 'single-diagnosis', label: '单图诊断', path: ROUTES.SINGLE_DIAGNOSIS, icon: 'FileImageOutlined' },
  { key: 'batch-diagnosis', label: '批量诊断', path: ROUTES.BATCH_DIAGNOSIS, icon: 'FolderOpenOutlined' },
  { key: 'history', label: '诊断历史', path: ROUTES.DIAGNOSIS_HISTORY, icon: 'HistoryOutlined' },
  { key: 'ontology', label: '本体管理', path: ROUTES.ONTOLOGY_MANAGEMENT, icon: 'DatabaseOutlined' },
  { key: 'knowledge', label: '知识管理', path: ROUTES.KNOWLEDGE_MANAGEMENT, icon: 'BookOutlined' },
] as const;

/**
 * 错误消息
 */
export const ERROR_MESSAGES = {
  /** 网络错误 */
  NETWORK_ERROR: '网络连接失败，请检查网络设置',
  /** 请求超时 */
  TIMEOUT_ERROR: '请求超时，请稍后重试',
  /** 服务器错误 */
  SERVER_ERROR: '服务器错误，请稍后重试',
  /** 未授权 */
  UNAUTHORIZED: '未授权，请先登录',
  /** 文件格式错误 */
  INVALID_FILE_FORMAT: '不支持的文件格式',
  /** 文件过大 */
  FILE_TOO_LARGE: `文件大小超过 ${UPLOAD_CONFIG.MAX_SIZE}MB`,
  /** 批量上传超限 */
  BATCH_LIMIT_EXCEEDED: `批量上传不能超过 ${UPLOAD_CONFIG.MAX_BATCH_COUNT} 张`,
} as const;

/**
 * 成功消息
 */
export const SUCCESS_MESSAGES = {
  /** 上传成功 */
  UPLOAD_SUCCESS: '上传成功',
  /** 诊断成功 */
  DIAGNOSIS_SUCCESS: '诊断完成',
  /** 保存成功 */
  SAVE_SUCCESS: '保存成功',
  /** 删除成功 */
  DELETE_SUCCESS: '删除成功',
  /** 导出成功 */
  EXPORT_SUCCESS: '导出成功',
} as const;

/**
 * 应用信息
 */
export const APP_INFO = {
  /** 应用名称 */
  NAME: process.env.NEXT_PUBLIC_APP_NAME || 'PhytoOracle',
  /** 应用版本 */
  VERSION: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
  /** 描述 */
  DESCRIPTION: '基于本体建模的花卉疾病诊断系统',
  /** 作者 */
  AUTHOR: 'PhytoOracle Team',
} as const;
