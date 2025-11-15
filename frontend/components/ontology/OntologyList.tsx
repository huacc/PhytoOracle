/**
 * 本体类型列表组件
 * 展示所有本体类型的列表，支持选择切换
 */

import React from 'react';
import { List, Badge, Spin, Empty, Typography } from 'antd';
import {
  DatabaseOutlined,
  ExperimentOutlined,
  HomeOutlined,
  MedicineBoxOutlined,
  LinkOutlined,
} from '@ant-design/icons';
import { OntologyType, OntologyListItem } from '@/types';

const { Text } = Typography;

/**
 * 本体类型图标映射
 */
const ONTOLOGY_ICONS: Record<OntologyType, React.ReactNode> = {
  feature: <ExperimentOutlined className="text-blue-500" />,
  disease: <DatabaseOutlined className="text-red-500" />,
  host: <HomeOutlined className="text-green-500" />,
  treatment: <MedicineBoxOutlined className="text-purple-500" />,
};

/**
 * 本体类型名称映射
 */
const ONTOLOGY_NAMES: Record<OntologyType, string> = {
  feature: '特征本体',
  disease: '疾病本体',
  host: '宿主本体',
  treatment: '治疗本体',
};

/**
 * 本体类型描述映射
 */
const ONTOLOGY_DESCRIPTIONS: Record<OntologyType, string> = {
  feature: '定义可观察病害特征的维度和枚举值',
  disease: '定义疾病知识实例的数据结构',
  host: '定义宿主植物的分类和属性结构',
  treatment: '定义疾病治疗方案的结构',
};

/**
 * OntologyList 组件属性
 */
interface OntologyListProps {
  /** 本体列表数据 */
  ontologyList: OntologyListItem[];
  /** 当前选中的本体类型 */
  selectedType: OntologyType;
  /** 类型切换回调 */
  onTypeChange: (type: OntologyType) => void;
  /** 加载状态 */
  loading?: boolean;
}

/**
 * 本体类型列表组件
 */
export const OntologyList: React.FC<OntologyListProps> = ({
  ontologyList,
  selectedType,
  onTypeChange,
  loading = false,
}) => {
  /**
   * 获取本体的维度/字段数量
   * @param type - 本体类型
   * @returns 数量（用于Badge显示）
   */
  const getOntologyCount = (type: OntologyType): number => {
    const item = ontologyList.find((ont) => ont.type === type);
    // 如果没有具体数量，返回默认值
    return (item as any)?.count || 0;
  };

  /**
   * 处理列表项点击
   * @param type - 本体类型
   */
  const handleItemClick = (type: OntologyType) => {
    onTypeChange(type);
  };

  // 如果正在加载，显示加载状态
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <Spin tip="加载本体列表..." />
      </div>
    );
  }

  // 如果列表为空，显示空状态
  if (!ontologyList || ontologyList.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <Empty description="暂无本体数据" />
      </div>
    );
  }

  // 构建列表数据源（固定顺序）
  const dataSource: Array<{
    type: OntologyType;
    name: string;
    description: string;
    icon: React.ReactNode;
    count: number;
  }> = [
    {
      type: 'feature',
      name: ONTOLOGY_NAMES.feature,
      description: ONTOLOGY_DESCRIPTIONS.feature,
      icon: ONTOLOGY_ICONS.feature,
      count: getOntologyCount('feature') || 8, // 默认8个维度
    },
    {
      type: 'disease',
      name: ONTOLOGY_NAMES.disease,
      description: ONTOLOGY_DESCRIPTIONS.disease,
      icon: ONTOLOGY_ICONS.disease,
      count: getOntologyCount('disease') || 6, // 默认6个字段
    },
    {
      type: 'host',
      name: ONTOLOGY_NAMES.host,
      description: ONTOLOGY_DESCRIPTIONS.host,
      icon: ONTOLOGY_ICONS.host,
      count: getOntologyCount('host') || 5, // 默认5个字段
    },
    {
      type: 'treatment',
      name: ONTOLOGY_NAMES.treatment,
      description: ONTOLOGY_DESCRIPTIONS.treatment,
      icon: ONTOLOGY_ICONS.treatment,
      count: getOntologyCount('treatment') || 3, // 默认3个字段
    },
  ];

  return (
    <div className="flex h-full flex-col">
      {/* 列表标题 */}
      <div className="border-b border-gray-200 p-5">
        <h3 className="text-base font-medium text-gray-900">本体类型</h3>
        <p className="mt-1 text-sm text-gray-500">选择要查看的本体结构</p>
      </div>

      {/* 本体类型列表 */}
      <div className="flex-1 overflow-y-auto">
        <List
          dataSource={dataSource}
          renderItem={(item) => (
            <List.Item
              className={`
                cursor-pointer border-l-4 px-5 py-4 transition-all
                hover:bg-gray-50
                ${
                  selectedType === item.type
                    ? 'border-l-blue-500 bg-blue-50'
                    : 'border-l-transparent'
                }
              `}
              onClick={() => handleItemClick(item.type)}
            >
              <List.Item.Meta
                avatar={
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white shadow-sm">
                    <div className="text-xl">{item.icon}</div>
                  </div>
                }
                title={
                  <div className="flex items-center justify-between">
                    <Text
                      strong
                      className={
                        selectedType === item.type ? 'text-blue-600' : 'text-gray-900'
                      }
                    >
                      {item.name}
                    </Text>
                    <Badge
                      count={item.count}
                      showZero
                      style={{
                        backgroundColor: selectedType === item.type ? '#1890ff' : '#d9d9d9',
                      }}
                    />
                  </div>
                }
                description={
                  <Text
                    className={`text-xs ${
                      selectedType === item.type ? 'text-blue-500' : 'text-gray-500'
                    }`}
                  >
                    {item.description}
                  </Text>
                }
              />
            </List.Item>
          )}
        />
      </div>
    </div>
  );
};

/**
 * 示例用法：
 *
 * <OntologyList
 *   ontologyList={[
 *     { type: 'feature', name: '特征本体', version: '1.0' },
 *     { type: 'disease', name: '疾病本体', version: '1.0' },
 *   ]}
 *   selectedType="feature"
 *   onTypeChange={(type) => console.log('切换到', type)}
 *   loading={false}
 * />
 */
