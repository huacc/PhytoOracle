/**
 * PhytoOracle ErrorBoundary 错误边界组件
 * 捕获React组件树中的JavaScript错误，显示降级UI
 */

'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button, Result } from 'antd';

/**
 * ErrorBoundary 组件属性
 */
interface ErrorBoundaryProps {
  /** 子组件 */
  children: ReactNode;
  /** 降级UI（可选） */
  fallback?: ReactNode;
  /** 错误回调函数 */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

/**
 * ErrorBoundary 组件状态
 */
interface ErrorBoundaryState {
  /** 是否发生错误 */
  hasError: boolean;
  /** 错误对象 */
  error: Error | null;
  /** 错误信息 */
  errorInfo: ErrorInfo | null;
}

/**
 * ErrorBoundary 错误边界组件
 *
 * React错误边界组件，用于捕获组件树中的JavaScript错误
 * 并显示降级UI，防止整个应用崩溃
 *
 * @example
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 *
 * @example
 * // 自定义降级UI
 * <ErrorBoundary fallback={<CustomErrorPage />}>
 *   <YourComponent />
 * </ErrorBoundary>
 *
 * @example
 * // 错误日志上报
 * <ErrorBoundary onError={(error, errorInfo) => {
 *   logErrorToService(error, errorInfo);
 * }}>
 *   <YourComponent />
 * </ErrorBoundary>
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  /**
   * 当子组件抛出错误时调用
   * 更新state以显示降级UI
   */
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  /**
   * 错误被捕获后调用
   * 用于记录错误信息
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // 记录错误信息
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // 更新状态
    this.setState({
      error,
      errorInfo,
    });

    // 调用错误回调
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // 在生产环境可以上报到错误监控服务
    if (process.env.NODE_ENV === 'production') {
      // TODO: 集成错误监控服务（如Sentry）
      // logErrorToService(error, errorInfo);
    }
  }

  /**
   * 重置错误状态
   */
  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  /**
   * 刷新页面
   */
  handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    const { hasError, error, errorInfo } = this.state;
    const { children, fallback } = this.props;

    // 如果发生错误，显示降级UI
    if (hasError) {
      // 如果提供了自定义降级UI，使用它
      if (fallback) {
        return fallback;
      }

      // 默认降级UI
      return (
        <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
          <div className="w-full max-w-md">
            <Result
              status="error"
              title="页面出错了"
              subTitle="抱歉，页面加载时遇到了问题。您可以尝试重新加载页面。"
              extra={[
                <Button type="primary" key="reload" onClick={this.handleReload}>
                  刷新页面
                </Button>,
                <Button key="reset" onClick={this.handleReset}>
                  返回上一页
                </Button>,
              ]}
            >
              {/* 开发环境显示错误详情 */}
              {process.env.NODE_ENV === 'development' && error && (
                <div className="mt-6 text-left">
                  <details className="cursor-pointer rounded-lg bg-gray-100 p-4">
                    <summary className="font-semibold text-red-600">
                      错误详情（仅开发环境显示）
                    </summary>
                    <pre className="mt-2 overflow-auto text-xs text-gray-700">
                      {error.toString()}
                    </pre>
                    {errorInfo && (
                      <pre className="mt-2 overflow-auto text-xs text-gray-600">
                        {errorInfo.componentStack}
                      </pre>
                    )}
                  </details>
                </div>
              )}
            </Result>
          </div>
        </div>
      );
    }

    // 正常渲染子组件
    return children;
  }
}

/**
 * 函数式错误边界Hook（React 18+）
 * 注意：这只是一个示例，真正的错误边界需要使用Class组件
 */
export const useErrorHandler = () => {
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    if (error) {
      throw error;
    }
  }, [error]);

  return setError;
};
