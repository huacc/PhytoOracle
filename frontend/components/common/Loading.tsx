/**
 * PhytoOracle Loading 加载组件
 * 提供全局和局部加载状态显示
 */

'use client';

import React from 'react';
import { Spin } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

/**
 * Loading 组件属性
 */
export interface LoadingProps {
  /** 是否显示加载状态 */
  loading?: boolean;
  /** 加载提示文字 */
  tip?: string;
  /** 尺寸 */
  size?: 'small' | 'default' | 'large';
  /** 是否全屏 */
  fullscreen?: boolean;
  /** 子元素（局部加载时使用） */
  children?: React.ReactNode;
  /** 自定义图标 */
  indicator?: React.ReactElement;
  /** 延迟显示加载效果的时间（毫秒） */
  delay?: number;
}

/**
 * Loading 加载组件
 *
 * @example
 * // 全屏加载
 * <Loading loading={true} fullscreen tip="加载中..." />
 *
 * @example
 * // 局部加载
 * <Loading loading={isLoading} tip="处理中...">
 *   <YourContent />
 * </Loading>
 */
export const Loading: React.FC<LoadingProps> = ({
  loading = true,
  tip,
  size = 'default',
  fullscreen = false,
  children,
  indicator,
  delay = 0,
}) => {
  // 默认图标
  const defaultIndicator = <LoadingOutlined style={{ fontSize: size === 'large' ? 48 : size === 'small' ? 16 : 24 }} spin />;

  // 全屏加载
  if (fullscreen && loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/80 backdrop-blur-sm">
        <div className="text-center">
          <Spin
            indicator={indicator || defaultIndicator}
            size={size}
            tip={tip}
            delay={delay}
          />
        </div>
      </div>
    );
  }

  // 局部加载
  if (children) {
    return (
      <Spin
        spinning={loading}
        indicator={indicator || defaultIndicator}
        size={size}
        tip={tip}
        delay={delay}
      >
        {children}
      </Spin>
    );
  }

  // 简单加载指示器
  return (
    <div className="flex items-center justify-center p-8">
      <Spin
        indicator={indicator || defaultIndicator}
        size={size}
        tip={tip}
        delay={delay}
      />
    </div>
  );
};

/**
 * 页面级加载组件
 * 用于整个页面的加载状态
 */
export const PageLoading: React.FC<{ tip?: string }> = ({ tip = '加载中...' }) => {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Loading size="large" tip={tip} />
    </div>
  );
};
