/**
 * PhytoOracle - 图片上传组件
 * 功能：支持拖拽上传、点击上传、图片预览
 *
 * @author PhytoOracle Team
 * @version 1.0.0
 */

'use client';

import React, { useState, useCallback, useRef } from 'react';
import { Upload, message } from 'antd';
import { InboxOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd/es/upload/interface';
import { validateImageFile, formatFileSize } from '@/utils';
import { UPLOAD_CONFIG } from '@/constants';
import Image from 'next/image';

/**
 * ImageUploader 组件属性
 */
export interface ImageUploaderProps {
  /** 选择文件后的回调 */
  onFileSelect?: (file: File | null) => void;
  /** 已选择的文件 */
  value?: File | null;
  /** 是否禁用 */
  disabled?: boolean;
  /** 自定义样式 */
  className?: string;
}

/**
 * 图片上传组件
 *
 * 功能：
 * - 支持拖拽上传和点击上传
 * - 实时图片预览
 * - 文件格式验证（JPG/PNG/HEIC/WEBP）
 * - 文件大小验证（最大10MB）
 * - 显示文件信息（名称、大小）
 *
 * @param props - 组件属性
 * @returns 图片上传组件
 */
export const ImageUploader: React.FC<ImageUploaderProps> = ({
  onFileSelect,
  value,
  disabled = false,
  className = '',
}) => {
  // 状态：预览图片URL
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  // 状态：文件列表（Ant Design Upload组件需要）
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  /**
   * 处理文件变更
   * @param file - 上传的文件
   */
  const handleFileChange = useCallback(
    (file: File | null) => {
      // 调用父组件回调
      onFileSelect?.(file);

      // 更新预览
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          setPreviewUrl(e.target?.result as string);
        };
        reader.readAsDataURL(file);

        // 更新文件列表
        setFileList([
          {
            uid: '-1',
            name: file.name,
            status: 'done',
            size: file.size,
            type: file.type,
          } as UploadFile,
        ]);
      } else {
        // 清空预览
        setPreviewUrl(null);
        setFileList([]);
      }
    },
    [onFileSelect]
  );

  /**
   * 在上传前验证文件
   * @param file - 待上传的文件
   * @returns false表示不自动上传，由组件自行处理
   */
  const beforeUpload: UploadProps['beforeUpload'] = (file) => {
    // 验证文件
    const validation = validateImageFile(file);

    if (!validation.valid) {
      message.error(validation.error || '文件验证失败');
      return Upload.LIST_IGNORE; // 不添加到文件列表
    }

    // 文件验证通过，处理文件
    handleFileChange(file);

    // 返回false阻止自动上传，由组件自行管理
    return false;
  };

  /**
   * 删除已选择的文件
   */
  const handleRemove = () => {
    handleFileChange(null);
  };

  /**
   * 自定义上传区域渲染
   */
  const customRender = () => {
    // 如果已选择文件，显示预览区域
    if (value && previewUrl) {
      return (
        <div className="relative">
          {/* 图片预览 */}
          <div className="relative w-full h-[400px] bg-gray-50 rounded-lg overflow-hidden border-2 border-gray-200">
            <Image
              src={previewUrl}
              alt="预览图片"
              fill
              style={{ objectFit: 'contain' }}
              className="transition-transform hover:scale-105 duration-300"
            />
          </div>

          {/* 文件信息 */}
          <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <EyeOutlined className="text-blue-500 text-lg" />
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {value.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(value.size)}
                  </p>
                </div>
              </div>

              {/* 删除按钮 */}
              {!disabled && (
                <button
                  onClick={handleRemove}
                  className="px-3 py-1.5 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                  type="button"
                >
                  <DeleteOutlined className="mr-1" />
                  移除
                </button>
              )}
            </div>
          </div>
        </div>
      );
    }

    // 默认显示上传区域
    return null;
  };

  return (
    <div className={className}>
      <Upload.Dragger
        name="image"
        multiple={false}
        fileList={fileList}
        beforeUpload={beforeUpload}
        onRemove={handleRemove}
        disabled={disabled}
        accept={Object.values(UPLOAD_CONFIG.MIME_TYPES).join(',')}
        showUploadList={false}
        className={value ? 'hidden' : ''}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined style={{ fontSize: 64, color: '#1890ff' }} />
        </p>
        <p className="ant-upload-text text-lg font-medium">
          点击或拖拽图片到此处上传
        </p>
        <p className="ant-upload-hint text-gray-500">
          支持格式：{UPLOAD_CONFIG.ALLOWED_FORMATS.map((f) => f.toUpperCase()).join(' / ')}
          <br />
          文件大小限制：最大 {UPLOAD_CONFIG.MAX_SIZE}MB
        </p>
      </Upload.Dragger>

      {/* 自定义预览区域 */}
      {customRender()}
    </div>
  );
};

/**
 * 使用示例：
 *
 * ```tsx
 * import { ImageUploader } from '@/components/diagnosis/ImageUploader';
 *
 * function DiagnosisPage() {
 *   const [selectedFile, setSelectedFile] = useState<File | null>(null);
 *
 *   return (
 *     <ImageUploader
 *       value={selectedFile}
 *       onFileSelect={setSelectedFile}
 *       disabled={false}
 *     />
 *   );
 * }
 * ```
 */
