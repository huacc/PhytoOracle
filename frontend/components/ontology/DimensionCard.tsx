/**
 * 维度卡片组件
 * 展示本体的单个维度/字段的详细信息，支持展开/折叠
 */

import React, { useState } from 'react';
import { Card, Tag, Space, Typography, Divider, Button, Collapse } from 'antd';
import {
  DownOutlined,
  UpOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { FeatureOntologyDimension, EnumValue, DiseaseSchemaField } from '@/types';

const { Text, Paragraph } = Typography;
const { Panel } = Collapse;

/**
 * DimensionCard 组件属性
 */
interface DimensionCardProps {
  /** 维度/字段数据（特征本体维度或疾病Schema字段） */
  dimension: FeatureOntologyDimension | DiseaseSchemaField;
  /** 卡片序号 */
  index: number;
  /** 是否默认展开 */
  defaultExpanded?: boolean;
}

/**
 * 维度卡片组件
 * 用于展示本体的维度或字段定义
 */
export const DimensionCard: React.FC<DimensionCardProps> = ({
  dimension,
  index,
  defaultExpanded = false,
}) => {
  // 展开/折叠状态
  const [expanded, setExpanded] = useState(defaultExpanded);

  /**
   * 判断是否为特征本体维度
   */
  const isFeatureDimension = (
    dim: FeatureOntologyDimension | DiseaseSchemaField
  ): dim is FeatureOntologyDimension => {
    return 'dimension_name' in dim;
  };

  /**
   * 判断是否为疾病Schema字段
   */
  const isDiseaseField = (
    dim: FeatureOntologyDimension | DiseaseSchemaField
  ): dim is DiseaseSchemaField => {
    return 'field_name' in dim;
  };

  /**
   * 获取维度/字段名称
   */
  const getName = (): string => {
    if (isFeatureDimension(dimension)) {
      return dimension.dimension_name;
    }
    if (isDiseaseField(dimension)) {
      return dimension.field_name;
    }
    return 'unknown';
  };

  /**
   * 获取显示名称
   */
  const getDisplayName = (): string => {
    if (isFeatureDimension(dimension)) {
      return dimension.display_name;
    }
    if (isDiseaseField(dimension)) {
      return dimension.display_name;
    }
    return '';
  };

  /**
   * 获取描述
   */
  const getDescription = (): string => {
    return dimension.description || '暂无描述';
  };

  /**
   * 获取数据类型
   */
  const getType = (): string => {
    return dimension.type;
  };

  /**
   * 是否必需
   */
  const isRequired = (): boolean => {
    if (isFeatureDimension(dimension)) {
      return dimension.required || false;
    }
    if (isDiseaseField(dimension)) {
      return dimension.required;
    }
    return false;
  };

  /**
   * 获取枚举值列表
   */
  const getEnumValues = (): EnumValue[] | undefined => {
    if (isFeatureDimension(dimension)) {
      return dimension.enum_values;
    }
    return undefined;
  };

  /**
   * 获取数据类型标签颜色
   */
  const getTypeColor = (type: string): string => {
    const colorMap: Record<string, string> = {
      string: 'blue',
      number: 'green',
      boolean: 'orange',
      enum: 'purple',
      array: 'cyan',
      object: 'magenta',
    };
    return colorMap[type] || 'default';
  };

  /**
   * 切换展开/折叠
   */
  const toggleExpanded = () => {
    setExpanded(!expanded);
  };

  const name = getName();
  const displayName = getDisplayName();
  const description = getDescription();
  const type = getType();
  const required = isRequired();
  const enumValues = getEnumValues();

  return (
    <Card
      className="transition-shadow hover:shadow-md"
      bodyStyle={{ padding: '16px' }}
    >
      {/* 卡片头部 */}
      <div
        className="flex cursor-pointer items-center justify-between"
        onClick={toggleExpanded}
      >
        <div className="flex flex-1 items-center gap-3">
          {/* 序号 */}
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-sm font-medium text-blue-600">
            {index + 1}
          </div>

          {/* 名称 */}
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <Text strong className="text-base">
                {displayName}
              </Text>
              <Text type="secondary" className="text-sm">
                ({name})
              </Text>
              {required && (
                <Tag color="red" className="text-xs">
                  必需
                </Tag>
              )}
            </div>
          </div>
        </div>

        {/* 右侧：类型标签和展开按钮 */}
        <Space size="middle">
          <Tag color={getTypeColor(type)} className="text-sm">
            {type}
          </Tag>
          <Button
            type="text"
            icon={expanded ? <UpOutlined /> : <DownOutlined />}
            size="small"
          />
        </Space>
      </div>

      {/* 卡片描述 */}
      <div className="mt-3">
        <Text className="text-sm text-gray-600">{description}</Text>
      </div>

      {/* 展开的详细内容 */}
      {expanded && (
        <>
          <Divider className="my-4" />

          <div className="space-y-4">
            {/* 基本属性 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Text type="secondary" className="text-xs">
                  字段名称：
                </Text>
                <Text className="ml-2 text-sm">{name}</Text>
              </div>
              <div>
                <Text type="secondary" className="text-xs">
                  数据类型：
                </Text>
                <Tag color={getTypeColor(type)} className="ml-2 text-xs">
                  {type}
                </Tag>
              </div>
              <div>
                <Text type="secondary" className="text-xs">
                  是否必需：
                </Text>
                <Text className="ml-2 text-sm">
                  {required ? (
                    <Tag color="red" icon={<CheckCircleOutlined />} className="text-xs">
                      是
                    </Tag>
                  ) : (
                    <Tag color="default" className="text-xs">
                      否
                    </Tag>
                  )}
                </Text>
              </div>

              {/* 特征本体特有：显示权重等信息 */}
              {isFeatureDimension(dimension) && (dimension as any).weight !== undefined && (
                <div>
                  <Text type="secondary" className="text-xs">
                    匹配权重：
                  </Text>
                  <Text className="ml-2 text-sm font-medium text-blue-600">
                    {(dimension as any).weight}%
                  </Text>
                </div>
              )}

              {/* 疾病Schema特有：显示默认值 */}
              {isDiseaseField(dimension) && dimension.default_value !== undefined && (
                <div>
                  <Text type="secondary" className="text-xs">
                    默认值：
                  </Text>
                  <Text className="ml-2 text-sm">{String(dimension.default_value)}</Text>
                </div>
              )}
            </div>

            {/* 枚举值列表（仅当类型为enum时） */}
            {type === 'enum' && enumValues && enumValues.length > 0 && (
              <div>
                <Divider className="my-3" />
                <div className="flex items-center gap-2 mb-3">
                  <InfoCircleOutlined className="text-blue-500" />
                  <Text strong className="text-sm">
                    枚举值定义 ({enumValues.length} 个)
                  </Text>
                </div>

                <div className="flex flex-wrap gap-2">
                  {enumValues.map((enumValue, idx) => (
                    <Tag
                      key={idx}
                      color="blue"
                      className="m-0 px-3 py-1 text-sm"
                      title={enumValue.description || enumValue.label}
                    >
                      <Space size={4}>
                        <Text className="text-xs font-mono">{enumValue.key}</Text>
                        <Text className="text-xs">-</Text>
                        <Text className="text-xs">{enumValue.label}</Text>
                        {enumValue.label_en && (
                          <>
                            <Text className="text-xs">/</Text>
                            <Text className="text-xs text-gray-500">{enumValue.label_en}</Text>
                          </>
                        )}
                      </Space>
                    </Tag>
                  ))}
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </Card>
  );
};

/**
 * 示例用法：
 *
 * // 特征本体维度
 * <DimensionCard
 *   dimension={{
 *     dimension_name: 'symptom_type',
 *     display_name: '症状类型',
 *     type: 'enum',
 *     description: '病害的主要症状表现形式',
 *     required: true,
 *     enum_values: [
 *       { key: 'necrosis_spot', label: '坏死斑点', label_en: 'Necrosis Spot' },
 *       { key: 'powdery_mildew', label: '白粉病', label_en: 'Powdery Mildew' },
 *     ],
 *   }}
 *   index={0}
 *   defaultExpanded={true}
 * />
 *
 * // 疾病Schema字段
 * <DimensionCard
 *   dimension={{
 *     field_name: 'disease_id',
 *     display_name: '疾病ID',
 *     type: 'string',
 *     description: '疾病的唯一标识符',
 *     required: true,
 *   }}
 *   index={0}
 * />
 */
