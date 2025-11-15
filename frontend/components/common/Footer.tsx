/**
 * PhytoOracle Footer 页脚组件
 * 应用底部页脚，包含版权信息、链接等
 */

'use client';

import React from 'react';
import { Layout } from 'antd';
import { GithubOutlined, MailOutlined } from '@ant-design/icons';
import { APP_INFO } from '@/constants';

const { Footer: AntFooter } = Layout;

/**
 * Footer 组件属性
 */
export interface FooterProps {
  /** 是否显示链接 */
  showLinks?: boolean;
  /** 自定义类名 */
  className?: string;
}

/**
 * Footer 页脚组件
 *
 * @example
 * <Footer showLinks />
 */
export const Footer: React.FC<FooterProps> = ({ showLinks = true, className = '' }) => {
  const currentYear = new Date().getFullYear();

  return (
    <AntFooter className={`bg-gray-50 text-center ${className}`}>
      {/* 链接区域 */}
      {showLinks && (
        <div className="mb-4 flex justify-center gap-6 text-gray-600">
          <a
            href="https://github.com/phytooracle/phytooracle"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 transition-colors hover:text-primary-600"
          >
            <GithubOutlined />
            <span>GitHub</span>
          </a>
          <a
            href="mailto:support@phytooracle.com"
            className="flex items-center gap-1 transition-colors hover:text-primary-600"
          >
            <MailOutlined />
            <span>技术支持</span>
          </a>
          <a
            href="/docs"
            className="transition-colors hover:text-primary-600"
          >
            文档
          </a>
          <a
            href="/about"
            className="transition-colors hover:text-primary-600"
          >
            关于
          </a>
        </div>
      )}

      {/* 版权信息 */}
      <div className="text-sm text-gray-500">
        <p>
          {APP_INFO.NAME} v{APP_INFO.VERSION} - {APP_INFO.DESCRIPTION}
        </p>
        <p className="mt-1">
          Copyright © {currentYear} {APP_INFO.AUTHOR}. All rights reserved.
        </p>
      </div>
    </AntFooter>
  );
};
