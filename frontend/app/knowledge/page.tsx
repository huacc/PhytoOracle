/**
 * PhytoOracle 知识库管理页面
 * 用于管理疾病诊断知识库，查看和编辑疾病的多维度知识
 * 采用资源管理器风格布局（左侧目录树，右侧详情区域）
 */

'use client';

import React, { useState, useEffect } from 'react';
import { message, Button } from 'antd';
import {
  SaveOutlined,
  HistoryOutlined,
  ExportOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { Layout } from '@/components/common';
import {
  KnowledgeTree as KnowledgeTreeComponent,
  DiseaseDetail,
} from '@/components/knowledge';
import { knowledgeApi } from '@/lib';
import {
  KnowledgeTree,
  DiseaseKnowledge,
  KnowledgeSnapshot,
} from '@/types';
import { Loading } from '@/components/common';

/**
 * 知识库管理页面组件
 */
export default function KnowledgeManagementPage() {
  // 知识库目录树数据
  const [treeData, setTreeData] = useState<KnowledgeTree | null>(null);

  // 当前选中的疾病ID
  const [selectedDiseaseId, setSelectedDiseaseId] = useState<string | null>(null);

  // 当前疾病知识数据
  const [diseaseKnowledge, setDiseaseKnowledge] = useState<DiseaseKnowledge | null>(null);

  // 是否处于编辑模式
  const [isEditMode, setIsEditMode] = useState(false);

  // 加载状态
  const [loading, setLoading] = useState(false);

  // 树加载状态
  const [treeLoading, setTreeLoading] = useState(false);

  /**
   * 页面加载时获取知识库目录树
   */
  useEffect(() => {
    fetchKnowledgeTree();
  }, []);

  /**
   * 当选中的疾病ID改变时，加载对应的疾病知识
   */
  useEffect(() => {
    if (selectedDiseaseId) {
      fetchDiseaseKnowledge(selectedDiseaseId);
      // 切换疾病时退出编辑模式
      setIsEditMode(false);
    }
  }, [selectedDiseaseId]);

  /**
   * 获取知识库目录树
   */
  const fetchKnowledgeTree = async () => {
    setTreeLoading(true);
    try {
      const data = await knowledgeApi.getKnowledgeTree();
      setTreeData(data);

      // 如果还没有选中疾病，自动选中第一个宿主的第一个疾病
      if (!selectedDiseaseId && data.hosts.length > 0 && data.hosts[0].diseases.length > 0) {
        setSelectedDiseaseId(data.hosts[0].diseases[0].id);
      }
    } catch (error) {
      console.error('获取知识库目录树失败:', error);
      message.error('加载知识库目录树失败，请稍后重试');
    } finally {
      setTreeLoading(false);
    }
  };

  /**
   * 获取疾病知识详情
   * @param diseaseId - 疾病ID
   */
  const fetchDiseaseKnowledge = async (diseaseId: string) => {
    setLoading(true);
    setDiseaseKnowledge(null);

    try {
      const data = await knowledgeApi.getDiseaseKnowledge(diseaseId);
      setDiseaseKnowledge(data);
    } catch (error) {
      console.error('获取疾病知识失败:', error);
      message.error('加载疾病知识失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 处理疾病选择
   * @param diseaseId - 疾病ID
   */
  const handleDiseaseSelect = (diseaseId: string) => {
    // 如果正在编辑，提示保存或取消
    if (isEditMode) {
      // TODO: 显示确认对话框，询问是否保存修改
      message.warning('当前有未保存的修改，请先保存或取消编辑');
      return;
    }

    setSelectedDiseaseId(diseaseId);
  };

  /**
   * 处理进入编辑模式
   */
  const handleEdit = () => {
    setIsEditMode(true);
  };

  /**
   * 处理取消编辑
   */
  const handleCancelEdit = () => {
    setIsEditMode(false);
    // 重新加载原始数据
    if (selectedDiseaseId) {
      fetchDiseaseKnowledge(selectedDiseaseId);
    }
  };

  /**
   * 处理保存修改
   * @param updatedKnowledge - 更新后的疾病知识
   */
  const handleSave = async (updatedKnowledge: Partial<DiseaseKnowledge>) => {
    if (!selectedDiseaseId) {
      message.error('未选中疾病');
      return;
    }

    try {
      // 先验证数据
      const validation = await knowledgeApi.validateKnowledge(updatedKnowledge);

      if (!validation.valid) {
        message.error('数据验证失败，请检查输入');
        console.error('验证错误:', validation.errors);
        return;
      }

      // 保存修改
      const result = await knowledgeApi.saveDiseaseKnowledge(
        selectedDiseaseId,
        updatedKnowledge
      );

      if (result.success) {
        message.success('保存成功');
        setIsEditMode(false);
        // 重新加载数据
        fetchDiseaseKnowledge(selectedDiseaseId);
      } else {
        message.error(result.message || '保存失败');
      }
    } catch (error) {
      console.error('保存疾病知识失败:', error);
      message.error('保存失败，请稍后重试');
    }
  };

  /**
   * 处理创建知识库快照
   */
  const handleCreateSnapshot = async () => {
    // TODO: 显示对话框，输入版本号和修改说明
    const version = prompt('请输入版本号（如：v1.2）：');
    if (!version) return;

    const description = prompt('请输入修改说明：');
    if (!description) return;

    try {
      const snapshot = await knowledgeApi.createSnapshot(version, description);
      message.success(`快照创建成功：${snapshot.version}`);
    } catch (error) {
      console.error('创建快照失败:', error);
      message.error('创建快照失败，请稍后重试');
    }
  };

  /**
   * 处理查看版本历史
   */
  const handleViewHistory = async () => {
    // TODO: 显示版本历史对话框
    try {
      const snapshots = await knowledgeApi.getSnapshots();
      console.log('快照列表:', snapshots);
      message.info(`共有 ${snapshots.length} 个历史快照`);
    } catch (error) {
      console.error('获取快照列表失败:', error);
      message.error('获取快照列表失败，请稍后重试');
    }
  };

  /**
   * 处理导出知识库
   */
  const handleExport = () => {
    // TODO: 实现导出功能
    message.info('导出功能开发中...');
  };

  /**
   * 处理刷新数据
   */
  const handleRefresh = () => {
    fetchKnowledgeTree();
    if (selectedDiseaseId) {
      fetchDiseaseKnowledge(selectedDiseaseId);
    }
  };

  return (
    <Layout showHeader showFooter>
      {/* 顶部工具栏 */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">知识库管理</h1>
          <p className="mt-1 text-sm text-gray-500">
            管理疾病诊断知识库，查看和编辑疾病的多维度知识
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            type="default"
            icon={<HistoryOutlined />}
            onClick={handleViewHistory}
          >
            版本历史
          </Button>
          <Button
            type="default"
            icon={<SaveOutlined />}
            onClick={handleCreateSnapshot}
          >
            保存快照
          </Button>
          <Button
            type="default"
            icon={<ExportOutlined />}
            onClick={handleExport}
          >
            导出
          </Button>
          <Button
            type="default"
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
          >
            刷新
          </Button>
        </div>
      </div>

      <div className="flex h-full">
        {/* 左侧：知识库目录树 */}
        <div className="w-80 border-r border-gray-200 bg-white overflow-auto">
          {treeLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loading size="large" />
            </div>
          ) : treeData ? (
            <KnowledgeTreeComponent
              treeData={treeData}
              selectedDiseaseId={selectedDiseaseId}
              onSelect={handleDiseaseSelect}
            />
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-400">
              暂无数据
            </div>
          )}
        </div>

        {/* 右侧：疾病详情区域 */}
        <div className="flex-1 bg-gray-50 overflow-auto">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loading size="large" tip="加载疾病知识中..." />
            </div>
          ) : diseaseKnowledge ? (
            <DiseaseDetail
              knowledge={diseaseKnowledge}
              isEditMode={isEditMode}
              onEdit={handleEdit}
              onCancelEdit={handleCancelEdit}
              onSave={handleSave}
            />
          ) : selectedDiseaseId ? (
            <div className="flex items-center justify-center h-64 text-gray-400">
              加载失败
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
              <p className="text-lg mb-2">请从左侧选择一个疾病</p>
              <p className="text-sm">点击疾病节点查看详细知识</p>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}

/**
 * 示例用法：
 *
 * 该页面是知识库管理的主页面，包含以下功能：
 *
 * 1. 左侧目录树展示知识库结构（按宿主属分组）
 * 2. 右侧展示选中疾病的详细知识
 * 3. 支持编辑模式，修改疾病知识
 * 4. 支持保存修改、创建快照、查看版本历史
 * 5. 支持导出知识库
 *
 * 路由：/knowledge
 *
 * 页面加载流程：
 * 1. 加载知识库目录树
 * 2. 默认选中第一个疾病
 * 3. 加载选中疾病的知识详情
 * 4. 用户可点击目录树切换疾病
 * 5. 用户可点击"编辑"按钮进入编辑模式
 * 6. 用户修改后点击"保存"保存修改
 */
