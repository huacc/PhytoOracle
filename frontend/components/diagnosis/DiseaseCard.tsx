/**
 * PhytoOracle - 疾病信息卡片组件
 * 功能：展示诊断出的疾病信息
 *
 * @author PhytoOracle Team
 * @version 1.0.0
 */

'use client';

import React from 'react';
import { Card, Tag, Descriptions, Typography } from 'antd';
import {
  CheckCircleOutlined,
  QuestionCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { DiseaseInfo, DiagnosisStatus } from '@/types';
import { formatConfidence } from '@/utils';

const { Title, Text } = Typography;

/**
 * DiseaseCard 组件属性
 */
export interface DiseaseCardProps {
  /** 疾病信息 */
  disease: DiseaseInfo;
  /** 诊断状态 */
  status: DiagnosisStatus;
  /** 是否显示详细信息 */
  detailed?: boolean;
  /** 自定义样式 */
  className?: string;
}

/**
 * 获取状态配置
 * @param status - 诊断状态
 * @returns 状态配置对象
 */
const getStatusConfig = (status: DiagnosisStatus) => {
  switch (status) {
    case 'confirmed':
      return {
        color: 'success',
        icon: <CheckCircleOutlined />,
        text: '确诊',
        bgClass: 'bg-green-50 border-green-200',
      };
    case 'suspected':
      return {
        color: 'warning',
        icon: <QuestionCircleOutlined />,
        text: '疑似',
        bgClass: 'bg-orange-50 border-orange-200',
      };
    case 'unlikely':
      return {
        color: 'default',
        icon: <CloseCircleOutlined />,
        text: '未知',
        bgClass: 'bg-gray-50 border-gray-200',
      };
  }
};

/**
 * 获取置信度颜色
 * @param confidence - 置信度（0-1）
 * @returns Tailwind CSS 颜色类
 */
const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.85) return 'text-green-600';
  if (confidence >= 0.60) return 'text-orange-600';
  return 'text-red-600';
};

/**
 * 疾病信息卡片组件
 *
 * 功能：
 * - 展示疾病名称（中英文）
 * - 展示病原体信息
 * - 展示置信度
 * - 展示诊断状态（确诊/疑似/未知）
 * - 支持详细模式和简洁模式
 *
 * @param props - 组件属性
 * @returns 疾病信息卡片组件
 */
export const DiseaseCard: React.FC<DiseaseCardProps> = ({
  disease,
  status,
  detailed = true,
  className = '',
}) => {
  const statusConfig = getStatusConfig(status);
  const confidenceColor = getConfidenceColor(disease.confidence);

  return (
    <Card
      className={`${statusConfig.bgClass} border-2 shadow-sm hover:shadow-md transition-shadow ${className}`}
      bordered={false}
    >
      {/* 卡片头部：疾病名称和状态 */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          {/* 疾病中文名 */}
          <Title level={3} className="!mb-2">
            {disease.disease_name}
          </Title>

          {/* 疾病英文名 */}
          {disease.common_name_en && (
            <Text type="secondary" className="text-base">
              {disease.common_name_en}
            </Text>
          )}
        </div>

        {/* 诊断状态标签 */}
        <Tag
          color={statusConfig.color}
          icon={statusConfig.icon}
          className="text-base px-4 py-1"
        >
          {statusConfig.text}
        </Tag>
      </div>

      {/* 卡片内容：置信度和病原体 */}
      {detailed ? (
        <Descriptions column={1} size="small" bordered={false}>
          {/* 置信度 */}
          <Descriptions.Item label="置信度">
            <span className={`text-lg font-semibold ${confidenceColor}`}>
              {formatConfidence(disease.confidence)}
            </span>
          </Descriptions.Item>

          {/* 病原体学名 */}
          <Descriptions.Item label="病原体">
            <Text code className="text-sm">
              {disease.pathogen}
            </Text>
          </Descriptions.Item>

          {/* 病原体类型 */}
          {disease.pathogen_type && (
            <Descriptions.Item label="病原体类型">
              <Tag color="blue">
                {getPathogenTypeName(disease.pathogen_type)}
              </Tag>
            </Descriptions.Item>
          )}
        </Descriptions>
      ) : (
        // 简洁模式：仅显示置信度
        <div className="mt-2">
          <Text type="secondary">置信度：</Text>
          <span className={`ml-2 text-base font-semibold ${confidenceColor}`}>
            {formatConfidence(disease.confidence)}
          </span>
        </div>
      )}
    </Card>
  );
};

/**
 * 获取病原体类型中文名称
 * @param type - 病原体类型
 * @returns 中文名称
 */
const getPathogenTypeName = (type: string): string => {
  const nameMap: Record<string, string> = {
    fungal: '真菌性',
    bacterial: '细菌性',
    viral: '病毒性',
    pest: '虫害',
    abiotic: '非生物性',
  };
  return nameMap[type] || type;
};

/**
 * 使用示例：
 *
 * ```tsx
 * import { DiseaseCard } from '@/components/diagnosis/DiseaseCard';
 *
 * function DiagnosisResult() {
 *   const disease = {
 *     disease_id: 'rose_black_spot',
 *     disease_name: '玫瑰黑斑病',
 *     common_name_en: 'Black Spot',
 *     pathogen: 'Diplocarpon rosae',
 *     pathogen_type: 'fungal',
 *     confidence: 0.92,
 *   };
 *
 *   return (
 *     <DiseaseCard
 *       disease={disease}
 *       status="confirmed"
 *       detailed={true}
 *     />
 *   );
 * }
 * ```
 */
