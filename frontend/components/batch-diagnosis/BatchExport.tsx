/**
 * PhytoOracle 批量导出组件
 * 支持将批量诊断结果导出为JSON或CSV格式
 */

'use client';

import React from 'react';
import { Button, Space, message, Dropdown } from 'antd';
import { DownloadOutlined, FileTextOutlined, TableOutlined } from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { DiagnosisResult } from '@/types';
import { downloadFile, formatDate } from '@/utils';

/**
 * 批量导出组件的Props
 */
export interface BatchExportProps {
  /** 诊断结果列表 */
  results: DiagnosisResult[];
  /** 文件名前缀 */
  fileNamePrefix?: string;
  /** 是否禁用 */
  disabled?: boolean;
  /** 按钮大小 */
  size?: 'large' | 'middle' | 'small';
}

/**
 * 批量导出组件
 *
 * 功能：
 * - 导出为JSON格式（完整数据）
 * - 导出为CSV格式（表格数据）
 */
export const BatchExport: React.FC<BatchExportProps> = ({
  results,
  fileNamePrefix = 'batch_diagnosis',
  disabled = false,
  size = 'middle',
}) => {
  /**
   * 导出为JSON格式
   */
  const exportToJSON = () => {
    if (results.length === 0) {
      message.warning('暂无数据可导出');
      return;
    }

    try {
      // 生成JSON字符串
      const jsonData = JSON.stringify(results, null, 2);
      const blob = new Blob([jsonData], { type: 'application/json' });

      // 生成文件名
      const timestamp = formatDate(new Date(), 'YYYYMMDDHHmmss');
      const fileName = `${fileNamePrefix}_${timestamp}.json`;

      // 下载文件
      downloadFile(blob, fileName);
      message.success(`已导出 ${results.length} 条结果到 ${fileName}`);
    } catch (error) {
      console.error('导出JSON失败:', error);
      message.error('导出JSON失败，请重试');
    }
  };

  /**
   * 导出为CSV格式
   */
  const exportToCSV = () => {
    if (results.length === 0) {
      message.warning('暂无数据可导出');
      return;
    }

    try {
      // CSV表头
      const headers = [
        '诊断ID',
        '疾病ID',
        '疾病名称',
        '疾病英文名',
        '诊断类型',
        '置信度',
        '病原体学名',
        '病原体类型',
        '诊断时间',
      ];

      // CSV数据行
      const rows = results.map((result) => {
        const disease = result.confirmed_disease || result.suspected_diseases?.[0];
        const diagnosisType = result.confirmed_disease ? '确诊' : '疑似';
        const confidence = disease?.confidence ? (disease.confidence * 100).toFixed(2) + '%' : '-';

        return [
          result.diagnosis_id || '',
          disease?.disease_id || '',
          disease?.disease_name || '',
          disease?.common_name_en || '',
          disease ? diagnosisType : '失败',
          confidence,
          disease?.pathogen || '',
          disease?.pathogen_type || '',
          formatDate(result.timestamp, 'YYYY-MM-DD HH:mm:ss'),
        ];
      });

      // 构建CSV内容（处理特殊字符和换行）
      const escapeCsvField = (field: string): string => {
        // 如果字段包含逗号、引号或换行符，需要用引号包裹，并且引号需要转义
        if (field.includes(',') || field.includes('"') || field.includes('\n')) {
          return `"${field.replace(/"/g, '""')}"`;
        }
        return field;
      };

      const csvContent = [
        headers.map(escapeCsvField).join(','),
        ...rows.map((row) => row.map(escapeCsvField).join(',')),
      ].join('\n');

      // 添加BOM以支持Excel正确识别UTF-8编码
      const BOM = '\uFEFF';
      const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });

      // 生成文件名
      const timestamp = formatDate(new Date(), 'YYYYMMDDHHmmss');
      const fileName = `${fileNamePrefix}_${timestamp}.csv`;

      // 下载文件
      downloadFile(blob, fileName);
      message.success(`已导出 ${results.length} 条结果到 ${fileName}`);
    } catch (error) {
      console.error('导出CSV失败:', error);
      message.error('导出CSV失败，请重试');
    }
  };

  /**
   * 下拉菜单配置
   */
  const menuItems: MenuProps['items'] = [
    {
      key: 'json',
      label: '导出为JSON',
      icon: <FileTextOutlined />,
      onClick: exportToJSON,
    },
    {
      key: 'csv',
      label: '导出为CSV',
      icon: <TableOutlined />,
      onClick: exportToCSV,
    },
  ];

  return (
    <Dropdown menu={{ items: menuItems }} disabled={disabled || results.length === 0}>
      <Button
        type="primary"
        icon={<DownloadOutlined />}
        size={size}
        disabled={disabled || results.length === 0}
      >
        导出结果
      </Button>
    </Dropdown>
  );
};

export default BatchExport;

/**
 * 组件使用示例：
 *
 * ```tsx
 * import { BatchExport } from '@/components/batch-diagnosis';
 * import { DiagnosisResult } from '@/types';
 *
 * const results: DiagnosisResult[] = [
 *   // ... 诊断结果数组
 * ];
 *
 * <BatchExport
 *   results={results}
 *   fileNamePrefix="my_batch_diagnosis"
 *   disabled={false}
 *   size="large"
 * />
 * ```
 */
