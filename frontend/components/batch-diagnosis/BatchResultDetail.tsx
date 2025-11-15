/**
 * PhytoOracle 批量诊断结果详情Modal组件
 * 在Modal中展示单个诊断结果的完整详情，复用P5.2的DiagnosisResult组件
 */

'use client';

import React from 'react';
import { Modal, Button, Space } from 'antd';
import { LeftOutlined, RightOutlined, CloseOutlined } from '@ant-design/icons';
import { DiagnosisResult as DiagnosisResultType } from '@/types';
import { DiagnosisResult } from '@/components/diagnosis';

/**
 * 批量诊断结果详情Modal组件的Props
 */
export interface BatchResultDetailProps {
  /** 是否显示Modal */
  visible: boolean;
  /** 当前诊断结果 */
  result: DiagnosisResultType | null;
  /** 关闭Modal回调 */
  onClose: () => void;
  /** 是否有上一个结果 */
  hasPrevious?: boolean;
  /** 是否有下一个结果 */
  hasNext?: boolean;
  /** 上一个结果回调 */
  onPrevious?: () => void;
  /** 下一个结果回调 */
  onNext?: () => void;
  /** 当前索引（用于显示） */
  currentIndex?: number;
  /** 总数量（用于显示） */
  totalCount?: number;
}

/**
 * 批量诊断结果详情Modal组件
 *
 * 功能：
 * - Modal方式展示诊断详情
 * - 复用P5.2的DiagnosisResult组件
 * - 支持上一个/下一个导航
 * - 显示当前索引/总数
 */
export const BatchResultDetail: React.FC<BatchResultDetailProps> = ({
  visible,
  result,
  onClose,
  hasPrevious = false,
  hasNext = false,
  onPrevious,
  onNext,
  currentIndex,
  totalCount,
}) => {
  /**
   * 处理键盘导航
   */
  React.useEffect(() => {
    if (!visible) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft' && hasPrevious) {
        onPrevious?.();
      } else if (e.key === 'ArrowRight' && hasNext) {
        onNext?.();
      } else if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [visible, hasPrevious, hasNext, onPrevious, onNext, onClose]);

  return (
    <Modal
      title={
        <div className="flex justify-between items-center">
          <span>诊断详情</span>
          {currentIndex !== undefined && totalCount !== undefined && (
            <span className="text-sm font-normal text-gray-500">
              {currentIndex + 1} / {totalCount}
            </span>
          )}
        </div>
      }
      open={visible}
      onCancel={onClose}
      footer={
        <Space>
          {/* 导航按钮 */}
          <Button
            icon={<LeftOutlined />}
            onClick={onPrevious}
            disabled={!hasPrevious}
          >
            上一个
          </Button>
          <Button
            icon={<RightOutlined />}
            onClick={onNext}
            disabled={!hasNext}
          >
            下一个
          </Button>
          <Button icon={<CloseOutlined />} onClick={onClose}>
            关闭
          </Button>
        </Space>
      }
      width={1200}
      centered
      destroyOnClose
      className="batch-result-detail-modal"
    >
      {result ? (
        <div className="max-h-[70vh] overflow-y-auto">
          {/* 复用P5.2的DiagnosisResult组件 */}
          <DiagnosisResult
            result={result}
            loading={false}
            error={null}
            // 批量诊断结果详情中不显示反馈按钮
            onFeedbackCorrect={undefined}
            onFeedbackIncorrect={undefined}
          />
        </div>
      ) : (
        <div className="text-center text-gray-400 py-12">
          <p>暂无诊断结果</p>
        </div>
      )}
    </Modal>
  );
};

export default BatchResultDetail;

/**
 * 组件使用示例：
 *
 * ```tsx
 * import { BatchResultDetail } from '@/components/batch-diagnosis';
 * import { useState } from 'react';
 * import { DiagnosisResult } from '@/types';
 *
 * function MyPage() {
 *   const [visible, setVisible] = useState(false);
 *   const [currentIndex, setCurrentIndex] = useState(0);
 *   const results: DiagnosisResult[] = [
 *     // ... 诊断结果数组
 *   ];
 *
 *   const currentResult = results[currentIndex];
 *
 *   return (
 *     <>
 *       <Button onClick={() => setVisible(true)}>查看详情</Button>
 *
 *       <BatchResultDetail
 *         visible={visible}
 *         result={currentResult}
 *         onClose={() => setVisible(false)}
 *         hasPrevious={currentIndex > 0}
 *         hasNext={currentIndex < results.length - 1}
 *         onPrevious={() => setCurrentIndex(currentIndex - 1)}
 *         onNext={() => setCurrentIndex(currentIndex + 1)}
 *         currentIndex={currentIndex}
 *         totalCount={results.length}
 *       />
 *     </>
 *   );
 * }
 * ```
 */
