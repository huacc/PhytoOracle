/**
 * PhytoOracle 批量诊断结果卡片组件
 * 在批量诊断结果列表中展示单个诊断结果
 */

'use client';

import React from 'react';
import { Card, Tag, Typography, Space, Button, Tooltip } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  EyeOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import { DiagnosisResult } from '@/types';
import { ImageThumbnail } from './ImageThumbnail';
import { formatConfidence } from '@/utils';
import type { DiagnosisStatusType } from './ImageThumbnail';

const { Text } = Typography;

/**
 * 批量诊断结果卡片组件的Props
 */
export interface BatchResultCardProps {
  /** 诊断结果数据 */
  result: DiagnosisResult;
  /** 图片URL或文件对象 */
  imageSource?: string | File;
  /** 文件名 */
  fileName?: string;
  /** 是否选中 */
  selected?: boolean;
  /** 点击回调 */
  onClick?: () => void;
  /** 查看详情回调 */
  onViewDetail?: () => void;
}

/**
 * 批量诊断结果卡片组件
 *
 * 功能：
 * - 显示图片缩略图
 * - 显示诊断状态（成功/失败/进行中）
 * - 显示疾病名称和置信度
 * - 快速操作（查看详情、重新诊断）
 */
export const BatchResultCard: React.FC<BatchResultCardProps> = ({
  result,
  imageSource,
  fileName,
  selected = false,
  onClick,
  onViewDetail,
}) => {
  // 确定诊断状态
  const getStatus = (): DiagnosisStatusType => {
    // 如果没有确诊疾病且没有疑似疾病，视为失败
    if (!result.confirmed_disease && (!result.suspected_diseases || result.suspected_diseases.length === 0)) {
      return 'failed';
    }
    return 'success';
  };

  const status = getStatus();

  // 获取主要显示的疾病信息
  const primaryDisease = result.confirmed_disease || result.suspected_diseases?.[0];
  const isPrimaryDisease = !!result.confirmed_disease;

  // 获取置信度
  const confidence = primaryDisease?.confidence || 0;

  // 获取置信度标签颜色
  const getConfidenceColor = (conf: number): string => {
    if (conf >= 0.85) return 'green';
    if (conf >= 0.60) return 'orange';
    return 'red';
  };

  return (
    <Card
      hoverable
      className={`
        batch-result-card
        transition-all
        duration-200
        ${selected ? 'ring-2 ring-blue-500' : ''}
        ${status === 'failed' ? 'border-red-300' : ''}
      `}
      onClick={onClick}
      bodyStyle={{ padding: 12 }}
    >
      <div className="flex gap-3">
        {/* 左侧：图片缩略图 */}
        {imageSource && (
          <div className="flex-shrink-0">
            <ImageThumbnail
              src={imageSource}
              fileName={fileName}
              status={status}
              size={80}
              showStatus={false}
            />
          </div>
        )}

        {/* 右侧：诊断信息 */}
        <div className="flex-1 min-w-0">
          {/* 文件名 */}
          <Text
            strong
            ellipsis={{ tooltip: fileName }}
            className="block mb-2 text-sm"
          >
            {fileName || '未命名图片'}
          </Text>

          {/* 诊断结果 */}
          {status === 'success' && primaryDisease ? (
            <Space direction="vertical" size="small" className="w-full">
              {/* 疾病名称 */}
              <div>
                <Tag
                  color={isPrimaryDisease ? 'green' : 'orange'}
                  className="mb-1"
                >
                  {isPrimaryDisease ? '确诊' : '疑似'}
                </Tag>
                <Text className="text-sm">
                  {primaryDisease.disease_name || primaryDisease.disease_id}
                </Text>
              </div>

              {/* 置信度 */}
              <div>
                <Text type="secondary" className="text-xs">
                  置信度：
                </Text>
                <Tag color={getConfidenceColor(confidence)} className="ml-1">
                  {formatConfidence(confidence)}
                </Tag>
              </div>

              {/* 查看详情按钮 */}
              <Button
                type="link"
                size="small"
                icon={<EyeOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  onViewDetail?.();
                }}
                className="p-0 h-auto"
              >
                查看详情
              </Button>
            </Space>
          ) : (
            <div>
              <Tag color="red" icon={<CloseCircleOutlined />}>
                诊断失败
              </Tag>
              <Text type="secondary" className="block mt-2 text-xs">
                无法识别疾病，请检查图片质量或重新诊断
              </Text>
            </div>
          )}
        </div>

        {/* 状态图标（右上角） */}
        <div className="flex-shrink-0">
          {status === 'success' ? (
            <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />
          ) : (
            <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 20 }} />
          )}
        </div>
      </div>
    </Card>
  );
};

export default BatchResultCard;

/**
 * 组件使用示例：
 *
 * ```tsx
 * import { BatchResultCard } from '@/components/batch-diagnosis';
 * import { DiagnosisResult } from '@/types';
 *
 * const result: DiagnosisResult = {
 *   diagnosis_id: '123',
 *   image_id: 'img_001',
 *   confirmed_disease: {
 *     disease_id: 'rose_black_spot',
 *     disease_name_zh: '玫瑰黑斑病',
 *     disease_name_en: 'Rose Black Spot',
 *     confidence: 0.95,
 *     pathogen: {
 *       type: 'fungal',
 *       species: 'Diplocarpon rosae',
 *     },
 *   },
 *   feature_vector: {},
 *   feature_scores: {},
 *   reasoning: '',
 *   created_at: '2025-11-15T12:00:00Z',
 * };
 *
 * <BatchResultCard
 *   result={result}
 *   imageSource={fileObject}
 *   fileName="rose_001.jpg"
 *   selected={false}
 *   onClick={() => console.log('clicked')}
 *   onViewDetail={() => console.log('view detail')}
 * />
 * ```
 */
