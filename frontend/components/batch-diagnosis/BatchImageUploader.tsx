/**
 * PhytoOracle 批量图片上传组件
 * 支持拖拽上传、批量选择、预览和删除功能
 */

'use client';

import React, { useState, useCallback } from 'react';
import { Upload, Button, message, Card, Image, Space, Typography, Alert } from 'antd';
import {
  InboxOutlined,
  DeleteOutlined,
  PictureOutlined,
  CloudUploadOutlined,
} from '@ant-design/icons';
import type { UploadProps, UploadFile, UploadChangeParam } from 'antd/es/upload';
import { validateImageFile } from '@/utils';
import { UPLOAD_CONFIG } from '@/constants';

const { Dragger } = Upload;
const { Text, Title } = Typography;

/**
 * 批量图片上传组件的Props
 */
export interface BatchImageUploaderProps {
  /** 已选择的文件列表 */
  fileList?: UploadFile[];
  /** 文件列表变化回调 */
  onChange?: (fileList: UploadFile[]) => void;
  /** 最大文件数量 */
  maxCount?: number;
  /** 是否禁用 */
  disabled?: boolean;
  /** 是否显示上传区域 */
  showUploader?: boolean;
}

/**
 * 批量图片上传组件
 *
 * 功能：
 * - 支持拖拽上传和点击选择
 * - 支持批量选择（最多50张）
 * - 图片预览（缩略图网格）
 * - 单个图片删除
 * - 格式验证（JPG/PNG/HEIC/WEBP）
 * - 大小验证（每个最大10MB）
 */
export const BatchImageUploader: React.FC<BatchImageUploaderProps> = ({
  fileList = [],
  onChange,
  maxCount = 50,
  disabled = false,
  showUploader = true,
}) => {
  // 预览图片URL的state
  const [previewUrls, setPreviewUrls] = useState<Map<string, string>>(new Map());

  /**
   * 文件列表变化处理
   */
  const handleChange: UploadProps['onChange'] = useCallback(
    (info: UploadChangeParam<UploadFile>) => {
      let newFileList = [...info.fileList];

      // 限制文件数量
      if (newFileList.length > maxCount) {
        message.warning(`最多只能上传 ${maxCount} 张图片`);
        newFileList = newFileList.slice(0, maxCount);
      }

      onChange?.(newFileList);
    },
    [maxCount, onChange]
  );

  /**
   * 上传前的文件验证
   */
  const beforeUpload: UploadProps['beforeUpload'] = useCallback(
    (file: File) => {
      // 使用工具函数验证文件
      const validation = validateImageFile(file);
      if (!validation.valid) {
        message.error(validation.error);
        return Upload.LIST_IGNORE; // 忽略不合法的文件
      }

      // 检查文件数量限制
      if (fileList.length >= maxCount) {
        message.warning(`最多只能上传 ${maxCount} 张图片`);
        return Upload.LIST_IGNORE;
      }

      // 生成预览URL
      const url = URL.createObjectURL(file);
      setPreviewUrls((prev) => {
        const newMap = new Map(prev);
        newMap.set(file.name, url);
        return newMap;
      });

      // 阻止自动上传，仅保存文件
      return false;
    },
    [fileList.length, maxCount]
  );

  /**
   * 删除单个文件
   */
  const handleRemove = useCallback(
    (file: UploadFile) => {
      // 清理预览URL
      const fileName = file.name;
      const url = previewUrls.get(fileName);
      if (url) {
        URL.revokeObjectURL(url);
        setPreviewUrls((prev) => {
          const newMap = new Map(prev);
          newMap.delete(fileName);
          return newMap;
        });
      }

      // 更新文件列表
      const newFileList = fileList.filter((item) => item.uid !== file.uid);
      onChange?.(newFileList);
    },
    [fileList, onChange, previewUrls]
  );

  /**
   * 清空所有文件
   */
  const handleClearAll = useCallback(() => {
    // 清理所有预览URL
    previewUrls.forEach((url) => URL.revokeObjectURL(url));
    setPreviewUrls(new Map());

    // 清空文件列表
    onChange?.([]);
    message.success('已清空所有图片');
  }, [onChange, previewUrls]);

  // 上传配置
  const uploadProps: UploadProps = {
    multiple: true,
    accept: UPLOAD_CONFIG.ALLOWED_FORMATS.join(','),
    fileList,
    onChange: handleChange,
    beforeUpload,
    onRemove: handleRemove,
    showUploadList: false, // 自定义文件列表展示
    disabled,
  };

  return (
    <div className="batch-image-uploader">
      {/* 上传区域 */}
      {showUploader && (
        <Dragger {...uploadProps} className="mb-4">
          <p className="ant-upload-drag-icon">
            <InboxOutlined style={{ color: '#1890ff', fontSize: 48 }} />
          </p>
          <p className="ant-upload-text">
            点击或拖拽图片到此区域上传
          </p>
          <p className="ant-upload-hint">
            支持批量上传，单次最多 {maxCount} 张图片
            <br />
            支持格式：JPG、PNG、HEIC、WEBP，单个文件最大 {UPLOAD_CONFIG.MAX_SIZE / 1024 / 1024}MB
          </p>
        </Dragger>
      )}

      {/* 文件列表提示 */}
      {fileList.length > 0 && (
        <Alert
          message={
            <Space>
              <PictureOutlined />
              <Text>
                已选择 <Text strong>{fileList.length}</Text> 张图片
                {fileList.length >= maxCount && (
                  <Text type="warning"> （已达到最大数量）</Text>
                )}
              </Text>
            </Space>
          }
          type="info"
          showIcon={false}
          action={
            <Button size="small" danger onClick={handleClearAll} disabled={disabled}>
              清空所有
            </Button>
          }
          className="mb-4"
        />
      )}

      {/* 图片预览网格 */}
      {fileList.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {fileList.map((file) => {
            const previewUrl = previewUrls.get(file.name) || '';

            return (
              <Card
                key={file.uid}
                hoverable
                className="relative"
                bodyStyle={{ padding: 0 }}
                cover={
                  <div className="relative w-full h-32 bg-gray-100 flex items-center justify-center overflow-hidden">
                    {previewUrl ? (
                      <Image
                        src={previewUrl}
                        alt={file.name}
                        preview={{
                          mask: <div>查看</div>,
                        }}
                        className="object-cover w-full h-full"
                      />
                    ) : (
                      <PictureOutlined style={{ fontSize: 32, color: '#bfbfbf' }} />
                    )}
                  </div>
                }
              >
                <div className="p-2">
                  {/* 文件名 */}
                  <Text
                    ellipsis={{ tooltip: file.name }}
                    className="text-xs block mb-1"
                  >
                    {file.name}
                  </Text>

                  {/* 文件大小 */}
                  <Text type="secondary" className="text-xs">
                    {file.size
                      ? `${(file.size / 1024).toFixed(1)} KB`
                      : '未知大小'}
                  </Text>

                  {/* 删除按钮 */}
                  <Button
                    type="text"
                    danger
                    size="small"
                    icon={<DeleteOutlined />}
                    onClick={() => handleRemove(file)}
                    disabled={disabled}
                    className="absolute top-1 right-1 bg-white bg-opacity-80 hover:bg-opacity-100"
                  >
                    删除
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* 空状态提示 */}
      {fileList.length === 0 && !showUploader && (
        <div className="text-center py-12 text-gray-400">
          <CloudUploadOutlined style={{ fontSize: 48 }} />
          <p className="mt-2">暂无图片，请先上传</p>
        </div>
      )}
    </div>
  );
};

export default BatchImageUploader;

/**
 * 组件使用示例：
 *
 * ```tsx
 * import { BatchImageUploader } from '@/components/batch-diagnosis';
 * import { useState } from 'react';
 * import type { UploadFile } from 'antd';
 *
 * function MyPage() {
 *   const [fileList, setFileList] = useState<UploadFile[]>([]);
 *
 *   return (
 *     <BatchImageUploader
 *       fileList={fileList}
 *       onChange={setFileList}
 *       maxCount={50}
 *       disabled={false}
 *       showUploader={true}
 *     />
 *   );
 * }
 * ```
 */
