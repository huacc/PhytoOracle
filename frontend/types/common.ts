/**
 * PhytoOracle 通用类型定义
 * 定义全局通用的类型和接口
 */

/**
 * API 响应基础类型
 */
export interface ApiResponse<T = any> {
  /** 是否成功 */
  success?: boolean;
  /** 响应数据 */
  data?: T;
  /** 错误信息 */
  error?: string;
  /** 详细错误信息 */
  detail?: string;
  /** 时间戳 */
  timestamp?: string;
  /** 请求追踪ID */
  request_id?: string;
}

/**
 * 分页参数
 */
export interface PaginationParams {
  /** 每页数量 */
  limit?: number;
  /** 偏移量 */
  offset?: number;
  /** 当前页码（从1开始） */
  page?: number;
  /** 每页大小 */
  pageSize?: number;
}

/**
 * 分页响应数据
 */
export interface PaginatedResponse<T> {
  /** 总数 */
  total: number;
  /** 数据列表 */
  records: T[];
  /** 当前页 */
  page?: number;
  /** 每页大小 */
  pageSize?: number;
  /** 总页数 */
  totalPages?: number;
}

/**
 * 排序参数
 */
export interface SortParams {
  /** 排序字段 */
  field: string;
  /** 排序方向 */
  order: 'asc' | 'desc';
}

/**
 * 选项类型（用于下拉框等）
 */
export interface Option<T = any> {
  /** 显示标签 */
  label: string;
  /** 值 */
  value: T;
  /** 是否禁用 */
  disabled?: boolean;
  /** 额外数据 */
  extra?: any;
}

/**
 * 文件信息
 */
export interface FileInfo {
  /** 文件名 */
  name: string;
  /** 文件大小（字节） */
  size: number;
  /** 文件类型（MIME） */
  type: string;
  /** 文件URL */
  url?: string;
  /** 上传时间 */
  uploadTime?: string;
}

/**
 * 加载状态
 */
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

/**
 * 组件尺寸
 */
export type ComponentSize = 'small' | 'middle' | 'large';

/**
 * 组件主题
 */
export type Theme = 'light' | 'dark';

/**
 * 导出类型
 */
export type ExportFormat = 'excel' | 'csv' | 'json' | 'pdf';
