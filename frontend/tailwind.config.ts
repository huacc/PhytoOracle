/**
 * Tailwind CSS 配置文件
 * 与 Ant Design 兼容的配置
 */

import type { Config } from 'tailwindcss';

const config: Config = {
  // 指定需要扫描的文件路径
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],

  // 主题配置
  theme: {
    extend: {
      // 颜色扩展（与 Ant Design 主题一致）
      colors: {
        primary: {
          50: '#e6f7ff',
          100: '#bae7ff',
          200: '#91d5ff',
          300: '#69c0ff',
          400: '#40a9ff',
          500: '#1890ff',  // Ant Design 主色
          600: '#096dd9',
          700: '#0050b3',
          800: '#003a8c',
          900: '#002766',
        },
        success: {
          DEFAULT: '#52c41a',
          light: '#95de64',
          dark: '#389e0d',
        },
        warning: {
          DEFAULT: '#faad14',
          light: '#ffc53d',
          dark: '#d48806',
        },
        error: {
          DEFAULT: '#ff4d4f',
          light: '#ff7875',
          dark: '#cf1322',
        },
      },

      // 字体家族
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'Noto Sans',
          'sans-serif',
          'Apple Color Emoji',
          'Segoe UI Emoji',
          'Segoe UI Symbol',
          'Noto Color Emoji',
        ],
      },

      // 间距扩展
      spacing: {
        '128': '32rem',
        '144': '36rem',
      },

      // 圆角扩展
      borderRadius: {
        'ant': '2px',  // Ant Design 默认圆角
      },

      // 阴影扩展
      boxShadow: {
        'ant-sm': '0 2px 8px rgba(0, 0, 0, 0.08)',
        'ant-md': '0 4px 12px rgba(0, 0, 0, 0.15)',
        'ant-lg': '0 6px 16px rgba(0, 0, 0, 0.12)',
      },

      // 背景图片
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },

      // 动画扩展
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'spin-slow': 'spin 3s linear infinite',
      },

      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },

  // 插件
  plugins: [],

  // 重要性前缀（避免与 Ant Design 样式冲突）
  important: false,

  // 禁用预检样式（Ant Design 有自己的重置样式）
  corePlugins: {
    preflight: true,
  },
};

export default config;
