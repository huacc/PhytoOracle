/**
 * PhytoOracle - 特征匹配详情组件
 * 功能：展示特征向量与疾病本体的匹配得分详情
 *
 * @author PhytoOracle Team
 * @version 1.0.0
 */

'use client';

import React from 'react';
import { Card, Progress, Divider, Typography, Tag, Space } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  MinusCircleOutlined,
} from '@ant-design/icons';
import { FeatureScores } from '@/types';

const { Text, Title } = Typography;

/**
 * FeatureMatchDetails 组件属性
 */
export interface FeatureMatchDetailsProps {
  /** 特征得分详情 */
  scores?: FeatureScores;
  /** 推理过程 */
  reasoning?: string[];
  /** 是否默认展开 */
  defaultOpen?: boolean;
  /** 自定义样式 */
  className?: string;
}

/**
 * 特征匹配状态类型
 */
type MatchStatus = 'matched' | 'fuzzy' | 'unmatched';

/**
 * 特征项数据
 */
interface FeatureItem {
  name: string;
  displayName: string;
  score: number;
  status: MatchStatus;
}

/**
 * 特征匹配详情组件
 *
 * 功能：
 * - 展示总体匹配得分（0-100）
 * - 按特征重要性分组展示（主要/次要/可选）
 * - 显示每个特征的匹配状态（完全匹配✓、模糊匹配~、未匹配✗）
 * - 显示每个特征的得分
 * - 展示推理依据文本
 *
 * @param props - 组件属性
 * @returns 特征匹配详情组件
 */
export const FeatureMatchDetails: React.FC<FeatureMatchDetailsProps> = ({
  scores,
  reasoning,
  defaultOpen = true,
  className = '',
}) => {
  // 如果没有得分数据，显示提示
  if (!scores) {
    return (
      <Card title="🎯 特征匹配详情" className={className}>
        <Text type="secondary">暂无特征匹配详情</Text>
      </Card>
    );
  }

  /**
   * 将得分对象转换为特征项数组
   */
  const convertToFeatureItems = (
    features: Record<string, number>
  ): FeatureItem[] => {
    return Object.entries(features).map(([name, score]) => ({
      name,
      displayName: getFeatureDisplayName(name),
      score,
      status: getMatchStatus(score),
    }));
  };

  // 转换特征数据
  const majorFeatures = convertToFeatureItems(scores.major_features || {});
  const minorFeatures = convertToFeatureItems(scores.minor_features || {});
  const optionalFeatures = convertToFeatureItems(scores.optional_features || {});

  // 计算总得分颜色
  const getScoreColor = (score: number): string => {
    if (score >= 85) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  return (
    <Card
      title={
        <span className="text-lg font-semibold">🎯 特征匹配详情</span>
      }
      className={className}
    >
      {/* 总得分展示 */}
      <div className="text-center mb-6">
        <Title level={2} className="!mb-2" style={{ color: getProgressColor(scores.total_score) }}>
          {scores.total_score.toFixed(1)} / 100
        </Title>
        <Progress
          percent={scores.total_score}
          status={getScoreColor(scores.total_score) as any}
          strokeWidth={12}
          className="!mb-0"
        />
      </div>

      {/* 推理依据 */}
      {reasoning && reasoning.length > 0 && (
        <>
          <Divider orientation="left">推理依据</Divider>
          <div className="mb-6">
            <ul className="space-y-2">
              {reasoning.map((reason, index) => (
                <li key={index} className="flex items-start">
                  <CheckCircleOutlined className="text-green-500 mr-2 mt-1 flex-shrink-0" />
                  <Text className="text-sm">{reason}</Text>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}

      {/* 主要特征 */}
      {majorFeatures.length > 0 && (
        <>
          <Divider orientation="left">主要特征 (权重较高)</Divider>
          <FeatureGroup features={majorFeatures} />
        </>
      )}

      {/* 次要特征 */}
      {minorFeatures.length > 0 && (
        <>
          <Divider orientation="left">次要特征 (权重中等)</Divider>
          <FeatureGroup features={minorFeatures} />
        </>
      )}

      {/* 可选特征 */}
      {optionalFeatures.length > 0 && (
        <>
          <Divider orientation="left">可选特征 (权重较低)</Divider>
          <FeatureGroup features={optionalFeatures} />
        </>
      )}
    </Card>
  );
};

/**
 * 特征组展示组件
 */
interface FeatureGroupProps {
  features: FeatureItem[];
}

const FeatureGroup: React.FC<FeatureGroupProps> = ({ features }) => {
  return (
    <div className="space-y-3 mb-4">
      {features.map((feature, index) => (
        <div
          key={index}
          className={`p-3 rounded border-l-4 ${getFeatureBorderColor(feature.status)} bg-gray-50`}
        >
          <div className="flex items-center justify-between">
            {/* 特征名称和状态 */}
            <div className="flex items-center space-x-2 flex-1">
              {getStatusIcon(feature.status)}
              <Text strong>{feature.displayName}</Text>
              <Tag color={getStatusColor(feature.status)}>
                {getStatusText(feature.status)}
              </Tag>
            </div>

            {/* 得分 */}
            <div className="text-right">
              <Text
                strong
                className="text-base"
                style={{ color: getScoreTextColor(feature.status) }}
              >
                {feature.score} 分
              </Text>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * 辅助函数：获取特征显示名称
 */
const getFeatureDisplayName = (name: string): string => {
  const nameMap: Record<string, string> = {
    // 主要特征
    symptom_type: '症状类型',
    spot_color: '斑点颜色',
    spot_shape: '斑点形状',
    color_border: '边缘颜色',
    // 次要特征
    color_center: '中心颜色',
    location: '发病位置',
    leaf_yellowing: '叶片黄化',
    // 可选特征
    size: '病斑大小',
    distribution: '分布模式',
    coverage: '覆盖度',
    edge_clarity: '边缘清晰度',
    stem_affected: '茎干受影响',
  };
  return nameMap[name] || name;
};

/**
 * 辅助函数：根据得分判断匹配状态
 */
const getMatchStatus = (score: number): MatchStatus => {
  // 这里使用简化逻辑：得分>0表示匹配
  // 实际应用中可能需要更复杂的判断逻辑
  if (score >= 20) return 'matched'; // 高分：完全匹配
  if (score > 0) return 'fuzzy'; // 低分：模糊匹配
  return 'unmatched'; // 0分：未匹配
};

/**
 * 辅助函数：获取状态图标
 */
const getStatusIcon = (status: MatchStatus): React.ReactNode => {
  switch (status) {
    case 'matched':
      return <CheckCircleOutlined className="text-green-500" />;
    case 'fuzzy':
      return <MinusCircleOutlined className="text-orange-500" />;
    case 'unmatched':
      return <CloseCircleOutlined className="text-gray-400" />;
  }
};

/**
 * 辅助函数：获取状态标签颜色
 */
const getStatusColor = (status: MatchStatus): string => {
  switch (status) {
    case 'matched':
      return 'success';
    case 'fuzzy':
      return 'warning';
    case 'unmatched':
      return 'default';
  }
};

/**
 * 辅助函数：获取状态文本
 */
const getStatusText = (status: MatchStatus): string => {
  switch (status) {
    case 'matched':
      return '完全匹配';
    case 'fuzzy':
      return '模糊匹配';
    case 'unmatched':
      return '未匹配';
  }
};

/**
 * 辅助函数：获取特征边框颜色
 */
const getFeatureBorderColor = (status: MatchStatus): string => {
  switch (status) {
    case 'matched':
      return 'border-green-500';
    case 'fuzzy':
      return 'border-orange-500';
    case 'unmatched':
      return 'border-gray-300';
  }
};

/**
 * 辅助函数：获取得分文本颜色
 */
const getScoreTextColor = (status: MatchStatus): string => {
  switch (status) {
    case 'matched':
      return '#52c41a';
    case 'fuzzy':
      return '#fa8c16';
    case 'unmatched':
      return '#8c8c8c';
  }
};

/**
 * 辅助函数：获取进度条颜色
 */
const getProgressColor = (score: number): string => {
  if (score >= 85) return '#52c41a'; // 绿色
  if (score >= 60) return '#faad14'; // 橙色
  return '#ff4d4f'; // 红色
};

/**
 * 使用示例：
 *
 * ```tsx
 * import { FeatureMatchDetails } from '@/components/diagnosis/FeatureMatchDetails';
 *
 * function DiagnosisResultPage() {
 *   const scores = {
 *     total_score: 92.5,
 *     major_features: {
 *       spot_color: 30,
 *       spot_shape: 25,
 *     },
 *     minor_features: {
 *       leaf_yellowing: 15,
 *       location: 10,
 *     },
 *     optional_features: {
 *       size: 2,
 *       distribution: 2,
 *     },
 *   };
 *
 *   const reasoning = [
 *     '检测到叶片表面黑色斑点（主要特征匹配）',
 *     '斑点呈圆形，边缘清晰（形态匹配）',
 *     '叶片周围伴有轻微黄化（次要特征）',
 *   ];
 *
 *   return (
 *     <FeatureMatchDetails
 *       scores={scores}
 *       reasoning={reasoning}
 *       defaultOpen={true}
 *     />
 *   );
 * }
 * ```
 */
