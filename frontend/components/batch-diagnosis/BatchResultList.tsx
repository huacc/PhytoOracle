/**
 * PhytoOracle 批量诊断结果列表组件
 * 展示所有批量诊断结果，支持筛选、排序和查看详情
 */

'use client';

import React, { useState, useMemo } from 'react';
import { Card, Select, Radio, Space, Typography, Empty, Pagination } from 'antd';
import { FilterOutlined, SortAscendingOutlined } from '@ant-design/icons';
import { DiagnosisResult } from '@/types';
import { BatchResultCard } from './BatchResultCard';

const { Title, Text } = Typography;

/**
 * 批量诊断结果列表组件的Props
 */
export interface BatchResultListProps {
  /** 诊断结果列表 */
  results: DiagnosisResult[];
  /** 图片源映射（diagnosis_id -> File | URL） */
  imageSources?: Map<string, string | File>;
  /** 文件名映射（diagnosis_id -> fileName） */
  fileNames?: Map<string, string>;
  /** 当前选中的结果ID */
  selectedId?: string;
  /** 选中变化回调 */
  onSelectChange?: (diagnosisId: string) => void;
  /** 查看详情回调 */
  onViewDetail?: (result: DiagnosisResult) => void;
  /** 每页显示数量 */
  pageSize?: number;
}

/**
 * 筛选类型
 */
type FilterType = 'all' | 'success' | 'failed';

/**
 * 排序类型
 */
type SortType = 'default' | 'confidence-desc' | 'confidence-asc';

/**
 * 批量诊断结果列表组件
 *
 * 功能：
 * - 结果列表展示
 * - 筛选（全部/成功/失败）
 * - 排序（置信度升序/降序）
 * - 分页
 * - 点击查看详情
 */
export const BatchResultList: React.FC<BatchResultListProps> = ({
  results,
  imageSources = new Map(),
  fileNames = new Map(),
  selectedId,
  onSelectChange,
  onViewDetail,
  pageSize = 12,
}) => {
  // 筛选和排序状态
  const [filterType, setFilterType] = useState<FilterType>('all');
  const [sortType, setSortType] = useState<SortType>('default');
  const [currentPage, setCurrentPage] = useState(1);

  /**
   * 筛选结果
   */
  const filteredResults = useMemo(() => {
    return results.filter((result) => {
      if (filterType === 'all') return true;

      const hasDisease =
        result.confirmed_disease ||
        (result.suspected_diseases && result.suspected_diseases.length > 0);

      if (filterType === 'success') return hasDisease;
      if (filterType === 'failed') return !hasDisease;

      return true;
    });
  }, [results, filterType]);

  /**
   * 排序结果
   */
  const sortedResults = useMemo(() => {
    const sorted = [...filteredResults];

    if (sortType === 'confidence-desc') {
      sorted.sort((a, b) => {
        const confA = a.confirmed_disease?.confidence || a.suspected_diseases?.[0]?.confidence || 0;
        const confB = b.confirmed_disease?.confidence || b.suspected_diseases?.[0]?.confidence || 0;
        return confB - confA;
      });
    } else if (sortType === 'confidence-asc') {
      sorted.sort((a, b) => {
        const confA = a.confirmed_disease?.confidence || a.suspected_diseases?.[0]?.confidence || 0;
        const confB = b.confirmed_disease?.confidence || b.suspected_diseases?.[0]?.confidence || 0;
        return confA - confB;
      });
    }

    return sorted;
  }, [filteredResults, sortType]);

  /**
   * 分页结果
   */
  const paginatedResults = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    return sortedResults.slice(start, end);
  }, [sortedResults, currentPage, pageSize]);

  /**
   * 处理页码变化
   */
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  /**
   * 重置页码（当筛选或排序变化时）
   */
  React.useEffect(() => {
    setCurrentPage(1);
  }, [filterType, sortType]);

  return (
    <Card
      title={
        <div className="flex justify-between items-center">
          <Space>
            <Title level={5} className="m-0">
              诊断结果列表
            </Title>
            <Text type="secondary">
              ({filteredResults.length} / {results.length})
            </Text>
          </Space>
        </div>
      }
      extra={
        <Space>
          {/* 筛选器 */}
          <Space>
            <FilterOutlined />
            <Radio.Group
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              optionType="button"
              buttonStyle="solid"
              size="small"
            >
              <Radio.Button value="all">全部</Radio.Button>
              <Radio.Button value="success">成功</Radio.Button>
              <Radio.Button value="failed">失败</Radio.Button>
            </Radio.Group>
          </Space>

          {/* 排序器 */}
          <Space>
            <SortAscendingOutlined />
            <Select
              value={sortType}
              onChange={setSortType}
              size="small"
              style={{ width: 140 }}
              options={[
                { label: '默认排序', value: 'default' },
                { label: '置信度从高到低', value: 'confidence-desc' },
                { label: '置信度从低到高', value: 'confidence-asc' },
              ]}
            />
          </Space>
        </Space>
      }
      className="batch-result-list"
    >
      {/* 结果网格 */}
      {paginatedResults.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
            {paginatedResults.map((result) => (
              <BatchResultCard
                key={result.diagnosis_id}
                result={result}
                imageSource={imageSources.get(result.diagnosis_id)}
                fileName={fileNames.get(result.diagnosis_id)}
                selected={selectedId === result.diagnosis_id}
                onClick={() => onSelectChange?.(result.diagnosis_id)}
                onViewDetail={() => onViewDetail?.(result)}
              />
            ))}
          </div>

          {/* 分页 */}
          {sortedResults.length > pageSize && (
            <div className="flex justify-center">
              <Pagination
                current={currentPage}
                total={sortedResults.length}
                pageSize={pageSize}
                onChange={handlePageChange}
                showSizeChanger={false}
                showTotal={(total) => `共 ${total} 条结果`}
              />
            </div>
          )}
        </>
      ) : (
        <Empty description="暂无诊断结果" />
      )}
    </Card>
  );
};

export default BatchResultList;

/**
 * 组件使用示例：
 *
 * ```tsx
 * import { BatchResultList } from '@/components/batch-diagnosis';
 * import { useState } from 'react';
 * import { DiagnosisResult } from '@/types';
 *
 * function MyPage() {
 *   const [results, setResults] = useState<DiagnosisResult[]>([]);
 *   const [selectedId, setSelectedId] = useState<string>();
 *   const imageSources = new Map<string, File>();
 *   const fileNames = new Map<string, string>();
 *
 *   return (
 *     <BatchResultList
 *       results={results}
 *       imageSources={imageSources}
 *       fileNames={fileNames}
 *       selectedId={selectedId}
 *       onSelectChange={setSelectedId}
 *       onViewDetail={(result) => console.log('view', result)}
 *       pageSize={12}
 *     />
 *   );
 * }
 * ```
 */
