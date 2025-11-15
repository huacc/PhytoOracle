/**
 * PhytoOracle 知识库管理相关类型定义
 */

import { FlowerGenus, PathogenType } from './diagnosis';

/**
 * 本体类型
 */
export type OntologyType = 'feature' | 'disease' | 'host' | 'treatment';

/**
 * 字段数据类型
 */
export type FieldDataType = 'string' | 'number' | 'boolean' | 'enum' | 'array' | 'object';

/**
 * 特征本体维度
 */
export interface FeatureOntologyDimension {
  /** 维度名称（如：symptom_type） */
  dimension_name: string;
  /** 维度中文名 */
  display_name: string;
  /** 数据类型 */
  type: FieldDataType;
  /** 枚举值列表（type=enum时） */
  enum_values?: EnumValue[];
  /** 是否必需 */
  required?: boolean;
  /** 描述 */
  description?: string;
}

/**
 * 枚举值定义
 */
export interface EnumValue {
  /** 枚举键（如：necrosis_spot） */
  key: string;
  /** 中文标签 */
  label: string;
  /** 英文标签 */
  label_en?: string;
  /** 描述 */
  description?: string;
}

/**
 * 特征本体（Feature Ontology）
 */
export interface FeatureOntology {
  /** 本体ID */
  ontology_id: string;
  /** 版本 */
  version: string;
  /** 更新时间 */
  updated_at: string;
  /** 描述 */
  description: string;
  /** 维度列表 */
  dimensions: FeatureOntologyDimension[];
  /** 模糊匹配规则 */
  fuzzy_rules?: FuzzyMatchingRules;
}

/**
 * 模糊匹配规则
 */
export interface FuzzyMatchingRules {
  /** 颜色别名映射 */
  color_aliases?: Record<string, string[]>;
  /** 大小容差 */
  size_tolerance?: number;
  /** 同义词映射 */
  synonym_mapping?: Record<string, string[]>;
}

/**
 * 疾病Schema字段定义
 */
export interface DiseaseSchemaField {
  /** 字段名称 */
  field_name: string;
  /** 字段中文名 */
  display_name: string;
  /** 数据类型 */
  type: FieldDataType;
  /** 是否必需 */
  required: boolean;
  /** 描述 */
  description: string;
  /** 默认值（可选） */
  default_value?: any;
}

/**
 * 疾病Schema定义
 */
export interface DiseaseSchema {
  /** Schema ID */
  schema_id: string;
  /** 版本 */
  version: string;
  /** 必需字段 */
  required_fields: DiseaseSchemaField[];
  /** 可选字段 */
  optional_fields: DiseaseSchemaField[];
  /** 约束规则 */
  constraints?: Record<string, any>;
}

/**
 * 宿主Schema定义
 */
export interface HostSchema {
  /** Schema ID */
  schema_id: string;
  /** 版本 */
  version: string;
  /** 字段定义 */
  fields: DiseaseSchemaField[];
}

/**
 * 治疗Schema定义
 */
export interface TreatmentSchema {
  /** Schema ID */
  schema_id: string;
  /** 版本 */
  version: string;
  /** 字段定义 */
  fields: DiseaseSchemaField[];
}

/**
 * 本体列表项
 */
export interface OntologyListItem {
  /** 本体类型 */
  type: OntologyType;
  /** 本体名称 */
  name: string;
  /** 文件路径 */
  file_path?: string;
  /** 版本 */
  version?: string;
  /** 更新时间 */
  updated_at?: string;
}

/**
 * 知识库目录树 - 宿主节点
 */
export interface HostTreeNode {
  /** 宿主属名（如：Rosa） */
  genus: FlowerGenus;
  /** 中文名称 */
  name_zh: string;
  /** 该属下的疾病列表 */
  diseases: DiseaseTreeNode[];
}

/**
 * 知识库目录树 - 疾病节点
 */
export interface DiseaseTreeNode {
  /** 疾病ID */
  id: string;
  /** 疾病中文名 */
  name_zh: string;
  /** 疾病英文名（可选） */
  name_en?: string;
}

/**
 * 知识库目录树 - 配置节点
 */
export interface ConfigTreeNode {
  /** 配置ID */
  id: string;
  /** 配置名称 */
  name: string;
  /** 配置类型 */
  type: 'config';
}

/**
 * 知识库目录树
 */
export interface KnowledgeTree {
  /** 宿主列表 */
  hosts: HostTreeNode[];
  /** 其他配置 */
  others: ConfigTreeNode[];
}

/**
 * VLM可理解的描述
 */
export interface VLMDescription {
  /** 影像学描述 */
  imaging_description?: string;
  /** 日常用语描述 */
  everyday_language?: string;
  /** 空间定位方法 */
  spatial_positioning?: string;
}

/**
 * 疾病知识 - 特征维度
 */
export interface DiseaseFeatureDimension {
  /** 维度名称（引用特征本体） */
  dimension_name: string;
  /** 标准值 */
  standard_value: string | string[];
  /** 专业术语 */
  terminology?: string;
  /** VLM可理解的描述 */
  vlm_description?: VLMDescription;
  /** 权重（百分比） */
  weight?: number;
  /** 重要性级别 */
  importance?: 'major' | 'minor' | 'optional';
}

/**
 * 疾病知识实例
 */
export interface DiseaseKnowledge {
  /** 疾病ID */
  disease_id: string;
  /** 疾病中文名 */
  disease_name_zh: string;
  /** 疾病英文名 */
  disease_name_en: string;
  /** 病原体信息 */
  pathogen: {
    /** 病原体类型 */
    type: PathogenType;
    /** 病原体学名 */
    species: string;
  };
  /** 宿主属名 */
  host_genus: FlowerGenus;
  /** 特征向量（所有维度） */
  feature_vector: Record<string, any>;
  /** 多维度知识 */
  dimensions: DiseaseFeatureDimension[];
  /** 治疗建议（可选） */
  treatment_recommendations?: string[];
  /** 更新时间 */
  updated_at?: string;
}

/**
 * 知识库快照
 */
export interface KnowledgeSnapshot {
  /** 快照ID */
  snapshot_id: string;
  /** 版本号 */
  version: string;
  /** 创建时间 */
  created_at: string;
  /** 修改说明 */
  description: string;
  /** 文件路径 */
  file_path: string;
  /** 文件大小（字节） */
  file_size?: number;
}

/**
 * 知识验证结果
 */
export interface KnowledgeValidationResult {
  /** 是否有效 */
  valid: boolean;
  /** 错误列表 */
  errors?: ValidationError[];
  /** 警告列表 */
  warnings?: ValidationWarning[];
}

/**
 * 验证错误
 */
export interface ValidationError {
  /** 错误字段 */
  field: string;
  /** 错误消息 */
  message: string;
  /** 错误代码 */
  code?: string;
}

/**
 * 验证警告
 */
export interface ValidationWarning {
  /** 警告字段 */
  field: string;
  /** 警告消息 */
  message: string;
  /** 警告级别 */
  level?: 'info' | 'warning';
}
