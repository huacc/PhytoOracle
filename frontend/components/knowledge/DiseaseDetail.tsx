/**
 * PhytoOracle 疾病详情组件
 * 展示疾病的完整知识信息，包括基本信息和多维度特征
 * 支持只读模式和编辑模式
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Descriptions,
  Button,
  Space,
  Tag,
  Collapse,
  message,
} from 'antd';
import {
  EditOutlined,
  SaveOutlined,
  CloseOutlined,
  CheckCircleOutlined,
  ExperimentOutlined,
} from '@ant-design/icons';
import { DiseaseKnowledge, DiseaseFeatureDimension } from '@/types';
import { DimensionCard, VLMDescriptionEditor } from '@/components/knowledge';

const { Panel } = Collapse;

/**
 * DiseaseDetail 组件属性
 */
interface DiseaseDetailProps {
  /** 疾病知识数据 */
  knowledge: DiseaseKnowledge;
  /** 是否处于编辑模式 */
  isEditMode: boolean;
  /** 进入编辑模式回调 */
  onEdit: () => void;
  /** 取消编辑回调 */
  onCancelEdit: () => void;
  /** 保存修改回调 */
  onSave: (updatedKnowledge: Partial<DiseaseKnowledge>) => void;
}

/**
 * 疾病详情组件
 *
 * 功能：
 * 1. 展示疾病基本信息（ID、名称、病原体、宿主）
 * 2. 展示多维度特征卡片（8个维度）
 * 3. 支持编辑模式，修改VLM描述和权重
 * 4. 支持保存修改和取消编辑
 * 5. 支持测试诊断功能
 *
 * @param props - 组件属性
 * @returns React组件
 */
export const DiseaseDetail: React.FC<DiseaseDetailProps> = ({
  knowledge,
  isEditMode,
  onEdit,
  onCancelEdit,
  onSave,
}) => {
  // 编辑中的疾病知识数据（深拷贝）
  const [editingKnowledge, setEditingKnowledge] = useState<DiseaseKnowledge>(
    JSON.parse(JSON.stringify(knowledge))
  );

  // 当knowledge变化时，重置编辑数据
  useEffect(() => {
    setEditingKnowledge(JSON.parse(JSON.stringify(knowledge)));
  }, [knowledge]);

  /**
   * 处理维度更新
   * @param dimensionName - 维度名称
   * @param updatedDimension - 更新后的维度数据
   */
  const handleDimensionUpdate = (
    dimensionName: string,
    updatedDimension: DiseaseFeatureDimension
  ) => {
    setEditingKnowledge((prev) => {
      const newDimensions = prev.dimensions.map((dim) =>
        dim.dimension_name === dimensionName ? updatedDimension : dim
      );
      return { ...prev, dimensions: newDimensions };
    });
  };

  /**
   * 处理保存
   */
  const handleSave = () => {
    // 构建更新数据（只包含可编辑的字段）
    const updatedData: Partial<DiseaseKnowledge> = {
      dimensions: editingKnowledge.dimensions,
      // 其他可能的可编辑字段...
    };

    onSave(updatedData);
  };

  /**
   * 处理取消编辑
   */
  const handleCancel = () => {
    // 重置编辑数据
    setEditingKnowledge(JSON.parse(JSON.stringify(knowledge)));
    onCancelEdit();
  };

  /**
   * 处理测试诊断
   */
  const handleTestDiagnosis = () => {
    // TODO: 实现测试诊断功能
    message.info('测试诊断功能开发中...');
  };

  /**
   * 根据重要性级别获取Tag颜色
   */
  const getImportanceColor = (importance?: 'major' | 'minor' | 'optional'): string => {
    switch (importance) {
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
   * 根据重要性级别获取Tag文本
   */
  const getImportanceText = (importance?: 'major' | 'minor' | 'optional'): string => {
    switch (importance) {
      case 'major':
        return '主要特征';
      case 'minor':
        return '次要特征';
      case 'optional':
        return '可选特征';
      default:
        return '未分类';
    }
  };

  // 获取用于显示的数据（编辑模式用editingKnowledge，只读模式用knowledge）
  const displayKnowledge = isEditMode ? editingKnowledge : knowledge;

  // 按重要性分组维度
  const majorDimensions = displayKnowledge.dimensions.filter(
    (dim) => dim.importance === 'major'
  );
  const minorDimensions = displayKnowledge.dimensions.filter(
    (dim) => dim.importance === 'minor'
  );
  const optionalDimensions = displayKnowledge.dimensions.filter(
    (dim) => dim.importance === 'optional'
  );

  return (
    <div className="p-6 space-y-6">
      {/* 操作按钮栏 */}
      <Card>
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-800">
            {displayKnowledge.disease_name_zh}
            <span className="ml-3 text-sm text-gray-500">
              ({displayKnowledge.disease_name_en})
            </span>
          </h2>

          <Space>
            {isEditMode ? (
              <>
                <Button
                  type="default"
                  icon={<CloseOutlined />}
                  onClick={handleCancel}
                >
                  取消
                </Button>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  onClick={handleSave}
                >
                  保存修改
                </Button>
              </>
            ) : (
              <>
                <Button
                  type="default"
                  icon={<ExperimentOutlined />}
                  onClick={handleTestDiagnosis}
                >
                  测试诊断
                </Button>
                <Button
                  type="primary"
                  icon={<EditOutlined />}
                  onClick={onEdit}
                >
                  编辑
                </Button>
              </>
            )}
          </Space>
        </div>
      </Card>

      {/* 基本信息 */}
      <Card title="基本信息" size="small">
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="疾病ID">
            <code className="bg-gray-100 px-2 py-1 rounded text-sm">
              {displayKnowledge.disease_id}
            </code>
          </Descriptions.Item>

          <Descriptions.Item label="宿主属">
            <Tag color="green">{displayKnowledge.host_genus}</Tag>
          </Descriptions.Item>

          <Descriptions.Item label="病原体类型">
            <Tag color="orange">{displayKnowledge.pathogen.type}</Tag>
          </Descriptions.Item>

          <Descriptions.Item label="病原体学名">
            <em>{displayKnowledge.pathogen.species}</em>
          </Descriptions.Item>

          {displayKnowledge.updated_at && (
            <Descriptions.Item label="更新时间" span={2}>
              {new Date(displayKnowledge.updated_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      {/* 主要特征 */}
      {majorDimensions.length > 0 && (
        <Card
          title={
            <span>
              主要特征
              <Tag color="red" className="ml-2">
                权重 50%+
              </Tag>
            </span>
          }
          size="small"
        >
          <div className="space-y-4">
            {majorDimensions.map((dimension) => (
              <DimensionCard
                key={dimension.dimension_name}
                dimension={dimension}
                isEditMode={isEditMode}
                onUpdate={(updated) =>
                  handleDimensionUpdate(dimension.dimension_name, updated)
                }
              />
            ))}
          </div>
        </Card>
      )}

      {/* 次要特征 */}
      {minorDimensions.length > 0 && (
        <Card
          title={
            <span>
              次要特征
              <Tag color="orange" className="ml-2">
                权重 10-30%
              </Tag>
            </span>
          }
          size="small"
        >
          <div className="space-y-4">
            {minorDimensions.map((dimension) => (
              <DimensionCard
                key={dimension.dimension_name}
                dimension={dimension}
                isEditMode={isEditMode}
                onUpdate={(updated) =>
                  handleDimensionUpdate(dimension.dimension_name, updated)
                }
              />
            ))}
          </div>
        </Card>
      )}

      {/* 可选特征 */}
      {optionalDimensions.length > 0 && (
        <Card
          title={
            <span>
              可选特征
              <Tag color="blue" className="ml-2">
                权重 &lt;10%
              </Tag>
            </span>
          }
          size="small"
        >
          <Collapse ghost>
            <Panel header={`展开查看 ${optionalDimensions.length} 个可选特征`} key="optional">
              <div className="space-y-4">
                {optionalDimensions.map((dimension) => (
                  <DimensionCard
                    key={dimension.dimension_name}
                    dimension={dimension}
                    isEditMode={isEditMode}
                    onUpdate={(updated) =>
                      handleDimensionUpdate(dimension.dimension_name, updated)
                    }
                  />
                ))}
              </div>
            </Panel>
          </Collapse>
        </Card>
      )}

      {/* 治疗知识（可折叠，预留接口） */}
      {displayKnowledge.treatment_recommendations &&
        displayKnowledge.treatment_recommendations.length > 0 && (
          <Card title="治疗建议" size="small">
            <Collapse ghost>
              <Panel header="展开查看治疗建议" key="treatment">
                <ul className="list-disc list-inside space-y-2">
                  {displayKnowledge.treatment_recommendations.map((treatment, index) => (
                    <li key={index} className="text-gray-700">
                      {treatment}
                    </li>
                  ))}
                </ul>
              </Panel>
            </Collapse>
          </Card>
        )}
    </div>
  );
};

export default DiseaseDetail;

/**
 * 示例用法：
 *
 * import { DiseaseDetail } from '@/components/knowledge';
 * import { DiseaseKnowledge } from '@/types';
 *
 * const diseaseKnowledge: DiseaseKnowledge = {
 *   disease_id: 'rose_black_spot',
 *   disease_name_zh: '玫瑰黑斑病',
 *   disease_name_en: 'Rose Black Spot',
 *   pathogen: {
 *     type: 'fungal',
 *     species: 'Diplocarpon rosae',
 *   },
 *   host_genus: 'Rosa',
 *   feature_vector: {},
 *   dimensions: [
 *     {
 *       dimension_name: 'symptom_type',
 *       standard_value: 'necrosis_spot',
 *       terminology: '坏死斑点',
 *       weight: 50,
 *       importance: 'major',
 *       vlm_description: {
 *         imaging_description: '组织坏死形成的黑色或褐色斑点',
 *         everyday_language: '像被香烟烫过留下的焦痕',
 *       },
 *     },
 *   ],
 * };
 *
 * function MyComponent() {
 *   const [isEditMode, setIsEditMode] = useState(false);
 *
 *   return (
 *     <DiseaseDetail
 *       knowledge={diseaseKnowledge}
 *       isEditMode={isEditMode}
 *       onEdit={() => setIsEditMode(true)}
 *       onCancelEdit={() => setIsEditMode(false)}
 *       onSave={(updated) => {
 *         console.log('保存修改:', updated);
 *         setIsEditMode(false);
 *       }}
 *     />
 *   );
 * }
 */
