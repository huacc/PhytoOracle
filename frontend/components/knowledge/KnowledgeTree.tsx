/**
 * PhytoOracle 知识库目录树组件
 * 展示按宿主属分组的疾病目录树
 * 支持展开/折叠和选择功能
 */

import React, { useState } from 'react';
import { Tree, TreeDataNode } from 'antd';
import {
  FolderOutlined,
  FolderOpenOutlined,
  FileTextOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import type { KnowledgeTree as KnowledgeTreeType, HostTreeNode, DiseaseTreeNode, ConfigTreeNode } from '@/types';

/**
 * KnowledgeTree 组件属性
 */
interface KnowledgeTreeProps {
  /** 知识库树数据 */
  treeData: KnowledgeTreeType;
  /** 当前选中的疾病ID */
  selectedDiseaseId: string | null;
  /** 选择回调函数 */
  onSelect: (diseaseId: string) => void;
}

/**
 * 知识库目录树组件
 *
 * 功能：
 * 1. 按宿主属分组展示疾病列表
 * 2. 支持展开/折叠宿主节点
 * 3. 支持选中疾病节点
 * 4. 底部显示配置文件节点（特征本体、宿主关联、治疗方案）
 *
 * @param props - 组件属性
 * @returns React组件
 */
export const KnowledgeTree: React.FC<KnowledgeTreeProps> = ({
  treeData,
  selectedDiseaseId,
  onSelect,
}) => {
  // 展开的节点key列表（默认展开第一个宿主）
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>(
    treeData.hosts.length > 0 ? [`host-${treeData.hosts[0].genus}`] : []
  );

  /**
   * 将后端数据转换为Ant Design Tree组件需要的数据格式
   */
  const convertToTreeData = (): TreeDataNode[] => {
    const treeNodes: TreeDataNode[] = [];

    // 1. 宿主节点（父节点）
    treeData.hosts.forEach((host: HostTreeNode) => {
      const hostNode: TreeDataNode = {
        key: `host-${host.genus}`,
        title: (
          <span className="flex items-center">
            <span className="font-semibold text-gray-800">
              {host.name_zh} ({host.genus})
            </span>
            <span className="ml-2 text-xs text-gray-500">
              {host.diseases.length} 种疾病
            </span>
          </span>
        ),
        icon: (props: any) =>
          props.expanded ? <FolderOpenOutlined /> : <FolderOutlined />,
        selectable: false, // 宿主节点不可选中
        children: [],
      };

      // 2. 疾病节点（叶子节点）
      host.diseases.forEach((disease: DiseaseTreeNode) => {
        const diseaseNode: TreeDataNode = {
          key: `disease-${disease.id}`,
          title: (
            <span className="text-gray-700">
              {disease.name_zh}
              {disease.name_en && (
                <span className="ml-2 text-xs text-gray-400">
                  ({disease.name_en})
                </span>
              )}
            </span>
          ),
          icon: <FileTextOutlined />,
          isLeaf: true,
          selectable: true,
        };

        hostNode.children!.push(diseaseNode);
      });

      treeNodes.push(hostNode);
    });

    // 3. 其他配置节点（底部折叠区域）
    if (treeData.others && treeData.others.length > 0) {
      const othersNode: TreeDataNode = {
        key: 'others',
        title: (
          <span className="flex items-center text-gray-600">
            <span className="font-semibold">其他</span>
            <span className="ml-2 text-xs text-gray-500">
              配置文件
            </span>
          </span>
        ),
        icon: <SettingOutlined />,
        selectable: false,
        children: [],
      };

      treeData.others.forEach((config: ConfigTreeNode) => {
        const configNode: TreeDataNode = {
          key: `config-${config.id}`,
          title: (
            <span className="text-gray-600 text-sm">
              {config.name}
            </span>
          ),
          icon: <FileTextOutlined className="text-gray-400" />,
          isLeaf: true,
          selectable: false, // 配置节点暂不支持查看（MVP版本）
        };

        othersNode.children!.push(configNode);
      });

      treeNodes.push(othersNode);
    }

    return treeNodes;
  };

  /**
   * 处理节点展开/折叠
   * @param keys - 展开的节点key数组
   */
  const handleExpand = (keys: React.Key[]) => {
    setExpandedKeys(keys);
  };

  /**
   * 处理节点选中
   * @param selectedKeys - 选中的节点key数组
   */
  const handleSelect = (selectedKeys: React.Key[]) => {
    if (selectedKeys.length === 0) return;

    const key = selectedKeys[0] as string;

    // 只处理疾病节点的选中（key格式：disease-{diseaseId}）
    if (key.startsWith('disease-')) {
      const diseaseId = key.replace('disease-', '');
      onSelect(diseaseId);
    }
  };

  // 转换树数据
  const treeDataNodes = convertToTreeData();

  // 当前选中的节点key
  const selectedKeys = selectedDiseaseId ? [`disease-${selectedDiseaseId}`] : [];

  return (
    <div className="p-4">
      <Tree
        showIcon
        showLine={{ showLeafIcon: false }}
        expandedKeys={expandedKeys}
        selectedKeys={selectedKeys}
        treeData={treeDataNodes}
        onExpand={handleExpand}
        onSelect={handleSelect}
        // 自定义样式
        className="knowledge-tree"
        style={{
          fontSize: '14px',
        }}
      />

      {/* 自定义CSS样式 */}
      <style jsx>{`
        :global(.knowledge-tree .ant-tree-node-content-wrapper) {
          padding: 4px 8px;
          border-radius: 4px;
          transition: background-color 0.2s;
        }

        :global(.knowledge-tree .ant-tree-node-content-wrapper:hover) {
          background-color: #f5f5f5;
        }

        :global(.knowledge-tree .ant-tree-node-selected .ant-tree-node-content-wrapper) {
          background-color: #e6f7ff !important;
        }

        :global(.knowledge-tree .ant-tree-treenode) {
          padding: 2px 0;
        }

        :global(.knowledge-tree .ant-tree-iconEle) {
          margin-right: 6px;
        }
      `}</style>
    </div>
  );
};

export default KnowledgeTree;

/**
 * 示例用法：
 *
 * import { KnowledgeTree } from '@/components/knowledge';
 * import type { KnowledgeTree as KnowledgeTreeType } from '@/types';
 *
 * const treeData: KnowledgeTreeType = {
 *   hosts: [
 *     {
 *       genus: 'Rosa',
 *       name_zh: '蔷薇属',
 *       diseases: [
 *         { id: 'rose_black_spot', name_zh: '玫瑰黑斑病', name_en: 'Rose Black Spot' },
 *         { id: 'rose_powdery_mildew', name_zh: '玫瑰白粉病', name_en: 'Rose Powdery Mildew' },
 *       ],
 *     },
 *     {
 *       genus: 'Prunus',
 *       name_zh: '李属',
 *       diseases: [
 *         { id: 'cherry_leaf_spot', name_zh: '樱花叶斑病' },
 *       ],
 *     },
 *   ],
 *   others: [
 *     { id: 'feature_ontology', name: '特征本体', type: 'config' },
 *     { id: 'host_associations', name: '宿主关联', type: 'config' },
 *   ],
 * };
 *
 * function MyComponent() {
 *   const [selectedDiseaseId, setSelectedDiseaseId] = useState<string | null>(null);
 *
 *   return (
 *     <KnowledgeTree
 *       treeData={treeData}
 *       selectedDiseaseId={selectedDiseaseId}
 *       onSelect={(diseaseId) => setSelectedDiseaseId(diseaseId)}
 *     />
 *   );
 * }
 */
