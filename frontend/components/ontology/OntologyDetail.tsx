/**
 * 本体详情展示组件
 * 展示选中本体的详细信息，包括元信息、维度/字段列表、约束规则等
 */

import React from 'react';
import { Card, Descriptions, Tag, Empty, Button, Space, Typography, Alert } from 'antd';
import {
  ReloadOutlined,
  InfoCircleOutlined,
  FileTextOutlined,
  LockOutlined,
} from '@ant-design/icons';
import { DimensionCard } from './DimensionCard';
import {
  OntologyType,
  FeatureOntology,
  DiseaseSchema,
  HostSchema,
  TreatmentSchema,
  FeatureOntologyDimension,
  DiseaseSchemaField,
} from '@/types';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;

/**
 * 本体数据类型（union type）
 */
type OntologyData = FeatureOntology | DiseaseSchema | HostSchema | TreatmentSchema | null;

/**
 * OntologyDetail 组件属性
 */
interface OntologyDetailProps {
  /** 本体类型 */
  type: OntologyType;
  /** 本体数据 */
  data: OntologyData;
  /** 刷新回调 */
  onRefresh?: () => void;
}

/**
 * 本体类型标题映射
 */
const ONTOLOGY_TITLES: Record<OntologyType, string> = {
  feature: '特征本体 (Feature Ontology)',
  disease: '疾病本体 (Disease Schema)',
  host: '宿主本体 (Host Schema)',
  treatment: '治疗本体 (Treatment Schema)',
};

/**
 * 本体详情展示组件
 */
export const OntologyDetail: React.FC<OntologyDetailProps> = ({
  type,
  data,
  onRefresh,
}) => {
  /**
   * 判断是否为特征本体
   */
  const isFeatureOntology = (data: OntologyData): data is FeatureOntology => {
    return data !== null && 'dimensions' in data;
  };

  /**
   * 判断是否为Schema类型（疾病/宿主/治疗）
   */
  const isSchema = (
    data: OntologyData
  ): data is DiseaseSchema | HostSchema | TreatmentSchema => {
    return data !== null && 'schema_id' in data;
  };

  /**
   * 获取维度/字段列表
   */
  const getDimensionsOrFields = (): Array<
    FeatureOntologyDimension | DiseaseSchemaField
  > => {
    if (!data) return [];

    if (isFeatureOntology(data)) {
      return data.dimensions;
    }

    if (isSchema(data)) {
      // 对于Schema类型，合并required_fields和optional_fields
      const diseaseSchema = data as DiseaseSchema;
      if (diseaseSchema.required_fields || diseaseSchema.optional_fields) {
        return [
          ...(diseaseSchema.required_fields || []),
          ...(diseaseSchema.optional_fields || []),
        ];
      }

      // 对于宿主和治疗Schema，使用fields字段
      const otherSchema = data as HostSchema | TreatmentSchema;
      return otherSchema.fields || [];
    }

    return [];
  };

  /**
   * 渲染本体元信息
   */
  const renderMetaInfo = () => {
    if (!data) return null;

    let items: Array<{ label: string; children: React.ReactNode }> = [];

    if (isFeatureOntology(data)) {
      items = [
        {
          label: '本体ID',
          children: <Text code>{data.ontology_id}</Text>,
        },
        {
          label: '版本',
          children: <Tag color="blue">{data.version}</Tag>,
        },
        {
          label: '更新时间',
          children: data.updated_at
            ? dayjs(data.updated_at).format('YYYY-MM-DD HH:mm:ss')
            : '-',
        },
        {
          label: '描述',
          children: data.description || '-',
        },
        {
          label: '维度数量',
          children: <Tag color="green">{data.dimensions?.length || 0} 个维度</Tag>,
        },
      ];
    } else if (isSchema(data)) {
      items = [
        {
          label: 'Schema ID',
          children: <Text code>{data.schema_id}</Text>,
        },
        {
          label: '版本',
          children: <Tag color="blue">{data.version}</Tag>,
        },
      ];

      // 疾病Schema特有字段
      const diseaseSchema = data as DiseaseSchema;
      if (diseaseSchema.required_fields || diseaseSchema.optional_fields) {
        items.push({
          label: '字段数量',
          children: (
            <Space>
              <Tag color="red">
                必需: {diseaseSchema.required_fields?.length || 0}
              </Tag>
              <Tag color="default">
                可选: {diseaseSchema.optional_fields?.length || 0}
              </Tag>
            </Space>
          ),
        });
      } else {
        // 宿主/治疗Schema
        const otherSchema = data as HostSchema | TreatmentSchema;
        items.push({
          label: '字段数量',
          children: <Tag color="green">{otherSchema.fields?.length || 0} 个字段</Tag>,
        });
      }
    }

    return (
      <Descriptions
        column={2}
        bordered
        size="small"
        items={items}
        className="mb-6"
      />
    );
  };

  /**
   * 渲染模糊匹配规则（仅特征本体）
   */
  const renderFuzzyRules = () => {
    if (!isFeatureOntology(data) || !data.fuzzy_rules) return null;

    const { fuzzy_rules } = data;

    return (
      <Card
        title={
          <Space>
            <InfoCircleOutlined className="text-blue-500" />
            <span>模糊匹配规则</span>
          </Space>
        }
        size="small"
        className="mb-6"
      >
        <Space direction="vertical" className="w-full" size="middle">
          {fuzzy_rules.color_aliases && (
            <div>
              <Text strong className="text-sm">
                颜色别名映射：
              </Text>
              <div className="mt-2 flex flex-wrap gap-2">
                {Object.entries(fuzzy_rules.color_aliases).map(([key, values]) => (
                  <Tag key={key} color="cyan" className="text-xs">
                    {key} → {values.join(', ')}
                  </Tag>
                ))}
              </div>
            </div>
          )}

          {fuzzy_rules.size_tolerance !== undefined && (
            <div>
              <Text strong className="text-sm">
                大小容差：
              </Text>
              <Tag color="orange" className="ml-2 text-xs">
                ±{fuzzy_rules.size_tolerance} 级别
              </Tag>
            </div>
          )}

          {fuzzy_rules.synonym_mapping && (
            <div>
              <Text strong className="text-sm">
                症状同义词：
              </Text>
              <div className="mt-2 flex flex-wrap gap-2">
                {Object.entries(fuzzy_rules.synonym_mapping).map(([key, values]) => (
                  <Tag key={key} color="purple" className="text-xs">
                    {key} ≈ {values.join(', ')}
                  </Tag>
                ))}
              </div>
            </div>
          )}
        </Space>
      </Card>
    );
  };

  /**
   * 渲染维度/字段列表
   */
  const renderDimensionsList = () => {
    const items = getDimensionsOrFields();

    if (!items || items.length === 0) {
      return (
        <Empty
          description="暂无维度或字段数据"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      );
    }

    return (
      <div className="space-y-4">
        {items.map((item, index) => (
          <DimensionCard
            key={index}
            dimension={item}
            index={index}
            defaultExpanded={index === 0} // 默认展开第一个
          />
        ))}
      </div>
    );
  };

  // 如果没有数据，显示空状态
  if (!data) {
    return (
      <div className="flex h-full items-center justify-center p-12">
        <Empty
          description="请从左侧选择要查看的本体类型"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto p-6">
      {/* 页面头部 */}
      <Card className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <Space size="middle">
              <FileTextOutlined className="text-2xl text-blue-500" />
              <div>
                <Title level={3} className="mb-1">
                  {ONTOLOGY_TITLES[type]}
                </Title>
                <Text type="secondary" className="text-sm">
                  本体结构定义 - 只读模式
                </Text>
              </div>
            </Space>
          </div>

          <Space>
            <Tag icon={<LockOutlined />} color="default">
              只读
            </Tag>
            {onRefresh && (
              <Button
                icon={<ReloadOutlined />}
                onClick={onRefresh}
              >
                刷新数据
              </Button>
            )}
          </Space>
        </div>
      </Card>

      {/* 提示信息 */}
      <Alert
        message="什么是本体（Ontology Schema）？"
        description="本体是系统的结构定义，规定了数据模型、字段类型、枚举值约束等。本体较少修改，主要用于指导知识实例的录入和验证。如需编辑具体的疾病知识，请前往知识管理页面。"
        type="info"
        showIcon
        closable
        className="mb-6"
      />

      {/* 本体元信息 */}
      <Card
        title="本体元信息"
        size="small"
        className="mb-6"
      >
        {renderMetaInfo()}
      </Card>

      {/* 模糊匹配规则（仅特征本体） */}
      {renderFuzzyRules()}

      {/* 维度/字段列表 */}
      <Card
        title={
          <Space>
            <span>
              {isFeatureOntology(data) ? '维度定义' : '字段定义'}
            </span>
            <Tag color="blue">
              {getDimensionsOrFields().length} 个
            </Tag>
          </Space>
        }
        size="small"
      >
        {renderDimensionsList()}
      </Card>
    </div>
  );
};

/**
 * 示例用法：
 *
 * <OntologyDetail
 *   type="feature"
 *   data={{
 *     ontology_id: 'feature_ontology_v1',
 *     version: '1.0.0',
 *     updated_at: '2025-11-10T12:00:00Z',
 *     description: '定义花卉疾病的视觉特征维度和枚举值',
 *     dimensions: [
 *       {
 *         dimension_name: 'symptom_type',
 *         display_name: '症状类型',
 *         type: 'enum',
 *         required: true,
 *         description: '病害的主要症状表现形式',
 *         enum_values: [
 *           { key: 'necrosis_spot', label: '坏死斑点' },
 *         ],
 *       },
 *     ],
 *     fuzzy_rules: {
 *       color_aliases: { '褐色': ['棕色', 'brown'] },
 *       size_tolerance: 1,
 *     },
 *   }}
 *   onRefresh={() => console.log('刷新数据')}
 * />
 */
