/**
 * PhytoOracle Layout 布局组件
 * 应用主布局，包含Header、Content、Footer
 */

'use client';

import React, { ReactNode } from 'react';
import { Layout as AntLayout } from 'antd';
import { Header } from './Header';
import { Footer } from './Footer';
import { ErrorBoundary } from './ErrorBoundary';
import { useAppStore } from '@/stores';

const { Content } = AntLayout;

/**
 * Layout 组件属性
 */
export interface LayoutProps {
  /** 子元素 */
  children: ReactNode;
  /** 是否显示Header */
  showHeader?: boolean;
  /** 是否显示Footer */
  showFooter?: boolean;
  /** 是否使用ErrorBoundary包裹 */
  useErrorBoundary?: boolean;
  /** 内容区域的自定义类名 */
  contentClassName?: string;
  /** 内容区域的最大宽度（tailwind class） */
  maxWidth?: string;
  /** 是否添加内边距 */
  padding?: boolean;
}

/**
 * Layout 主布局组件
 *
 * 提供应用的主要布局结构，包含Header、Content和Footer
 *
 * @example
 * // 基本用法
 * <Layout>
 *   <YourPageContent />
 * </Layout>
 *
 * @example
 * // 自定义配置
 * <Layout
 *   showHeader
 *   showFooter
 *   maxWidth="max-w-7xl"
 *   padding
 * >
 *   <YourPageContent />
 * </Layout>
 *
 * @example
 * // 不显示Header和Footer（登录页等）
 * <Layout showHeader={false} showFooter={false}>
 *   <LoginPage />
 * </Layout>
 */
export const Layout: React.FC<LayoutProps> = ({
  children,
  showHeader = true,
  showFooter = true,
  useErrorBoundary = true,
  contentClassName = '',
  maxWidth = 'max-w-screen-2xl',
  padding = true,
}) => {
  // 内容区域的样式类
  const contentClasses = [
    'min-h-screen',
    showHeader ? 'pt-16' : '', // Header高度补偿
    padding ? 'px-4 py-6 md:px-6 md:py-8' : '',
    contentClassName,
  ].filter(Boolean).join(' ');

  // 渲染内容
  const renderContent = () => (
    <Content className={contentClasses}>
      <div className={`mx-auto ${maxWidth}`}>
        {children}
      </div>
    </Content>
  );

  return (
    <AntLayout className="min-h-screen bg-gray-50">
      {/* Header 导航栏 */}
      {showHeader && <Header showUser showSidebarToggle />}

      {/* Content 内容区域 */}
      {useErrorBoundary ? (
        <ErrorBoundary>{renderContent()}</ErrorBoundary>
      ) : (
        renderContent()
      )}

      {/* Footer 页脚 */}
      {showFooter && <Footer showLinks />}
    </AntLayout>
  );
};

/**
 * 简单布局组件
 * 适用于登录页、404页等不需要Header/Footer的页面
 */
export const SimpleLayout: React.FC<{ children: ReactNode; className?: string }> = ({
  children,
  className = '',
}) => {
  return (
    <div className={`flex min-h-screen items-center justify-center bg-gray-50 ${className}`}>
      <ErrorBoundary>{children}</ErrorBoundary>
    </div>
  );
};

/**
 * 卡片布局组件
 * 内容区域带白色卡片背景的布局
 */
export const CardLayout: React.FC<LayoutProps> = (props) => {
  const { children, ...rest } = props;

  return (
    <Layout {...rest}>
      <div className="rounded-lg bg-white p-6 shadow-sm">
        {children}
      </div>
    </Layout>
  );
};
