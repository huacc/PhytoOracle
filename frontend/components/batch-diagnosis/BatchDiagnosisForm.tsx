/**
 * PhytoOracle 批量诊断参数配置表单组件
 * 用于配置批量诊断的花卉种属等参数
 */

'use client';

import React from 'react';
import { Form, Select, Button, Space, Alert, Card, Typography } from 'antd';
import {
  PlayCircleOutlined,
  ClearOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { FlowerGenus } from '@/types';
import { FLOWER_GENUS_OPTIONS } from '@/constants';

const { Text } = Typography;

/**
 * 批量诊断表单组件的Props
 */
export interface BatchDiagnosisFormProps {
  /** 当前选择的花卉种属 */
  flowerGenus?: FlowerGenus;
  /** 花卉种属变化回调 */
  onGenusChange?: (genus?: FlowerGenus) => void;
  /** 开始诊断回调 */
  onDiagnose?: () => void;
  /** 清空回调 */
  onClear?: () => void;
  /** 是否正在诊断 */
  diagnosing?: boolean;
  /** 是否有图片 */
  hasImages?: boolean;
  /** 图片数量 */
  imageCount?: number;
}

/**
 * 批量诊断参数配置表单组件
 *
 * 功能：
 * - 花卉种属选择（所有图片使用相同种属）
 * - 开始批量诊断
 * - 清空操作
 * - 参数说明
 */
export const BatchDiagnosisForm: React.FC<BatchDiagnosisFormProps> = ({
  flowerGenus,
  onGenusChange,
  onDiagnose,
  onClear,
  diagnosing = false,
  hasImages = false,
  imageCount = 0,
}) => {
  /**
   * 开始诊断按钮点击处理
   */
  const handleDiagnose = () => {
    if (!hasImages) {
      return;
    }
    onDiagnose?.();
  };

  /**
   * 清空按钮点击处理
   */
  const handleClear = () => {
    onClear?.();
  };

  return (
    <Card
      title={
        <Space>
          <InfoCircleOutlined />
          <span>诊断参数配置</span>
        </Space>
      }
      className="batch-diagnosis-form"
    >
      <Form layout="vertical">
        {/* 花卉种属选择 */}
        <Form.Item
          label="花卉种属"
          tooltip="选择所有图片对应的花卉种属，留空则自动识别"
        >
          <Select
            placeholder="请选择花卉种属（可选）"
            value={flowerGenus}
            onChange={onGenusChange}
            disabled={diagnosing}
            allowClear
            options={[...FLOWER_GENUS_OPTIONS]}
            size="large"
          />
        </Form.Item>

        {/* 操作说明 */}
        <Alert
          message="批量诊断说明"
          description={
            <div className="text-sm">
              <p className="mb-2">
                • 所有图片将使用相同的花卉种属参数
              </p>
              <p className="mb-2">
                • 如不选择种属，系统将自动识别每张图片的种属
              </p>
              <p className="mb-0">
                • 诊断时间取决于图片数量，请耐心等待
              </p>
            </div>
          }
          type="info"
          showIcon
          className="mb-4"
        />

        {/* 当前状态显示 */}
        {hasImages && (
          <div className="mb-4 p-3 bg-blue-50 rounded">
            <Space direction="vertical" size="small" className="w-full">
              <Text>
                已选择图片：<Text strong>{imageCount}</Text> 张
              </Text>
              <Text>
                花卉种属：
                <Text strong>
                  {flowerGenus
                    ? FLOWER_GENUS_OPTIONS.find((opt) => opt.value === flowerGenus)
                        ?.label || flowerGenus
                    : '自动识别'}
                </Text>
              </Text>
            </Space>
          </div>
        )}

        {/* 操作按钮 */}
        <Form.Item className="mb-0">
          <Space className="w-full" direction="vertical" size="middle">
            {/* 开始诊断按钮 */}
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={handleDiagnose}
              loading={diagnosing}
              disabled={!hasImages || diagnosing}
              size="large"
              block
            >
              {diagnosing ? '诊断中...' : '开始批量诊断'}
            </Button>

            {/* 清空按钮 */}
            <Button
              icon={<ClearOutlined />}
              onClick={handleClear}
              disabled={diagnosing}
              size="large"
              block
            >
              清空所有
            </Button>
          </Space>
        </Form.Item>

        {/* 未选择图片提示 */}
        {!hasImages && (
          <Alert
            message="请先上传图片"
            description="点击或拖拽图片到上传区域，然后开始诊断"
            type="warning"
            showIcon
            className="mt-4"
          />
        )}
      </Form>
    </Card>
  );
};

export default BatchDiagnosisForm;

/**
 * 组件使用示例：
 *
 * ```tsx
 * import { BatchDiagnosisForm } from '@/components/batch-diagnosis';
 * import { useState } from 'react';
 * import { FlowerGenus } from '@/types';
 *
 * function MyPage() {
 *   const [genus, setGenus] = useState<FlowerGenus | undefined>();
 *   const [diagnosing, setDiagnosing] = useState(false);
 *   const [imageCount, setImageCount] = useState(0);
 *
 *   const handleDiagnose = async () => {
 *     setDiagnosing(true);
 *     // 执行批量诊断逻辑
 *     await diagnoseBatch(images, genus);
 *     setDiagnosing(false);
 *   };
 *
 *   return (
 *     <BatchDiagnosisForm
 *       flowerGenus={genus}
 *       onGenusChange={setGenus}
 *       onDiagnose={handleDiagnose}
 *       onClear={() => {
 *         setGenus(undefined);
 *         setImageCount(0);
 *       }}
 *       diagnosing={diagnosing}
 *       hasImages={imageCount > 0}
 *       imageCount={imageCount}
 *     />
 *   );
 * }
 * ```
 */
