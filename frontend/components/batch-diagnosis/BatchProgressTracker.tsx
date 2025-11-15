/**
 * PhytoOracle 批量诊断进度追踪组件
 * 显示批量诊断的实时进度
 */

'use client';

import React from 'react';
import { Progress, Card, Typography, Space, Statistic, Row, Col } from 'antd';
import {
  SyncOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';

const { Text, Title } = Typography;

/**
 * 批量诊断进度追踪组件的Props
 */
export interface BatchProgressTrackerProps {
  /** 总数 */
  total: number;
  /** 已完成数 */
  completed: number;
  /** 失败数 */
  failed?: number;
  /** 是否正在进行 */
  inProgress?: boolean;
  /** 预计完成时间（秒） */
  estimatedTime?: number;
  /** 已用时间（秒） */
  elapsedTime?: number;
  /** 自定义样式类名 */
  className?: string;
}

/**
 * 批量诊断进度追踪组件
 *
 * 功能：
 * - 显示总进度条（已完成/总数量）
 * - 显示成功数和失败数
 * - 显示实时状态更新
 * - 显示预计完成时间
 */
export const BatchProgressTracker: React.FC<BatchProgressTrackerProps> = ({
  total,
  completed,
  failed = 0,
  inProgress = true,
  estimatedTime,
  elapsedTime,
  className,
}) => {
  // 计算进度百分比
  const completedPercent = total > 0 ? Math.round((completed / total) * 100) : 0;
  const successCount = completed - failed;

  // 计算剩余数量
  const remaining = total - completed;

  /**
   * 格式化时间（秒转为 mm:ss）
   */
  const formatTime = (seconds?: number): string => {
    if (seconds === undefined || seconds === null) return '-';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Card
      title={
        <Space>
          {inProgress && <SyncOutlined spin />}
          <span>{inProgress ? '批量诊断进行中' : '批量诊断已完成'}</span>
        </Space>
      }
      className={className || 'batch-progress-tracker'}
    >
      {/* 总进度条 */}
      <div className="mb-6">
        <div className="flex justify-between mb-2">
          <Text strong>总体进度</Text>
          <Text type="secondary">
            {completed} / {total}
          </Text>
        </div>
        <Progress
          percent={completedPercent}
          status={
            !inProgress && failed > 0
              ? 'exception'
              : !inProgress
              ? 'success'
              : 'active'
          }
          strokeColor={{
            from: '#108ee9',
            to: '#87d068',
          }}
          showInfo={true}
          format={(percent) => `${percent}%`}
        />
      </div>

      {/* 统计数据 */}
      <Row gutter={16} className="mb-4">
        {/* 成功数 */}
        <Col span={8}>
          <Statistic
            title="成功"
            value={successCount}
            valueStyle={{ color: '#52c41a' }}
            prefix={<CheckCircleOutlined />}
          />
        </Col>

        {/* 失败数 */}
        <Col span={8}>
          <Statistic
            title="失败"
            value={failed}
            valueStyle={{ color: failed > 0 ? '#ff4d4f' : undefined }}
            prefix={<CloseCircleOutlined />}
          />
        </Col>

        {/* 剩余数 */}
        <Col span={8}>
          <Statistic
            title="剩余"
            value={remaining}
            valueStyle={{ color: remaining > 0 ? '#1890ff' : undefined }}
            prefix={<SyncOutlined spin={inProgress && remaining > 0} />}
          />
        </Col>
      </Row>

      {/* 时间信息 */}
      {(estimatedTime !== undefined || elapsedTime !== undefined) && (
        <div className="pt-4 border-t border-gray-200">
          <Row gutter={16}>
            {/* 已用时间 */}
            {elapsedTime !== undefined && (
              <Col span={12}>
                <div className="text-center">
                  <Text type="secondary" className="block text-xs mb-1">
                    已用时间
                  </Text>
                  <Text strong className="text-lg">
                    {formatTime(elapsedTime)}
                  </Text>
                </div>
              </Col>
            )}

            {/* 预计完成时间 */}
            {estimatedTime !== undefined && inProgress && (
              <Col span={12}>
                <div className="text-center">
                  <Text type="secondary" className="block text-xs mb-1">
                    预计剩余
                  </Text>
                  <Text strong className="text-lg">
                    {formatTime(estimatedTime)}
                  </Text>
                </div>
              </Col>
            )}
          </Row>
        </div>
      )}

      {/* 完成提示 */}
      {!inProgress && (
        <div className="mt-4 p-3 rounded bg-green-50 text-center">
          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 24 }} />
          <Text className="block mt-2" style={{ color: '#52c41a' }}>
            批量诊断已完成！
            {failed > 0 && `（${failed} 张图片诊断失败）`}
          </Text>
        </div>
      )}
    </Card>
  );
};

export default BatchProgressTracker;

/**
 * 组件使用示例：
 *
 * ```tsx
 * import { BatchProgressTracker } from '@/components/batch-diagnosis';
 * import { useState, useEffect } from 'react';
 *
 * function MyPage() {
 *   const [progress, setProgress] = useState({
 *     total: 10,
 *     completed: 5,
 *     failed: 1,
 *   });
 *
 *   return (
 *     <BatchProgressTracker
 *       total={progress.total}
 *       completed={progress.completed}
 *       failed={progress.failed}
 *       inProgress={progress.completed < progress.total}
 *       estimatedTime={120}
 *       elapsedTime={60}
 *     />
 *   );
 * }
 * ```
 */
