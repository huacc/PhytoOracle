/**
 * Next.js 15 配置文件
 * PhytoOracle 项目前端配置
 */

import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // 启用 React 严格模式
  reactStrictMode: true,

  // 输出配置
  output: 'standalone',

  // 环境变量配置
  env: {
    // 可在客户端访问的环境变量（使用 process.env.NEXT_PUBLIC_ 前缀）
    NEXT_PUBLIC_APP_NAME: 'PhytoOracle',
    NEXT_PUBLIC_APP_VERSION: '1.0.0',
  },

  // 图片优化配置
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/storage/**',
      },
    ],
    formats: ['image/avif', 'image/webp'],
  },

  // API 代理配置（开发环境）
  async rewrites() {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

    return [
      {
        source: '/api/v1/:path*',
        destination: `${apiBaseUrl}/api/v1/:path*`,
      },
    ];
  },

  // 编译配置
  compiler: {
    // 移除 console.log（仅生产环境）
    removeConsole: process.env.NODE_ENV === 'production' ? {
      exclude: ['error', 'warn'],
    } : false,
  },

  // Webpack 配置扩展
  webpack: (config, { isServer }) => {
    // 处理 .node 文件
    config.externals = config.externals || [];

    if (!isServer) {
      // 客户端特定配置
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }

    return config;
  },

  // TypeScript 配置
  typescript: {
    // 生产构建时忽略 TypeScript 错误（仅开发时检查）
    ignoreBuildErrors: false,
  },

  // ESLint 配置
  eslint: {
    // 生产构建时忽略 ESLint 错误（仅开发时检查）
    ignoreDuringBuilds: false,
  },

  // 实验性功能
  experimental: {
    // 启用服务端组件优化
    serverActions: {
      bodySizeLimit: '10mb', // 文件上传大小限制
    },
  },
};

export default nextConfig;
