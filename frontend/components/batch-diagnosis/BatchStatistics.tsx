/**
 * PhytoOracle 批量诊断结果统计汇总组件
 * 展示批量诊断结果的统计信息
 */

'use client';

import React, { useMemo } from 'react';
import { Card, Row, Col, Statistic, Progress, Typography, Tag, Space } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  FileImageOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { DiagnosisResult } from '@/types';

const { Text } = Typography;

/**
 * 批量诊断结果统计组件的Props
 */
export interface BatchStatisticsProps {
  /** 诊断结果列表 */
  results: DiagnosisResult[];
}

/**
 * 批量诊断结果统计汇总组件
 *
 * 功能：
 * - 总数/成功/失败数量统计
 * - 疾病分布统计（Top 5）
 * - 置信度分布统计
 * - 成功率展示
 */
export const BatchStatistics: React.FC<BatchStatisticsProps> = ({ results }) => {
  /**
   * 计算统计数据
   */
  const statistics = useMemo(() => {
    const total = results.length;
    let successCount = 0;
    let failedCount = 0;
    const diseaseMap = new Map<string, number>();
    let totalConfidence = 0;
    let confidenceCount = 0;

    results.forEach((result) => {
      const hasDisease =
        result.confirmed_disease ||
        (result.suspected_diseases && result.suspected_diseases.length > 0);

      if (hasDisease) {
        successCount++;

        // 统计疾病分布
        const disease = result.confirmed_disease || result.suspected_diseases![0];
        const diseaseName = disease.disease_name || disease.disease_id;
        diseaseMap.set(diseaseName, (diseaseMap.get(diseaseName) || 0) + 1);

        // 累加置信度
        if (disease.confidence) {
          totalConfidence += disease.confidence;
          confidenceCount++;
        }
      } else {
        failedCount++;
      }
    });

    // 疾病分布Top 5
    const diseaseDistribution = Array.from(diseaseMap.entries())
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    // 平均置信度
    const avgConfidence = confidenceCount > 0 ? totalConfidence / confidenceCount : 0;

    // 成功率
    const successRate = total > 0 ? (successCount / total) * 100 : 0;

    return {
      total,
      successCount,
      failedCount,
      successRate,
      avgConfidence,
      diseaseDistribution,
    };
  }, [results]);

  return (
    <Card title="统计汇总" className="batch-statistics">
      {/* 核心指标 */}
      <Row gutter={16} className="mb-6">
        <Col span={6}>
          <Statistic
            title="总数"
            value={statistics.total}
            prefix={<FileImageOutlined />}
            valueStyle={{ color: '#1890ff' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="成功"
            value={statistics.successCount}
            prefix={<CheckCircleOutlined />}
            valueStyle={{ color: '#52c41a' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="失败"
            value={statistics.failedCount}
            prefix={<CloseCircleOutlined />}
            valueStyle={{ color: statistics.failedCount > 0 ? '#ff4d4f' : undefined }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="平均置信度"
            value={statistics.avgConfidence}
            precision={2}
            suffix="%"
            prefix={<ThunderboltOutlined />}
            formatter={(value) => `${((value as number) * 100).toFixed(1)}`}
            valueStyle={{ color: '#faad14' }}
          />
        </Col>
      </Row>

      {/* 成功率进度条 */}
      <div className="mb-6">
        <div className="flex justify-between mb-2">
          <Text strong>成功率</Text>
          <Text type="secondary">{statistics.successRate.toFixed(1)}%</Text>
        </div>
        <Progress
          percent={statistics.successRate}
          status={statistics.successRate >= 80 ? 'success' : 'normal'}
          strokeColor={{
            '0%': statistics.successRate >= 80 ? '#52c41a' : '#1890ff',
            '100%': statistics.successRate >= 80 ? '#95de64' : '#69c0ff',
          }}
        />
      </div>

      {/* 疾病分布Top 5 */}
      {statistics.diseaseDistribution.length > 0 && (
        <div>
          <Text strong className="block mb-3">
            疾病分布（Top 5）
          </Text>
          <div className="space-y-2">
            {statistics.diseaseDistribution.map((item, index) => (
              <div
                key={item.name}
                className="flex items-center justify-between p-2 bg-gray-50 rounded"
              >
                <Space>
                  <Tag color="blue">{index + 1}</Tag>
                  <Text>{item.name}</Text>
                </Space>
                <Text strong>{item.count} 张</Text>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 空状态 */}
      {statistics.total === 0 && (
        <div className="text-center text-gray-400 py-8">
          <Text type="secondary">暂无统计数据</Text>
        </div>
      )}
    </Card>
  );
};

export default BatchStatistics;

/**
 * 组件使用示例：
 *
 * ```tsx
 * import { BatchStatistics } from '@/components/batch-diagnosis';
 * import { DiagnosisResult } from '@/types';
 *
 * const results: DiagnosisResult[] = [
 *   // ... 诊断结果数组
 * ];
 *
 * <BatchStatistics results={results} />
 * ```
 */
