/**
 * PhytoOracle 本体结构管理页面
 * 展示系统的本体结构定义（Schema），包括特征本体、疾病本体、宿主本体、治疗本体
 * 功能：只读查看本体结构，不支持在线编辑（MVP版本）
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Layout, OntologyList, OntologyDetail } from '@/components/ontology';
import { ontologyApi } from '@/lib';
import {
  OntologyType,
  FeatureOntology,
  DiseaseSchema,
  HostSchema,
  TreatmentSchema,
  OntologyListItem,
} from '@/types';
import { message } from 'antd';
import { Loading } from '@/components/common';

/**
 * 本体数据类型（union type）
 */
type OntologyData = FeatureOntology | DiseaseSchema | HostSchema | TreatmentSchema | null;

/**
 * 本体结构管理页面组件
 */
export default function OntologyManagementPage() {
  // 当前选中的本体类型
  const [selectedType, setSelectedType] = useState<OntologyType>('feature');

  // 本体列表数据
  const [ontologyList, setOntologyList] = useState<OntologyListItem[]>([]);

  // 当前本体详情数据
  const [ontologyData, setOntologyData] = useState<OntologyData>(null);

  // 加载状态
  const [loading, setLoading] = useState(false);

  // 列表加载状态
  const [listLoading, setListLoading] = useState(false);

  /**
   * 页面加载时获取本体列表
   */
  useEffect(() => {
    fetchOntologyList();
  }, []);

  /**
   * 当选中的本体类型改变时，加载对应的本体数据
   */
  useEffect(() => {
    if (selectedType) {
      fetchOntologyData(selectedType);
    }
  }, [selectedType]);

  /**
   * 获取本体类型列表
   */
  const fetchOntologyList = async () => {
    setListLoading(true);
    try {
      const list = await ontologyApi.getOntologyList();
      setOntologyList(list);
    } catch (error) {
      console.error('获取本体列表失败:', error);
      message.error('加载本体列表失败，请稍后重试');
    } finally {
      setListLoading(false);
    }
  };

  /**
   * 根据本体类型获取对应的本体数据
   * @param type - 本体类型
   */
  const fetchOntologyData = async (type: OntologyType) => {
    setLoading(true);
    setOntologyData(null);

    try {
      let data: OntologyData = null;

      // 根据类型调用不同的API
      switch (type) {
        case 'feature':
          data = await ontologyApi.getFeatureOntology();
          break;
        case 'disease':
          data = await ontologyApi.getDiseaseSchema();
          break;
        case 'host':
          data = await ontologyApi.getHostSchema();
          break;
        case 'treatment':
          data = await ontologyApi.getTreatmentSchema();
          break;
        default:
          throw new Error(`未知的本体类型: ${type}`);
      }

      setOntologyData(data);
    } catch (error) {
      console.error(`获取${type}本体失败:`, error);
      message.error('加载本体数据失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 处理本体类型切换
   * @param type - 本体类型
   */
  const handleTypeChange = (type: OntologyType) => {
    setSelectedType(type);
  };

  /**
   * 刷新数据
   */
  const handleRefresh = () => {
    fetchOntologyList();
    fetchOntologyData(selectedType);
    message.success('数据已刷新');
  };

  return (
    <Layout>
      <div className="flex h-[calc(100vh-120px)] gap-0">
        {/* 左侧：本体类型列表 */}
        <div className="w-[280px] border-r border-gray-200 bg-white">
          <OntologyList
            ontologyList={ontologyList}
            selectedType={selectedType}
            onTypeChange={handleTypeChange}
            loading={listLoading}
          />
        </div>

        {/* 右侧：本体详情展示 */}
        <div className="flex-1 overflow-auto bg-gray-50">
          {loading ? (
            <div className="flex h-full items-center justify-center">
              <Loading tip="加载本体数据中..." />
            </div>
          ) : (
            <OntologyDetail
              type={selectedType}
              data={ontologyData}
              onRefresh={handleRefresh}
            />
          )}
        </div>
      </div>
    </Layout>
  );
}

/**
 * 示例用法：
 *
 * 该页面通过路由访问：/ontology
 *
 * 功能说明：
 * 1. 左侧列表展示所有本体类型（特征、疾病、宿主、治疗）
 * 2. 点击左侧列表项，右侧展示对应的本体详情
 * 3. 本体详情包括：
 *    - 元信息（文件名、版本、更新时间、描述）
 *    - 维度列表或字段列表
 *    - 枚举值定义（对于 enum 类型字段）
 *    - 约束规则（如模糊匹配规则）
 * 4. MVP版本为只读模式，不支持在线编辑
 * 5. 点击刷新按钮重新加载数据
 */
