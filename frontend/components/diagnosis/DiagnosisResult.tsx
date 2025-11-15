/**
 * PhytoOracle - 诊断结果展示组件
 * 功能：整合诊断结果的各个子组件，提供完整的结果展示
 *
 * @author PhytoOracle Team
 * @version 1.0.0
 */

'use client';

import React from 'react';
import { Card, Empty, Spin, Alert, Divider, Button, Space } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  LikeOutlined,
  DislikeOutlined,
} from '@ant-design/icons';
import { DiagnosisResult as DiagnosisResultType } from '@/types';
import { DiseaseCard } from './DiseaseCard';
import { VLMQuestionnaire } from './VLMQuestionnaire';
import { FeatureMatchDetails } from './FeatureMatchDetails';

/**
 * DiagnosisResult 组件属性
 */
export interface DiagnosisResultProps {
  /** 诊断结果数据 */
  result: DiagnosisResultType | null;
  /** 是否正在诊断 */
  loading?: boolean;
  /** 诊断错误信息 */
  error?: string | null;
  /** 反馈回调：诊断结果正确 */
  onFeedbackCorrect?: (resultId: string) => void;
  /** 反馈回调：诊断结果错误 */
  onFeedbackIncorrect?: (resultId: string) => void;
  /** 自定义样式 */
  className?: string;
}

/**
 * 诊断结果展示组件
 *
 * 功能：
 * - 展示加载中状态（骨架屏或Loading）
 * - 展示错误状态（错误提示）
 * - 展示成功状态：
 *   - 疾病信息卡片（DiseaseCard）
 *   - VLM问答对展示（VLMQuestionnaire）
 *   - 特征匹配详情（FeatureMatchDetails）
 *   - 反馈按钮（诊断正确/错误）
 * - 处理无结果状态（Empty）
 *
 * @param props - 组件属性
 * @returns 诊断结果展示组件
 */
export const DiagnosisResult: React.FC<DiagnosisResultProps> = ({
  result,
  loading = false,
  error = null,
  onFeedbackCorrect,
  onFeedbackIncorrect,
  className = '',
}) => {
  /**
   * 渲染加载中状态
   */
  const renderLoading = () => (
    <Card className={className}>
      <div className="flex flex-col items-center justify-center py-16">
        <Spin size="large" />
        <p className="mt-4 text-gray-600">正在分析图片，请稍候...</p>
        <p className="mt-2 text-sm text-gray-400">
          系统正在使用视觉语言模型提取特征并匹配疾病
        </p>
      </div>
    </Card>
  );

  /**
   * 渲染错误状态
   */
  const renderError = () => (
    <Alert
      message="诊断失败"
      description={error || '诊断过程中发生未知错误，请重试'}
      type="error"
      showIcon
      icon={<CloseCircleOutlined />}
      className={className}
    />
  );

  /**
   * 渲染空状态
   */
  const renderEmpty = () => (
    <Card className={className}>
      <Empty
        description="暂无诊断结果"
        className="py-12"
      />
    </Card>
  );

  /**
   * 处理反馈按钮点击
   */
  const handleFeedback = (isCorrect: boolean) => {
    if (!result?.diagnosis_id) return;

    if (isCorrect) {
      onFeedbackCorrect?.(result.diagnosis_id);
    } else {
      onFeedbackIncorrect?.(result.diagnosis_id);
    }
  };

  // 加载中状态
  if (loading) {
    return renderLoading();
  }

  // 错误状态
  if (error) {
    return renderError();
  }

  // 无结果状态
  if (!result) {
    return renderEmpty();
  }

  // 成功状态：展示完整诊断结果
  return (
    <div className={`space-y-6 ${className}`}>
      {/* 诊断成功提示 */}
      <Alert
        message="诊断完成"
        description={`已成功分析图片并识别出可能的疾病。诊断ID：${result.diagnosis_id}`}
        type="success"
        showIcon
        icon={<CheckCircleOutlined />}
        closable
      />

      {/* 疾病信息卡片 */}
      {result.confirmed_disease && (
        <div>
          <h2 className="text-xl font-semibold mb-4">🩺 诊断结果</h2>
          <DiseaseCard
            disease={result.confirmed_disease}
            status={result.status}
            detailed={true}
          />
        </div>
      )}

      {/* 疑似疾病列表 */}
      {result.suspected_diseases && result.suspected_diseases.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4">🩺 可能的疾病</h2>
          <div className="space-y-4">
            {result.suspected_diseases.map((disease, index) => (
              <DiseaseCard
                key={index}
                disease={disease}
                status={result.status}
                detailed={true}
              />
            ))}
          </div>
        </div>
      )}

      {/* VLM 问答对展示 */}
      {result.feature_vector && (
        <>
          <Divider />
          <div>
            <h2 className="text-xl font-semibold mb-4">💬 VLM 分析过程</h2>
            <VLMQuestionnaire
              featureVector={result.feature_vector}
              defaultOpen={false}
            />
          </div>
        </>
      )}

      {/* 特征匹配详情 */}
      {result.scores && (
        <>
          <Divider />
          <div>
            <h2 className="text-xl font-semibold mb-4">🎯 特征匹配分析</h2>
            <FeatureMatchDetails
              scores={result.scores}
              reasoning={result.reasoning}
              defaultOpen={true}
            />
          </div>
        </>
      )}

      <Divider />

      {/* 反馈区域 */}
      <Card
        title={
          <span className="text-lg font-semibold">📝 诊断反馈</span>
        }
      >
        <div className="text-center">
          <p className="text-gray-600 mb-4">
            这个诊断结果是否准确？您的反馈将帮助我们改进诊断系统。
          </p>
          <Space size="large">
            <Button
              type="primary"
              size="large"
              icon={<LikeOutlined />}
              onClick={() => handleFeedback(true)}
              className="px-8"
            >
              诊断正确
            </Button>
            <Button
              size="large"
              icon={<DislikeOutlined />}
              onClick={() => handleFeedback(false)}
              className="px-8"
            >
              诊断错误
            </Button>
          </Space>
        </div>

        {/* 反馈说明 */}
        <div className="mt-6 p-4 bg-gray-50 rounded border border-gray-200">
          <p className="text-xs text-gray-600 mb-2">
            <strong>反馈说明：</strong>
          </p>
          <ul className="text-xs text-gray-600 space-y-1 pl-4">
            <li>• 点击"诊断正确"表示系统识别的疾病与实际情况相符</li>
            <li>• 点击"诊断错误"表示系统识别有误，我们会记录并改进</li>
            <li>• 您的反馈将用于优化诊断算法和本体知识库</li>
            <li>• 反馈数据会被匿名化处理，仅用于系统改进</li>
          </ul>
        </div>
      </Card>

      {/* 诊断详情元信息 */}
      <Card
        title={
          <span className="text-sm font-medium text-gray-600">诊断元信息</span>
        }
        size="small"
      >
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500">诊断ID：</span>
            <span className="font-mono text-xs">{result.diagnosis_id}</span>
          </div>
          <div>
            <span className="text-gray-500">诊断时间：</span>
            <span>{new Date(result.timestamp).toLocaleString('zh-CN')}</span>
          </div>
          <div>
            <span className="text-gray-500">诊断状态：</span>
            <span className="font-semibold">
              {getStatusText(result.status)}
            </span>
          </div>
          {result.scores && (
            <div>
              <span className="text-gray-500">总得分：</span>
              <span className="font-semibold text-green-600">
                {result.scores.total_score.toFixed(1)} / 100
              </span>
            </div>
          )}
          {result.execution_time_ms && (
            <div>
              <span className="text-gray-500">执行时间：</span>
              <span className="font-semibold">
                {result.execution_time_ms}ms
              </span>
            </div>
          )}
          {result.vlm_provider && (
            <div>
              <span className="text-gray-500">VLM提供商：</span>
              <span className="font-semibold">
                {result.vlm_provider}
              </span>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

/**
 * 辅助函数：获取诊断状态文本
 */
const getStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    confirmed: '确诊',
    suspected: '疑似',
    unlikely: '不确定',
  };
  return statusMap[status] || status;
};

/**
 * 使用示例：
 *
 * ```tsx
 * import { DiagnosisResult } from '@/components/diagnosis/DiagnosisResult';
 * import { useDiagnosisStore } from '@/stores/diagnosis-store';
 *
 * function DiagnosisPage() {
 *   const { currentResult, loading, error } = useDiagnosisStore();
 *
 *   const handleFeedbackCorrect = async (resultId: string) => {
 *     console.log('诊断正确反馈:', resultId);
 *     // 调用反馈API
 *   };
 *
 *   const handleFeedbackIncorrect = async (resultId: string) => {
 *     console.log('诊断错误反馈:', resultId);
 *     // 调用反馈API
 *   };
 *
 *   return (
 *     <DiagnosisResult
 *       result={currentResult}
 *       loading={loading}
 *       error={error}
 *       onFeedbackCorrect={handleFeedbackCorrect}
 *       onFeedbackIncorrect={handleFeedbackIncorrect}
 *     />
 *   );
 * }
 * ```
 */
