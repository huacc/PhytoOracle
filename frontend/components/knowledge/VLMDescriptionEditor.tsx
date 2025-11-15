/**
 * PhytoOracle VLM描述编辑器组件
 * 用于编辑VLM可理解的描述（影像学描述、日常用语、空间定位）
 */

import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Space, Card } from 'antd';
import { SaveOutlined, CloseOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { VLMDescription } from '@/types';

const { TextArea } = Input;

/**
 * VLMDescriptionEditor 组件属性
 */
interface VLMDescriptionEditorProps {
  /** 初始VLM描述数据 */
  initialValue?: VLMDescription;
  /** 是否只读 */
  readOnly?: boolean;
  /** 保存回调 */
  onSave?: (description: VLMDescription) => void;
  /** 取消回调 */
  onCancel?: () => void;
}

/**
 * VLM描述编辑器组件
 *
 * 功能：
 * 1. 编辑影像学描述
 * 2. 编辑日常用语描述
 * 3. 编辑空间定位方法
 * 4. 表单验证
 * 5. 保存和取消操作
 *
 * @param props - 组件属性
 * @returns React组件
 */
export const VLMDescriptionEditor: React.FC<VLMDescriptionEditorProps> = ({
  initialValue,
  readOnly = false,
  onSave,
  onCancel,
}) => {
  const [form] = Form.useForm<VLMDescription>();

  /**
   * 初始化表单值
   */
  useEffect(() => {
    if (initialValue) {
      form.setFieldsValue(initialValue);
    }
  }, [initialValue, form]);

  /**
   * 处理保存
   */
  const handleSave = async () => {
    try {
      // 验证表单
      const values = await form.validateFields();

      // 调用保存回调
      if (onSave) {
        onSave(values);
      }
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  /**
   * 处理取消
   */
  const handleCancel = () => {
    // 重置表单
    form.resetFields();

    // 调用取消回调
    if (onCancel) {
      onCancel();
    }
  };

  return (
    <Card size="small" className="vlm-description-editor">
      <Form
        form={form}
        layout="vertical"
        initialValues={initialValue}
        disabled={readOnly}
      >
        {/* 影像学描述 */}
        <Form.Item
          name="imaging_description"
          label={
            <span>
              <InfoCircleOutlined className="mr-1 text-blue-500" />
              影像学描述
            </span>
          }
          rules={[
            { required: true, message: '请输入影像学描述' },
            { min: 10, message: '描述至少需要10个字符' },
          ]}
          tooltip="医学/植物病理学的专业描述，使用科学术语"
        >
          <TextArea
            placeholder="例如：组织坏死形成的黑色或褐色斑点，边界清晰，直径2-5mm"
            autoSize={{ minRows: 3, maxRows: 6 }}
            showCount
            maxLength={500}
          />
        </Form.Item>

        {/* 日常用语 */}
        <Form.Item
          name="everyday_language"
          label={
            <span>
              <InfoCircleOutlined className="mr-1 text-blue-500" />
              日常用语
            </span>
          }
          rules={[
            { required: true, message: '请输入日常用语描述' },
            { min: 10, message: '描述至少需要10个字符' },
          ]}
          tooltip="生活化的比喻和视觉隐喻，帮助VLM理解"
        >
          <TextArea
            placeholder="例如：像被香烟烫过留下的焦痕，像纸张被火星烧出的小洞边缘"
            autoSize={{ minRows: 3, maxRows: 6 }}
            showCount
            maxLength={500}
          />
        </Form.Item>

        {/* 空间定位方法 */}
        <Form.Item
          name="spatial_positioning"
          label={
            <span>
              <InfoCircleOutlined className="mr-1 text-blue-500" />
              空间定位方法
            </span>
          }
          rules={[
            { min: 10, message: '描述至少需要10个字符' },
          ]}
          tooltip="位置、大小、范围的量化描述"
        >
          <TextArea
            placeholder="例如：从病斑中心向外0.5-2mm的环状区域，主要分布在叶片主体"
            autoSize={{ minRows: 3, maxRows: 6 }}
            showCount
            maxLength={500}
          />
        </Form.Item>

        {/* 操作按钮 */}
        {!readOnly && (
          <Form.Item className="mb-0">
            <Space>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSave}
              >
                保存
              </Button>
              <Button
                icon={<CloseOutlined />}
                onClick={handleCancel}
              >
                取消
              </Button>
            </Space>
          </Form.Item>
        )}
      </Form>

      {/* 帮助提示 */}
      <div className="mt-4 p-3 bg-blue-50 rounded text-sm text-blue-700">
        <p className="font-medium mb-2">编辑提示：</p>
        <ul className="list-disc list-inside space-y-1">
          <li>影像学描述：使用科学术语，准确描述病害特征</li>
          <li>日常用语：使用生活化的比喻，帮助VLM建立视觉联系</li>
          <li>空间定位：量化位置、大小、范围，提高识别精度</li>
        </ul>
      </div>
    </Card>
  );
};

export default VLMDescriptionEditor;

/**
 * 示例用法：
 *
 * import { VLMDescriptionEditor } from '@/components/knowledge';
 * import { VLMDescription } from '@/types';
 *
 * const initialDescription: VLMDescription = {
 *   imaging_description: '病斑周围有明显的黄色晕染区域',
 *   everyday_language: '像月亮周围的黄色光晕',
 *   spatial_positioning: '从病斑中心向外0.5-2mm的环状区域',
 * };
 *
 * function MyComponent() {
 *   return (
 *     <VLMDescriptionEditor
 *       initialValue={initialDescription}
 *       readOnly={false}
 *       onSave={(description) => {
 *         console.log('保存描述:', description);
 *       }}
 *       onCancel={() => {
 *         console.log('取消编辑');
 *       }}
 *     />
 *   );
 * }
 */
