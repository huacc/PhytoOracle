/**
 * PhytoOracle - VLM问答对展示组件
 * 功能：展示VLM特征提取的Q0-Q6问答对
 *
 * @author PhytoOracle Team
 * @version 1.0.0
 */

'use client';

import React, { useState } from 'react';
import { Card, Collapse, Tag, Typography, Divider, Button } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  DownOutlined,
} from '@ant-design/icons';
import { FeatureVector } from '@/types';

const { Panel } = Collapse;
const { Text, Paragraph } = Typography;

/**
 * VLMQuestionnaire 组件属性
 */
export interface VLMQuestionnaireProps {
  /** VLM提取的特征向量 */
  featureVector: FeatureVector;
  /** 是否默认展开 */
  defaultOpen?: boolean;
  /** 自定义样式 */
  className?: string;
}

/**
 * 问答对数据项
 */
interface QAItem {
  /** 问题ID */
  id: string;
  /** 问题标题 */
  title: string;
  /** 问题描述 */
  question: string;
  /** VLM回答 */
  answer: string;
  /** 是否通过（仅Q0阶段有效） */
  passed?: boolean;
  /** 提取的结构化值 */
  extracted_value?: string;
}

/**
 * VLM问答对展示组件
 *
 * 功能：
 * - 展示Q0.0-Q0.5的过滤问答（带通过/失败标记）
 * - 展示Q1-Q6的特征提取问答
 * - 支持折叠/展开详情
 * - 显示提取的结构化值
 *
 * @param props - 组件属性
 * @returns VLM问答对组件
 */
export const VLMQuestionnaire: React.FC<VLMQuestionnaireProps> = ({
  featureVector,
  defaultOpen = false,
  className = '',
}) => {
  // 状态：是否展开所有问答对
  const [expandedQA, setExpandedQA] = useState<Set<string>>(new Set());

  /**
   * 生成Q0阶段问答对（过滤阶段）
   */
  const getQ0Items = (): QAItem[] => {
    return [
      {
        id: 'Q0.0',
        title: 'Q0.0 图片内容',
        question:
          '请判断这张图片的内容类型。如果是花卉或植物图片，回答"花卉图片"；如果不是，回答"非花卉图片"。',
        answer: getContentTypeAnswer(featureVector.content_type),
        passed: featureVector.content_type === 'plant',
        extracted_value: featureVector.content_type,
      },
      {
        id: 'Q0.1',
        title: 'Q0.1 植物类别',
        question:
          '这张花卉图片展示的是什么类型？请从以下选项中选择：叶部病害、花部病害、茎部病害、根部病害、果实病害、健康植株。',
        answer: getPlantCategoryAnswer(featureVector.plant_category),
        passed: !!featureVector.plant_category,
        extracted_value: featureVector.plant_category,
      },
      {
        id: 'Q0.2',
        title: 'Q0.2 花卉种属',
        question:
          '请识别图片中的花卉植物属于哪个属（Genus）。请用拉丁学名回答，格式为"属名 (中文名)"，例如："Rosa (蔷薇属)"。',
        answer: featureVector.flower_genus
          ? `${featureVector.flower_genus} (${getGenusName(featureVector.flower_genus)})`
          : '未能识别',
        passed: !!featureVector.flower_genus,
        extracted_value: featureVector.flower_genus,
      },
      {
        id: 'Q0.3',
        title: 'Q0.3 器官类型',
        question:
          '图片中主要展示的是植物的哪个器官？请从以下选项中选择：叶片、花朵、茎干、果实、根部。',
        answer: getOrganAnswer(featureVector.organ),
        passed: featureVector.organ === 'leaf',
        extracted_value: featureVector.organ,
      },
      {
        id: 'Q0.4',
        title: 'Q0.4 完整性',
        question:
          '图片中的器官是否完整可见，没有被严重遮挡或截断？请回答"完整可见"或"不完整"。',
        answer: getCompletenessAnswer(featureVector.completeness),
        passed: featureVector.completeness === 'intact',
        extracted_value: featureVector.completeness,
      },
      {
        id: 'Q0.5',
        title: 'Q0.5 异常检测',
        question:
          '仔细观察图片中的器官，是否存在病害症状或异常特征（如斑点、变色、粉状物、腐烂等）？如果发现明显的异常，回答"存在异常"；如果看起来健康正常，回答"无异常"。',
        answer: getAbnormalityAnswer(featureVector.has_abnormality),
        passed: featureVector.has_abnormality === 'yes',
        extracted_value: featureVector.has_abnormality,
      },
    ];
  };

  /**
   * 生成Q1-Q6阶段问答对（特征提取阶段）
   */
  const getFeatureItems = (): QAItem[] => {
    return [
      {
        id: 'Q1',
        title: 'Q1 症状类型',
        question:
          '请描述图片中病害的主要症状类型。请从以下类型中选择最符合的一项：坏死斑点、白粉病、锈病、花叶病、萎蔫、腐烂、溃疡、虫瘿。',
        answer: featureVector.symptom_type || '未提取',
        extracted_value: featureVector.symptom_type,
      },
      {
        id: 'Q2',
        title: 'Q2 病症颜色',
        question:
          '请观察病斑的颜色特征。从以下选项中选择：黑色、褐色、灰色、白色、黄色、橙色、红色、紫色。',
        answer: featureVector.colors?.join('、') || '未提取',
        extracted_value: featureVector.colors?.join(', '),
      },
      {
        id: 'Q3',
        title: 'Q3 发病位置',
        question:
          '病害主要发生在器官的哪个部位？从以下选项中选择：叶片主体、叶尖、叶缘、叶基、叶脉、叶柄、茎、花。',
        answer: featureVector.location || '未提取',
        extracted_value: featureVector.location,
      },
      {
        id: 'Q4',
        title: 'Q4 病症大小',
        question:
          '病斑的大小大概是多少？从以下选项中选择：针尖大小（<2mm）、小型（2-3mm）、中等（3-8mm）、大型（8-15mm）、融合（>15mm）。',
        answer: featureVector.size || '未提取',
        extracted_value: featureVector.size,
      },
      {
        id: 'Q5',
        title: 'Q5 分布模式',
        question:
          '病斑在器官上是如何分布的？从以下选项中选择：散点分布、聚集分布、线状分布、环状分布、边缘分布、均匀分布。',
        answer: featureVector.distribution || '未提取',
        extracted_value: featureVector.distribution,
      },
    ];
  };

  /**
   * 切换问答对展开状态
   */
  const toggleQA = (id: string) => {
    const newExpanded = new Set(expandedQA);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedQA(newExpanded);
  };

  /**
   * 展开/收起所有问答对
   */
  const toggleAll = () => {
    if (expandedQA.size > 0) {
      setExpandedQA(new Set());
    } else {
      const allIds = [...getQ0Items(), ...getFeatureItems()].map((item) => item.id);
      setExpandedQA(new Set(allIds));
    }
  };

  const q0Items = getQ0Items();
  const featureItems = getFeatureItems();

  return (
    <Card
      title={
        <div className="flex items-center justify-between">
          <span className="text-lg font-semibold">📋 VLM问答对详情</span>
          <Button size="small" onClick={toggleAll}>
            {expandedQA.size > 0 ? '收起全部' : '展开全部'}
          </Button>
        </div>
      }
      className={className}
    >
      {/* Q0阶段：过滤问答 */}
      <div className="mb-6">
        <Text strong className="text-base">
          过滤阶段 (Q0.0 - Q0.5)
        </Text>
        <div className="mt-3 space-y-2">
          {q0Items.map((item) => (
            <QARow
              key={item.id}
              item={item}
              expanded={expandedQA.has(item.id)}
              onToggle={() => toggleQA(item.id)}
            />
          ))}
        </div>
      </div>

      <Divider />

      {/* Q1-Q6阶段：特征提取问答 */}
      <div>
        <Text strong className="text-base">
          特征提取阶段 (Q1 - Q5)
        </Text>
        <div className="mt-3 space-y-2">
          {featureItems.map((item) => (
            <QARow
              key={item.id}
              item={item}
              expanded={expandedQA.has(item.id)}
              onToggle={() => toggleQA(item.id)}
            />
          ))}
        </div>
      </div>
    </Card>
  );
};

/**
 * 单个问答对行组件
 */
interface QARowProps {
  item: QAItem;
  expanded: boolean;
  onToggle: () => void;
}

const QARow: React.FC<QARowProps> = ({ item, expanded, onToggle }) => {
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* 问答对标题行 */}
      <div
        className="flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 cursor-pointer transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-center space-x-3 flex-1">
          <Text className="font-medium text-sm text-gray-700">{item.title}</Text>
          <Text className="text-sm text-gray-900">{item.answer}</Text>
        </div>

        <div className="flex items-center space-x-2">
          {/* 通过/失败标记（仅Q0阶段） */}
          {item.passed !== undefined && (
            <Tag
              color={item.passed ? 'success' : 'error'}
              icon={item.passed ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
            >
              {item.passed ? '通过' : '未通过'}
            </Tag>
          )}

          {/* 展开/收起按钮 */}
          <Button
            type="text"
            size="small"
            icon={<DownOutlined rotate={expanded ? 180 : 0} />}
          />
        </div>
      </div>

      {/* 问答对详情 */}
      {expanded && (
        <div className="p-4 bg-white border-t border-gray-200">
          {/* 问题 */}
          <div className="mb-3">
            <Text type="secondary" className="text-xs block mb-1">
              📤 原始问题 (Prompt)
            </Text>
            <Paragraph className="text-sm bg-gray-50 p-3 rounded border border-gray-200 !mb-0">
              {item.question}
            </Paragraph>
          </div>

          {/* 回答 */}
          <div>
            <Text type="secondary" className="text-xs block mb-1">
              📥 VLM原始回答
            </Text>
            <Paragraph className="text-sm bg-blue-50 p-3 rounded border border-blue-200 !mb-0">
              {item.answer}
            </Paragraph>
          </div>

          {/* 提取的结构化值 */}
          {item.extracted_value && (
            <div className="mt-2">
              <Text type="secondary" className="text-xs">
                提取值：
              </Text>
              <Tag color="blue" className="ml-2">
                {item.extracted_value}
              </Tag>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * 辅助函数：获取回答文本
 */
const getContentTypeAnswer = (type?: string): string => {
  if (type === 'plant') return '花卉图片';
  if (type === 'non_plant') return '非花卉图片';
  return '不清楚';
};

const getPlantCategoryAnswer = (category?: string): string => {
  const map: Record<string, string> = {
    flower: '花卉',
    tree: '树木',
    grass: '草本',
    vegetable: '蔬菜',
    other: '其他',
  };
  return category ? map[category] || category : '未识别';
};

const getGenusName = (genus?: string): string => {
  const map: Record<string, string> = {
    Rosa: '蔷薇属',
    Prunus: '李属',
    Tulipa: '郁金香属',
    Dianthus: '石竹属',
    Paeonia: '芍药属',
  };
  return genus ? map[genus] || genus : '';
};

const getOrganAnswer = (organ?: string): string => {
  const map: Record<string, string> = {
    leaf: '叶片',
    flower: '花朵',
    stem: '茎干',
    root: '根部',
  };
  return organ ? map[organ] || organ : '未识别';
};

const getCompletenessAnswer = (completeness?: string): string => {
  if (completeness === 'intact') return '完整可见';
  if (completeness === 'partial') return '部分可见';
  return '不清楚';
};

const getAbnormalityAnswer = (abnormality?: string): string => {
  if (abnormality === 'yes') return '存在异常';
  if (abnormality === 'no') return '无异常';
  return '不清楚';
};

/**
 * 使用示例：
 *
 * ```tsx
 * import { VLMQuestionnaire } from '@/components/diagnosis/VLMQuestionnaire';
 *
 * function DiagnosisResultPage() {
 *   const featureVector = {
 *     content_type: 'plant',
 *     plant_category: 'flower',
 *     flower_genus: 'Rosa',
 *     organ: 'leaf',
 *     completeness: 'intact',
 *     has_abnormality: 'yes',
 *     symptom_type: 'spot',
 *     colors: ['black', 'brown'],
 *     location: 'leaf_surface',
 *     size: 'medium',
 *     distribution: 'scattered',
 *   };
 *
 *   return (
 *     <VLMQuestionnaire
 *       featureVector={featureVector}
 *       defaultOpen={false}
 *     />
 *   );
 * }
 * ```
 */
