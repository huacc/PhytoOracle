/**
 * PhytoOracle - 诊断参数表单组件
 * 功能：花卉种属选择、诊断按钮
 *
 * @author PhytoOracle Team
 * @version 1.0.0
 */

'use client';

import React from 'react';
import { Form, Select, Button, Space, Alert } from 'antd';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import { FlowerGenus } from '@/types';
import { FLOWER_GENUS_OPTIONS } from '@/constants';

/**
 * DiagnosisForm 组件属性
 */
export interface DiagnosisFormProps {
  /** 当前选择的花卉种属 */
  flowerGenus?: FlowerGenus;
  /** 花卉种属变更回调 */
  onGenusChange?: (genus: FlowerGenus | undefined) => void;
  /** 开始诊断回调 */
  onDiagnose?: () => void;
  /** 重新上传回调 */
  onReset?: () => void;
  /** 是否禁用诊断按钮 */
  diagnosing?: boolean;
  /** 是否已选择图片 */
  hasImage?: boolean;
  /** 自定义样式 */
  className?: string;
}

/**
 * 诊断参数表单组件
 *
 * 功能：
 * - 花卉种属下拉选择（可选）
 * - 开始诊断按钮
 * - 重新上传按钮
 * - 表单验证（确保已选择图片）
 *
 * @param props - 组件属性
 * @returns 诊断表单组件
 */
export const DiagnosisForm: React.FC<DiagnosisFormProps> = ({
  flowerGenus,
  onGenusChange,
  onDiagnose,
  onReset,
  diagnosing = false,
  hasImage = false,
  className = '',
}) => {
  // Form 实例
  const [form] = Form.useForm();

  /**
   * 处理诊断按钮点击
   */
  const handleDiagnose = () => {
    if (!hasImage) {
      // 未选择图片时不执行诊断
      return;
    }

    // 调用父组件回调
    onDiagnose?.();
  };

  /**
   * 处理种属变更
   */
  const handleGenusChange = (value: FlowerGenus | undefined) => {
    onGenusChange?.(value);
  };

  /**
   * 处理重置
   */
  const handleReset = () => {
    form.resetFields();
    onGenusChange?.(undefined);
    onReset?.();
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm p-6 ${className}`}>
      {/* 提示信息 */}
      {!hasImage && (
        <Alert
          message="请先上传花卉图片"
          description="请在上方上传需要诊断的花卉病害图片，然后选择花卉种属（可选），最后点击开始诊断按钮。"
          type="info"
          showIcon
          className="mb-4"
        />
      )}

      {hasImage && !diagnosing && (
        <Alert
          message="图片已准备就绪"
          description="您可以选择花卉种属以提高诊断准确率，或直接点击开始诊断。"
          type="success"
          showIcon
          className="mb-4"
        />
      )}

      {diagnosing && (
        <Alert
          message="诊断进行中"
          description="正在分析图片并提取特征，请稍候..."
          type="warning"
          showIcon
          icon={<SearchOutlined spin />}
          className="mb-4"
        />
      )}

      <Form
        form={form}
        layout="vertical"
        initialValues={{
          flower_genus: flowerGenus,
        }}
      >
        {/* 花卉种属选择 */}
        <Form.Item
          label="花卉种属 (可选)"
          name="flower_genus"
          tooltip="提供花卉种属可以提高诊断准确率并缩短诊断时间。如果不确定，可以留空让系统自动识别。"
        >
          <Select
            placeholder="请选择花卉种属（留空则自动识别）"
            options={[...FLOWER_GENUS_OPTIONS]}
            onChange={handleGenusChange}
            disabled={diagnosing}
            allowClear
            size="large"
            className="w-full"
          />
        </Form.Item>

        {/* 操作按钮 */}
        <Form.Item className="mb-0">
          <Space size="middle" className="w-full" wrap>
            {/* 开始诊断按钮 */}
            <Button
              type="primary"
              size="large"
              icon={<SearchOutlined />}
              onClick={handleDiagnose}
              loading={diagnosing}
              disabled={!hasImage || diagnosing}
              className="px-8"
            >
              {diagnosing ? '诊断中...' : '开始诊断'}
            </Button>

            {/* 重新上传按钮 */}
            <Button
              size="large"
              icon={<ReloadOutlined />}
              onClick={handleReset}
              disabled={diagnosing}
            >
              重新上传
            </Button>
          </Space>
        </Form.Item>

        {/* 诊断说明 */}
        {hasImage && !diagnosing && (
          <div className="mt-4 p-3 bg-gray-50 rounded border border-gray-200">
            <p className="text-xs text-gray-600 mb-2">
              <strong>诊断说明：</strong>
            </p>
            <ul className="text-xs text-gray-600 space-y-1 pl-4">
              <li>• 系统将使用视觉语言模型（VLM）分析图片</li>
              <li>• 诊断时间约2-5秒，具体取决于图片大小和网络状况</li>
              <li>• 提供花卉种属可减少约300-500ms的识别时间</li>
              <li>• 诊断结果包含疾病信息、特征匹配详情和推理过程</li>
            </ul>
          </div>
        )}
      </Form>
    </div>
  );
};

/**
 * 使用示例：
 *
 * ```tsx
 * import { DiagnosisForm } from '@/components/diagnosis/DiagnosisForm';
 *
 * function DiagnosisPage() {
 *   const [genus, setGenus] = useState<FlowerGenus | undefined>();
 *   const [selectedFile, setSelectedFile] = useState<File | null>(null);
 *   const [diagnosing, setDiagnosing] = useState(false);
 *
 *   const handleDiagnose = async () => {
 *     if (!selectedFile) return;
 *     setDiagnosing(true);
 *     // 调用诊断API
 *     // ...
 *     setDiagnosing(false);
 *   };
 *
 *   const handleReset = () => {
 *     setSelectedFile(null);
 *     setGenus(undefined);
 *   };
 *
 *   return (
 *     <DiagnosisForm
 *       flowerGenus={genus}
 *       onGenusChange={setGenus}
 *       onDiagnose={handleDiagnose}
 *       onReset={handleReset}
 *       diagnosing={diagnosing}
 *       hasImage={!!selectedFile}
 *     />
 *   );
 * }
 * ```
 */
