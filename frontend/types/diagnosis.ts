/**
 * PhytoOracle 诊断相关类型定义
 * 对应后端 API 接口协议
 */

/**
 * 诊断状态
 */
export type DiagnosisStatus = 'confirmed' | 'suspected' | 'unlikely';

/**
 * 花卉种属（Genus）
 */
export type FlowerGenus = 'Rosa' | 'Prunus' | 'Tulipa' | 'Dianthus' | 'Paeonia';

/**
 * 病原体类型
 */
export type PathogenType = 'fungal' | 'bacterial' | 'viral' | 'pest' | 'abiotic';

/**
 * 内容类型（Q0.0）
 */
export type ContentType = 'plant' | 'non_plant' | 'unclear';

/**
 * 植物类别（Q0.1）
 */
export type PlantCategory = 'flower' | 'tree' | 'grass' | 'vegetable' | 'other';

/**
 * 植物器官（Q0.3）
 */
export type PlantOrgan = 'leaf' | 'flower' | 'stem' | 'root';

/**
 * 完整性（Q0.4）
 */
export type Completeness = 'intact' | 'partial' | 'unclear';

/**
 * 是否有异常（Q0.5）
 */
export type HasAbnormality = 'yes' | 'no' | 'unclear';

/**
 * 特征向量（VLM 提取结果）
 */
export interface FeatureVector {
  /** Q0.0: 内容类型 */
  content_type?: ContentType;
  /** Q0.1: 植物类别 */
  plant_category?: PlantCategory;
  /** Q0.2: 花卉种属 */
  flower_genus?: FlowerGenus;
  /** Q0.3: 植物器官 */
  organ?: PlantOrgan;
  /** Q0.4: 完整性 */
  completeness?: Completeness;
  /** Q0.5: 是否有异常 */
  has_abnormality?: HasAbnormality;
  /** Q1: 症状类型 */
  symptom_type?: string;
  /** Q2: 病症颜色 */
  colors?: string[];
  /** Q3: 病症位置 */
  location?: string;
  /** Q4: 病症大小 */
  size?: string;
  /** Q5: 病症分布 */
  distribution?: string;
}

/**
 * 特征得分详情
 */
export interface FeatureScores {
  /** 总分（0-100） */
  total_score: number;
  /** 主要特征得分 */
  major_features: Record<string, number>;
  /** 次要特征得分 */
  minor_features: Record<string, number>;
  /** 可选特征得分 */
  optional_features: Record<string, number>;
}

/**
 * 疾病信息
 */
export interface DiseaseInfo {
  /** 疾病ID */
  disease_id: string;
  /** 疾病中文名 */
  disease_name: string;
  /** 疾病英文名 */
  common_name_en?: string;
  /** 病原体学名 */
  pathogen: string;
  /** 病原体类型 */
  pathogen_type?: PathogenType;
  /** 置信度（0-1） */
  confidence: number;
}

/**
 * 候选疾病
 */
export interface CandidateDisease {
  /** 疾病名称 */
  disease_name: string;
  /** 得分 */
  score: number;
  /** 置信度 */
  confidence: number;
}

/**
 * 诊断结果
 */
export interface DiagnosisResult {
  /** 诊断ID */
  diagnosis_id: string;
  /** 诊断时间戳 */
  timestamp: string;
  /** 诊断状态 */
  status: DiagnosisStatus;
  /** 确诊疾病（status=confirmed时存在） */
  confirmed_disease?: DiseaseInfo;
  /** 疑似疾病列表（status=suspected时存在） */
  suspected_diseases?: DiseaseInfo[];
  /** 特征向量 */
  feature_vector?: FeatureVector;
  /** 得分详情 */
  scores?: FeatureScores;
  /** 推理过程 */
  reasoning?: string[];
  /** 候选疾病列表 */
  candidates?: CandidateDisease[];
  /** VLM提供商 */
  vlm_provider?: string;
  /** 执行时间（毫秒） */
  execution_time_ms?: number;
  /** 图片URL */
  image_url?: string;
  /** 用户反馈 */
  user_feedback?: 'correct' | 'incorrect' | null;
}

/**
 * 诊断请求参数
 */
export interface DiagnosisRequest {
  /** 图片文件 */
  image: File | Blob;
  /** 花卉种属（可选，提供可提高准确率） */
  flower_genus?: FlowerGenus;
}

/**
 * 批量诊断结果
 */
export interface BatchDiagnosisResult {
  /** 批量诊断ID */
  batch_id: string;
  /** 总数 */
  total: number;
  /** 已完成数 */
  completed: number;
  /** 诊断结果列表 */
  results: DiagnosisResult[];
  /** 创建时间 */
  created_at: string;
  /** 完成时间 */
  completed_at?: string;
}

/**
 * 疾病详情（知识库）
 */
export interface DiseaseDetail {
  /** 疾病ID */
  disease_id: string;
  /** 疾病中文名 */
  disease_name: string;
  /** 疾病英文名 */
  common_name_en: string;
  /** 病原体学名 */
  pathogen: string;
  /** 病原体类型 */
  pathogen_type: PathogenType;
  /** 受影响植物 */
  affected_plants: FlowerGenus[];
  /** 典型症状描述 */
  typical_symptoms: string[];
  /** 主要特征 */
  major_features?: FeatureDimension[];
  /** 次要特征 */
  minor_features?: FeatureDimension[];
  /** 可选特征 */
  optional_features?: FeatureDimension[];
  /** 治疗建议（可选） */
  treatment_recommendations?: string[];
}

/**
 * 特征维度
 */
export interface FeatureDimension {
  /** 特征名称 */
  feature_name: string;
  /** 特征值 */
  feature_value: string;
  /** 权重（可选） */
  weight?: number;
}

/**
 * 诊断历史记录
 */
export interface DiagnosisHistoryRecord {
  /** 诊断ID */
  diagnosis_id: string;
  /** 诊断时间 */
  timestamp: string;
  /** 花卉种属 */
  plant_genus?: FlowerGenus;
  /** 诊断状态 */
  status: DiagnosisStatus;
  /** 疾病名称 */
  disease_name: string;
  /** 置信度 */
  confidence: number;
  /** 图片URL */
  image_url: string;
  /** 用户反馈 */
  user_feedback?: 'correct' | 'incorrect' | null;
}

/**
 * 诊断历史查询参数
 */
export interface DiagnosisHistoryQuery {
  /** 起始日期（YYYY-MM-DD） */
  start_date?: string;
  /** 结束日期（YYYY-MM-DD） */
  end_date?: string;
  /** 花卉种属过滤 */
  plant_genus?: FlowerGenus;
  /** 置信度级别过滤 */
  confidence_level?: DiagnosisStatus;
  /** 分页限制 */
  limit?: number;
  /** 分页偏移 */
  offset?: number;
}
