/**
 * PhytoOracle Header 导航栏组件
 * 应用顶部导航栏，包含Logo、菜单、用户信息等
 */

'use client';

import React from 'react';
import { Layout, Menu, Avatar, Dropdown, Space, Button } from 'antd';
import {
  HomeOutlined,
  FileImageOutlined,
  FolderOpenOutlined,
  HistoryOutlined,
  DatabaseOutlined,
  BookOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuOutlined,
} from '@ant-design/icons';
import { useRouter, usePathname } from 'next/navigation';
import { MENU_ITEMS, APP_INFO, ROUTES } from '@/constants';
import { useAuthStore, useAppStore } from '@/stores';

const { Header: AntHeader } = Layout;

/**
 * Header 组件属性
 */
export interface HeaderProps {
  /** 是否显示用户信息 */
  showUser?: boolean;
  /** 是否显示侧边栏切换按钮 */
  showSidebarToggle?: boolean;
}

/**
 * Header 导航栏组件
 *
 * @example
 * <Header showUser showSidebarToggle />
 */
export const Header: React.FC<HeaderProps> = ({
  showUser = true,
  showSidebarToggle = false,
}) => {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, user, logout } = useAuthStore();
  const { toggleSidebar } = useAppStore();

  // 获取当前激活的菜单项
  const getCurrentMenuKey = (): string => {
    const menuItem = MENU_ITEMS.find((item) => pathname?.startsWith(item.path));
    return menuItem?.key || 'home';
  };

  // 菜单点击处理
  const handleMenuClick = (key: string): void => {
    const menuItem = MENU_ITEMS.find((item) => item.key === key);
    if (menuItem) {
      router.push(menuItem.path);
    }
  };

  // 用户下拉菜单项
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => {
        // TODO: 跳转到个人资料页
      },
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: async () => {
        await logout();
        router.push(ROUTES.LOGIN);
      },
    },
  ];

  return (
    <AntHeader className="fixed top-0 z-40 flex w-full items-center justify-between bg-white px-6 shadow-sm">
      {/* 左侧：Logo + 菜单 */}
      <div className="flex items-center gap-6">
        {/* 侧边栏切换按钮（移动端） */}
        {showSidebarToggle && (
          <Button
            type="text"
            icon={<MenuOutlined />}
            onClick={toggleSidebar}
            className="lg:hidden"
          />
        )}

        {/* Logo */}
        <div
          className="flex cursor-pointer items-center gap-2"
          onClick={() => router.push(ROUTES.HOME)}
        >
          <span className="text-2xl">🌸</span>
          <span className="text-lg font-bold text-primary-600">{APP_INFO.NAME}</span>
        </div>

        {/* 主导航菜单（桌面端） */}
        <Menu
          mode="horizontal"
          selectedKeys={[getCurrentMenuKey()]}
          className="hidden min-w-0 flex-1 border-0 lg:flex"
          items={MENU_ITEMS.map((item) => ({
            key: item.key,
            label: item.label,
            onClick: () => handleMenuClick(item.key),
          }))}
        />
      </div>

      {/* 右侧：用户信息 */}
      {showUser && (
        <div className="flex items-center gap-4">
          {isAuthenticated && user ? (
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Space className="cursor-pointer">
                <Avatar icon={<UserOutlined />} />
                <span className="hidden md:inline">{user.username}</span>
              </Space>
            </Dropdown>
          ) : (
            <Button type="primary" onClick={() => router.push(ROUTES.LOGIN)}>
              登录
            </Button>
          )}
        </div>
      )}
    </AntHeader>
  );
};
