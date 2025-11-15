/**
 * PhytoOracle 用户认证状态管理
 * 使用 Zustand 管理全局认证状态
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { STORAGE_KEYS } from '@/constants';
import { api, adminApi } from '@/lib';

/**
 * 用户信息接口
 */
export interface UserInfo {
  /** 用户名 */
  username: string;
  /** 角色 */
  role: string;
  /** 其他用户信息 */
  [key: string]: any;
}

/**
 * 认证状态接口
 */
interface AuthState {
  /** 是否已登录 */
  isAuthenticated: boolean;
  /** 用户信息 */
  user: UserInfo | null;
  /** 认证Token */
  token: string | null;
  /** 登录方法 */
  login: (username: string, password: string) => Promise<void>;
  /** 登出方法 */
  logout: () => Promise<void>;
  /** 设置用户信息 */
  setUser: (user: UserInfo) => void;
  /** 设置Token */
  setToken: (token: string) => void;
  /** 清除认证信息 */
  clearAuth: () => void;
}

/**
 * 认证状态Store
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      user: null,
      token: null,

      /**
       * 登录
       */
      login: async (username: string, password: string) => {
        try {
          const response = await adminApi.login(username, password);

          // 保存Token到API客户端
          api.setAuthToken(response.access_token);

          // 更新状态
          set({
            isAuthenticated: true,
            user: response.user_info,
            token: response.access_token,
          });
        } catch (error) {
          // 清除认证信息
          get().clearAuth();
          throw error;
        }
      },

      /**
       * 登出
       */
      logout: async () => {
        try {
          await adminApi.logout();
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          // 无论是否成功，都清除本地认证信息
          get().clearAuth();
        }
      },

      /**
       * 设置用户信息
       */
      setUser: (user: UserInfo) => {
        set({ user, isAuthenticated: true });
      },

      /**
       * 设置Token
       */
      setToken: (token: string) => {
        api.setAuthToken(token);
        set({ token, isAuthenticated: true });
      },

      /**
       * 清除认证信息
       */
      clearAuth: () => {
        api.clearAuthToken();
        set({
          isAuthenticated: false,
          user: null,
          token: null,
        });
      },
    }),
    {
      name: STORAGE_KEYS.USER_INFO, // localStorage key
      partialize: (state) => ({
        // 只持久化必要的字段
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
