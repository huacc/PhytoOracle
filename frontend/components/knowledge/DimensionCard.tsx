/**
 * PhytoOracle 维度卡片组件（知识管理版）
 * 展示疾病知识的单个特征维度信息
 * 带本体标识badge，支持编辑模式
 */

import React, { useState } from 'react';
import { Card, Tag, Badge, Collapse, Slider, Input, Space, Button } from 'antd';
import { DatabaseOutlined, EditOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons';
import { DiseaseFeatureDimension, VLMDescription } from '@/types';

const { Panel } = Collapse;
const { TextArea } = Input;

/**
 * DimensionCard 组件属性
 */
interface DimensionCardProps {
  /** 维度数据 */
  dimension: DiseaseFeatureDimension;
  /** 是否处于编辑模式 */
  isEditMode: boolean;
  /** 更新回调 */
  onUpdate: (updatedDimension: DiseaseFeatureDimension) => void;
}

/**
 * 维度卡片组件
 *
 * 功能：
 * 1. 展示维度的基本信息（名称、标准值、术语、权重）
 * 2. 展示VLM可理解的描述（影像学描述、日常用语、空间定位）
 * 3. 支持编辑VLM描述和调整权重
 * 4. 显示"特征本体"badge标识
 *
 * @param props - 组件属性
 * @returns React组件
 */
export const DimensionCard: React.FC<DimensionCardProps> = ({
  dimension,
  isEditMode,
  onUpdate,
}) => {
  // 本地编辑状态（用于编辑模式下的实时更新）
  const [localDimension, setLocalDimension] = useState<DiseaseFeatureDimension>(
    JSON.parse(JSON.stringify(dimension))
  );

  // 是否展开VLM描述
  const [isVLMExpanded, setIsVLMExpanded] = useState(false);

  /**
   * 处理权重变化
   * @param value - 新的权重值
   */
  const handleWeightChange = (value: number) => {
    const updated = { ...localDimension, weight: value };
    setLocalDimension(updated);
    onUpdate(updated);
  };

  /**
   * 处理VLM描述更新
   * @param field - 描述字段名
   * @param value - 新值
   */
  const handleVLMDescriptionChange = (
    field: keyof VLMDescription,
    value: string
  ) => {
    const updated = {
      ...localDimension,
      vlm_description: {
        ...localDimension.vlm_description,
        [field]: value,
      },
    };
    setLocalDimension(updated);
    onUpdate(updated);
  };

  /**
   * 格式化标准值（处理数组或字符串）
   */
  const formatStandardValue = (): string => {
    if (Array.isArray(dimension.standard_value)) {
      return dimension.standard_value.join(', ');
    }
    return String(dimension.standard_value);
  };

  /**
   * 获取重要性Tag颜色
   */
  const getImportanceColor = (): string => {
    switch (dimension.importance) {
      case 'major':
        return 'red';
      case 'minor':
        return 'orange';
      case 'optional':
        return 'blue';
      default:
        return 'default';
    }
  };

  /**
   * 获取重要性文本
   */
  const getImportanceText = (): string => {
    switch (dimension.importance) {
      case 'major':
        return '主要';
      case 'minor':
        return '次要';
      case 'optional':
        return '可选';
      default:
        return '未分类';
    }
  };

  return (
    <Card
      size="small"
      className="dimension-card shadow-sm"
      style={{ borderLeft: `4px solid ${getImportanceColor()}` }}
      title={
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {/* 本体标识badge */}
            <Badge
              count={
                <Tag icon={<DatabaseOutlined />} color="blue" className="m-0">
                  特征本体
                </Tag>
              }
              offset={[-10, 0]}
            >
              <span className="font-semibold text-base">
                {dimension.dimension_name}
              </span>
            </Badge>

            {/* 重要性标签 */}
            <Tag color={getImportanceColor()}>
              {getImportanceText()}
            </Tag>

            {/* 权重显示 */}
            {dimension.weight !== undefined && (
              <Tag color="purple">
                权重: {dimension.weight}%
              </Tag>
            )}
          </div>
        </div>
      }
    >
      {/* 基本信息 */}
      <div className="space-y-3 mb-4">
        <div>
          <span className="text-gray-600 font-medium">标准值：</span>
          <code className="ml-2 bg-gray-100 px-2 py-1 rounded text-sm">
            {formatStandardValue()}
          </code>
        </div>

        {dimension.terminology && (
          <div>
            <span className="text-gray-600 font-medium">术语：</span>
            <span className="ml-2 text-gray-800">{dimension.terminology}</span>
          </div>
        )}

        {/* 权重调整（编辑模式） */}
        {isEditMode && dimension.weight !== undefined && (
          <div>
            <span className="text-gray-600 font-medium">调整权重：</span>
            <Slider
              min={0}
              max={100}
              value={localDimension.weight}
              onChange={handleWeightChange}
              marks={{ 0: '0%', 25: '25%', 50: '50%', 75: '75%', 100: '100%' }}
              className="mt-2"
            />
          </div>
        )}
      </div>

      {/* VLM可理解的描述 */}
      {dimension.vlm_description && (
        <Collapse
          ghost
          activeKey={isVLMExpanded ? ['vlm'] : []}
          onChange={(keys) => setIsVLMExpanded(keys.includes('vlm'))}
        >
          <Panel
            header={
              <span className="text-blue-600 font-medium">
                VLM可理解的描述
                {isEditMode && <Tag color="green" className="ml-2">可编辑</Tag>}
              </span>
            }
            key="vlm"
          >
            <div className="space-y-4">
              {/* 影像学描述 */}
              <div>
                <div className="flex items-center mb-2">
                  <span className="text-gray-700 font-medium">影像学描述：</span>
                </div>
                {isEditMode ? (
                  <TextArea
                    value={localDimension.vlm_description?.imaging_description || ''}
                    onChange={(e) =>
                      handleVLMDescriptionChange('imaging_description', e.target.value)
                    }
                    placeholder="请输入医学/植物病理学的专业描述"
                    autoSize={{ minRows: 2, maxRows: 4 }}
                    className="text-sm"
                  />
                ) : (
                  <p className="text-gray-600 text-sm bg-gray-50 p-3 rounded">
                    {dimension.vlm_description.imaging_description ||
                      '（暂无描述）'}
                  </p>
                )}
              </div>

              {/* 日常用语 */}
              <div>
                <div className="flex items-center mb-2">
                  <span className="text-gray-700 font-medium">日常用语：</span>
                </div>
                {isEditMode ? (
                  <TextArea
                    value={localDimension.vlm_description?.everyday_language || ''}
                    onChange={(e) =>
                      handleVLMDescriptionChange('everyday_language', e.target.value)
                    }
                    placeholder="请输入生活化的比喻和视觉隐喻"
                    autoSize={{ minRows: 2, maxRows: 4 }}
                    className="text-sm"
                  />
                ) : (
                  <p className="text-gray-600 text-sm bg-gray-50 p-3 rounded">
                    {dimension.vlm_description.everyday_language ||
                      '（暂无描述）'}
                  </p>
                )}
              </div>

              {/* 空间定位 */}
              <div>
                <div className="flex items-center mb-2">
                  <span className="text-gray-700 font-medium">空间定位方法：</span>
                </div>
                {isEditMode ? (
                  <TextArea
                    value={localDimension.vlm_description?.spatial_positioning || ''}
                    onChange={(e) =>
                      handleVLMDescriptionChange('spatial_positioning', e.target.value)
                    }
                    placeholder="请输入位置、大小、范围的量化描述"
                    autoSize={{ minRows: 2, maxRows: 4 }}
                    className="text-sm"
                  />
                ) : (
                  <p className="text-gray-600 text-sm bg-gray-50 p-3 rounded">
                    {dimension.vlm_description.spatial_positioning ||
                      '（暂无描述）'}
                  </p>
                )}
              </div>
            </div>
          </Panel>
        </Collapse>
      )}
    </Card>
  );
};

export default DimensionCard;

/**
 * 示例用法：
 *
 * import { DimensionCard } from '@/components/knowledge';
 * import { DiseaseFeatureDimension } from '@/types';
 *
 * const dimension: DiseaseFeatureDimension = {
 *   dimension_name: 'color_border',
 *   standard_value: ['yellow', 'light_yellow'],
 *   terminology: '黄色晕圈',
 *   weight: 30,
 *   importance: 'major',
 *   vlm_description: {
 *     imaging_description: '病斑周围有明显的黄色晕染区域',
 *     everyday_language: '像月亮周围的黄色光晕，像煎蛋蛋白环绕蛋黄',
 *     spatial_positioning: '从病斑中心向外0.5-2mm的环状区域',
 *   },
 * };
 *
 * function MyComponent() {
 *   const [isEditMode, setIsEditMode] = useState(false);
 *
 *   return (
 *     <DimensionCard
 *       dimension={dimension}
 *       isEditMode={isEditMode}
 *       onUpdate={(updated) => {
 *         console.log('维度更新:', updated);
 *       }}
 *     />
 *   );
 * }
 */
