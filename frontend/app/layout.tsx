/**
 * PhytoOracle 根布局组件
 * Next.js 15 App Router 根布局
 */

import type { Metadata } from 'next';
import { AntdRegistry } from '@ant-design/nextjs-registry';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import './globals.css';

export const metadata: Metadata = {
  title: 'PhytoOracle - 花卉疾病诊断系统',
  description: '基于本体建模和VLM视觉理解的花卉疾病诊断系统',
  keywords: ['花卉', '疾病诊断', '本体建模', 'VLM', '人工智能'],
  authors: [{ name: 'PhytoOracle Team' }],
  viewport: 'width=device-width, initial-scale=1',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>
        {/* Ant Design 样式注册（支持 SSR） */}
        <AntdRegistry>
          {/* Ant Design 配置提供者 */}
          <ConfigProvider
            locale={zhCN}
            theme={{
              token: {
                colorPrimary: '#1890ff',
                colorSuccess: '#52c41a',
                colorWarning: '#faad14',
                colorError: '#ff4d4f',
                borderRadius: 2,
                fontSize: 14,
              },
              components: {
                Layout: {
                  headerBg: '#ffffff',
                  headerHeight: 64,
                },
                Menu: {
                  horizontalItemSelectedColor: '#1890ff',
                },
              },
            }}
          >
            {children}
          </ConfigProvider>
        </AntdRegistry>
      </body>
    </html>
  );
}
