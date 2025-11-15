/**
 * PhytoOracle 应用全局状态管理
 * 管理应用级别的全局状态（主题、语言、加载状态等）
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { STORAGE_KEYS } from '@/constants';
import { Theme, LoadingState } from '@/types';

/**
 * 应用状态接口
 */
interface AppState {
  /** 主题 */
  theme: Theme;
  /** 语言 */
  language: 'zh-CN' | 'en-US';
  /** 全局加载状态 */
  loading: LoadingState;
  /** 侧边栏折叠状态 */
  sidebarCollapsed: boolean;
  /** 全局错误信息 */
  globalError: string | null;

  /** 设置主题 */
  setTheme: (theme: Theme) => void;
  /** 设置语言 */
  setLanguage: (language: 'zh-CN' | 'en-US') => void;
  /** 设置加载状态 */
  setLoading: (loading: LoadingState) => void;
  /** 切换侧边栏 */
  toggleSidebar: () => void;
  /** 设置全局错误 */
  setGlobalError: (error: string | null) => void;
  /** 清除全局错误 */
  clearGlobalError: () => void;
}

/**
 * 应用状态Store
 */
export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      theme: 'light',
      language: 'zh-CN',
      loading: 'idle',
      sidebarCollapsed: false,
      globalError: null,

      /**
       * 设置主题
       */
      setTheme: (theme: Theme) => {
        set({ theme });
        // 可以在这里添加主题切换的副作用（如更新document.body的class）
        if (typeof document !== 'undefined') {
          document.body.className = theme;
        }
      },

      /**
       * 设置语言
       */
      setLanguage: (language: 'zh-CN' | 'en-US') => {
        set({ language });
      },

      /**
       * 设置加载状态
       */
      setLoading: (loading: LoadingState) => {
        set({ loading });
      },

      /**
       * 切换侧边栏
       */
      toggleSidebar: () => {
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }));
      },

      /**
       * 设置全局错误
       */
      setGlobalError: (error: string | null) => {
        set({ globalError: error });
      },

      /**
       * 清除全局错误
       */
      clearGlobalError: () => {
        set({ globalError: null });
      },
    }),
    {
      name: STORAGE_KEYS.THEME, // localStorage key
      partialize: (state) => ({
        // 只持久化主题和语言
        theme: state.theme,
        language: state.language,
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
);
