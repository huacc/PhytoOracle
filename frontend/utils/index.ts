/**
 * PhytoOracle 工具函数库
 * 提供通用的辅助函数
 */

import { UPLOAD_CONFIG, DATE_FORMATS } from '@/constants';
import dayjs from 'dayjs';

/**
 * 格式化日期时间
 * @param date - 日期对象、时间戳或ISO字符串
 * @param format - 格式化模板（默认：YYYY-MM-DD HH:mm:ss）
 * @returns 格式化后的日期字符串
 */
export function formatDate(
  date: Date | string | number,
  format: string = DATE_FORMATS.DATETIME
): string {
  return dayjs(date).format(format);
}

/**
 * 格式化文件大小
 * @param bytes - 字节数
 * @param decimals - 小数位数（默认：2）
 * @returns 格式化后的文件大小字符串（如：1.23 MB）
 */
export function formatFileSize(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

/**
 * 验证文件类型
 * @param file - 文件对象
 * @returns 是否为允许的图片格式
 */
export function validateFileType(file: File): boolean {
  const extension = file.name.split('.').pop()?.toLowerCase() || '';
  return UPLOAD_CONFIG.ALLOWED_FORMATS.includes(extension);
}

/**
 * 验证文件大小
 * @param file - 文件对象
 * @returns 是否在允许的大小范围内
 */
export function validateFileSize(file: File): boolean {
  const maxSizeInBytes = UPLOAD_CONFIG.MAX_SIZE * 1024 * 1024;
  return file.size <= maxSizeInBytes;
}

/**
 * 验证图片文件
 * @param file - 文件对象
 * @returns 验证结果对象 { valid: boolean, error?: string }
 */
export function validateImageFile(file: File): { valid: boolean; error?: string } {
  // 检查文件类型
  if (!validateFileType(file)) {
    return {
      valid: false,
      error: `不支持的文件格式，仅支持 ${UPLOAD_CONFIG.ALLOWED_FORMATS.join(', ')} 格式`,
    };
  }

  // 检查文件大小
  if (!validateFileSize(file)) {
    return {
      valid: false,
      error: `文件大小超过 ${UPLOAD_CONFIG.MAX_SIZE}MB 限制`,
    };
  }

  return { valid: true };
}

/**
 * 格式化置信度
 * @param confidence - 置信度（0-1）
 * @param decimals - 小数位数（默认：0）
 * @returns 格式化后的百分比字符串（如：95%）
 */
export function formatConfidence(confidence: number, decimals: number = 0): string {
  return `${(confidence * 100).toFixed(decimals)}%`;
}

/**
 * 防抖函数
 * @param func - 要执行的函数
 * @param wait - 等待时间（毫秒）
 * @returns 防抖后的函数
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;

  return function (this: any, ...args: Parameters<T>) {
    const context = this;

    if (timeout) clearTimeout(timeout);

    timeout = setTimeout(() => {
      func.apply(context, args);
    }, wait);
  };
}

/**
 * 节流函数
 * @param func - 要执行的函数
 * @param wait - 等待时间（毫秒）
 * @returns 节流后的函数
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  let previous = 0;

  return function (this: any, ...args: Parameters<T>) {
    const context = this;
    const now = Date.now();

    if (!previous) previous = now;

    const remaining = wait - (now - previous);

    if (remaining <= 0 || remaining > wait) {
      if (timeout) {
        clearTimeout(timeout);
        timeout = null;
      }
      previous = now;
      func.apply(context, args);
    } else if (!timeout) {
      timeout = setTimeout(() => {
        previous = Date.now();
        timeout = null;
        func.apply(context, args);
      }, remaining);
    }
  };
}

/**
 * 深拷贝对象
 * @param obj - 要拷贝的对象
 * @returns 深拷贝后的对象
 */
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  if (obj instanceof Date) {
    return new Date(obj.getTime()) as any;
  }

  if (obj instanceof Array) {
    return obj.map((item) => deepClone(item)) as any;
  }

  if (obj instanceof Object) {
    const clonedObj: any = {};
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key]);
      }
    }
    return clonedObj;
  }

  return obj;
}

/**
 * 生成唯一ID
 * @param prefix - ID前缀（可选）
 * @returns 唯一ID字符串
 */
export function generateId(prefix: string = ''): string {
  const timestamp = Date.now().toString(36);
  const randomStr = Math.random().toString(36).substring(2, 9);
  return prefix ? `${prefix}_${timestamp}_${randomStr}` : `${timestamp}_${randomStr}`;
}

/**
 * 下载文件
 * @param blob - Blob对象或URL字符串
 * @param filename - 文件名
 */
export function downloadFile(blob: Blob | string, filename: string): void {
  const url = typeof blob === 'string' ? blob : URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  // 释放URL对象
  if (typeof blob !== 'string') {
    URL.revokeObjectURL(url);
  }
}

/**
 * 复制文本到剪贴板
 * @param text - 要复制的文本
 * @returns Promise，成功时resolve
 */
export async function copyToClipboard(text: string): Promise<void> {
  if (navigator.clipboard && window.isSecureContext) {
    // 现代浏览器API
    await navigator.clipboard.writeText(text);
  } else {
    // 降级方案
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
  }
}

/**
 * 休眠函数
 * @param ms - 休眠时间（毫秒）
 * @returns Promise
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * 判断是否为移动设备
 * @returns 是否为移动设备
 */
export function isMobile(): boolean {
  if (typeof window === 'undefined') return false;
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

/**
 * 获取URL查询参数
 * @param key - 参数键名
 * @returns 参数值
 */
export function getQueryParam(key: string): string | null {
  if (typeof window === 'undefined') return null;
  const params = new URLSearchParams(window.location.search);
  return params.get(key);
}

/**
 * 设置URL查询参数
 * @param key - 参数键名
 * @param value - 参数值
 */
export function setQueryParam(key: string, value: string): void {
  if (typeof window === 'undefined') return;
  const params = new URLSearchParams(window.location.search);
  params.set(key, value);
  const newUrl = `${window.location.pathname}?${params.toString()}`;
  window.history.pushState({}, '', newUrl);
}

/**
 * 移除URL查询参数
 * @param key - 参数键名
 */
export function removeQueryParam(key: string): void {
  if (typeof window === 'undefined') return;
  const params = new URLSearchParams(window.location.search);
  params.delete(key);
  const newUrl = params.toString()
    ? `${window.location.pathname}?${params.toString()}`
    : window.location.pathname;
  window.history.pushState({}, '', newUrl);
}

/**
 * 清空所有URL查询参数
 */
export function clearQueryParams(): void {
  if (typeof window === 'undefined') return;
  window.history.pushState({}, '', window.location.pathname);
}
