/**
 * PhytoOracle 图片缩略图组件
 * 用于在批量诊断结果列表中展示图片缩略图
 */

'use client';

import React from 'react';
import { Image, Badge, Tag } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  PictureOutlined,
} from '@ant-design/icons';

/**
 * 诊断状态类型
 */
export type DiagnosisStatusType = 'success' | 'failed' | 'processing' | 'pending';

/**
 * 图片缩略图组件的Props
 */
export interface ImageThumbnailProps {
  /** 图片URL或文件对象 */
  src: string | File;
  /** 文件名 */
  fileName?: string;
  /** 诊断状态 */
  status?: DiagnosisStatusType;
  /** 是否选中 */
  selected?: boolean;
  /** 点击回调 */
  onClick?: () => void;
  /** 缩略图尺寸 */
  size?: number;
  /** 是否显示状态标记 */
  showStatus?: boolean;
}

/**
 * 图片缩略图组件
 *
 * 功能：
 * - 显示图片缩略图
 * - 显示诊断状态标记（成功/失败/处理中/待处理）
 * - 支持点击选中
 * - 支持预览
 */
export const ImageThumbnail: React.FC<ImageThumbnailProps> = ({
  src,
  fileName,
  status,
  selected = false,
  onClick,
  size = 80,
  showStatus = true,
}) => {
  // 处理图片URL
  const [imageUrl, setImageUrl] = React.useState<string>('');

  React.useEffect(() => {
    if (typeof src === 'string') {
      setImageUrl(src);
    } else {
      // 如果是File对象，创建URL
      const url = URL.createObjectURL(src);
      setImageUrl(url);

      // 清理函数，释放URL
      return () => URL.revokeObjectURL(url);
    }
  }, [src]);

  /**
   * 获取状态图标
   */
  const getStatusIcon = () => {
    switch (status) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'processing':
        return <SyncOutlined spin style={{ color: '#1890ff' }} />;
      case 'pending':
        return null;
      default:
        return null;
    }
  };

  /**
   * 获取状态徽章颜色
   */
  const getStatusBadgeColor = (): string => {
    switch (status) {
      case 'success':
        return '#52c41a';
      case 'failed':
        return '#ff4d4f';
      case 'processing':
        return '#1890ff';
      case 'pending':
        return '#d9d9d9';
      default:
        return 'transparent';
    }
  };

  /**
   * 获取状态文本
   */
  const getStatusText = (): string => {
    switch (status) {
      case 'success':
        return '成功';
      case 'failed':
        return '失败';
      case 'processing':
        return '诊断中';
      case 'pending':
        return '待诊断';
      default:
        return '';
    }
  };

  return (
    <div
      className={`
        inline-block
        cursor-pointer
        transition-all
        duration-200
        ${selected ? 'ring-2 ring-blue-500 ring-offset-2' : ''}
        hover:opacity-80
      `}
      onClick={onClick}
      style={{ width: size, height: size }}
    >
      <Badge
        count={showStatus && status ? getStatusIcon() : 0}
        offset={[-5, 5]}
        style={{
          backgroundColor: getStatusBadgeColor(),
          borderRadius: '50%',
        }}
      >
        <div
          className="relative overflow-hidden rounded bg-gray-100 flex items-center justify-center"
          style={{ width: size, height: size }}
        >
          {imageUrl ? (
            <Image
              src={imageUrl}
              alt={fileName || '图片'}
              preview={{
                mask: <div>预览</div>,
              }}
              className="object-cover w-full h-full"
              fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            />
          ) : (
            <PictureOutlined style={{ fontSize: size / 3, color: '#bfbfbf' }} />
          )}

          {/* 状态标签（底部显示） */}
          {showStatus && status && (
            <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white text-xs text-center py-0.5">
              {getStatusText()}
            </div>
          )}
        </div>
      </Badge>
    </div>
  );
};

export default ImageThumbnail;

/**
 * 组件使用示例：
 *
 * ```tsx
 * import { ImageThumbnail } from '@/components/batch-diagnosis';
 *
 * // 使用字符串URL
 * <ImageThumbnail
 *   src="https://example.com/image.jpg"
 *   fileName="rose_001.jpg"
 *   status="success"
 *   selected={true}
 *   onClick={() => console.log('clicked')}
 *   size={100}
 *   showStatus={true}
 * />
 *
 * // 使用File对象
 * <ImageThumbnail
 *   src={fileObject}
 *   status="processing"
 *   size={80}
 * />
 * ```
 */
