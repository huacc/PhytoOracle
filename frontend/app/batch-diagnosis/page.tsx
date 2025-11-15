/**
 * PhytoOracle 批量诊断页面
 * 支持批量上传图片、批量诊断、结果展示和导出
 */

'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { Layout, Card, Row, Col, message, Typography, Divider } from 'antd';
import type { UploadFile } from 'antd';
import { FlowerGenus, DiagnosisResult } from '@/types';
import { useDiagnosisStore } from '@/stores';
import {
  BatchImageUploader,
  BatchDiagnosisForm,
  BatchProgressTracker,
  BatchResultList,
  BatchStatistics,
  BatchExport,
  BatchResultDetail,
} from '@/components/batch-diagnosis';

const { Content } = Layout;
const { Title, Paragraph } = Typography;

/**
 * 批量诊断页面组件
 *
 * 功能：
 * - 批量图片上传（最多50张）
 * - 批量诊断参数配置
 * - 批量诊断执行和进度追踪
 * - 批量诊断结果展示（列表/详情）
 * - 结果统计汇总
 * - 批量导出（JSON/CSV）
 */
export default function BatchDiagnosisPage() {
  // ==== 状态管理 ====

  // 文件列表状态
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  // 花卉种属选择
  const [flowerGenus, setFlowerGenus] = useState<FlowerGenus | undefined>();

  // 诊断进度状态
  const [diagnosing, setDiagnosing] = useState(false);
  const [progress, setProgress] = useState({ total: 0, completed: 0, failed: 0 });

  // 结果详情Modal状态
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedResultIndex, setSelectedResultIndex] = useState(0);

  // 选中的结果ID
  const [selectedResultId, setSelectedResultId] = useState<string>();

  // 从Zustand获取批量诊断状态和方法
  const { batchResults, diagnoseBatch, clearDiagnosis, isLoading, error } =
    useDiagnosisStore();

  // ==== 图片源映射（用于结果展示） ====

  const imageSources = useMemo(() => {
    const map = new Map<string, File>();
    batchResults.forEach((result, index) => {
      const file = fileList[index]?.originFileObj;
      if (file) {
        map.set(result.diagnosis_id, file);
      }
    });
    return map;
  }, [batchResults, fileList]);

  const fileNames = useMemo(() => {
    const map = new Map<string, string>();
    batchResults.forEach((result, index) => {
      const fileName = fileList[index]?.name;
      if (fileName) {
        map.set(result.diagnosis_id, fileName);
      }
    });
    return map;
  }, [batchResults, fileList]);

  // ==== 事件处理 ====

  /**
   * 开始批量诊断
   */
  const handleDiagnose = useCallback(async () => {
    if (fileList.length === 0) {
      message.warning('请先上传图片');
      return;
    }

    setDiagnosing(true);
    setProgress({ total: fileList.length, completed: 0, failed: 0 });

    try {
      // 提取文件对象 - RcFile extends File，所以可以直接使用
      const files = fileList
        .map((file) => file.originFileObj as File | undefined)
        .filter((file): file is File => file !== undefined);

      // 调用批量诊断API
      await diagnoseBatch(files, flowerGenus);

      // 模拟进度更新（实际应该从API获取）
      // 注意：这里是简化处理，实际应该轮询后端获取进度
      setProgress({ total: files.length, completed: files.length, failed: 0 });

      message.success(`批量诊断完成！共诊断 ${files.length} 张图片`);
    } catch (error: any) {
      message.error(error.message || '批量诊断失败');
      setProgress((prev) => ({
        ...prev,
        failed: prev.total - prev.completed,
      }));
    } finally {
      setDiagnosing(false);
    }
  }, [fileList, flowerGenus, diagnoseBatch]);

  /**
   * 清空所有数据
   */
  const handleClear = useCallback(() => {
    setFileList([]);
    setFlowerGenus(undefined);
    setProgress({ total: 0, completed: 0, failed: 0 });
    setDiagnosing(false);
    setDetailVisible(false);
    setSelectedResultId(undefined);
    clearDiagnosis();
    message.success('已清空所有数据');
  }, [clearDiagnosis]);

  /**
   * 查看结果详情
   */
  const handleViewDetail = useCallback((result: DiagnosisResult) => {
    const index = batchResults.findIndex(
      (r) => r.diagnosis_id === result.diagnosis_id
    );
    if (index !== -1) {
      setSelectedResultIndex(index);
      setDetailVisible(true);
    }
  }, [batchResults]);

  /**
   * 详情Modal导航：上一个
   */
  const handlePreviousDetail = useCallback(() => {
    if (selectedResultIndex > 0) {
      setSelectedResultIndex(selectedResultIndex - 1);
    }
  }, [selectedResultIndex]);

  /**
   * 详情Modal导航：下一个
   */
  const handleNextDetail = useCallback(() => {
    if (selectedResultIndex < batchResults.length - 1) {
      setSelectedResultIndex(selectedResultIndex + 1);
    }
  }, [selectedResultIndex, batchResults.length]);

  // ==== 渲染 ====

  // 是否有上传的图片
  const hasImages = fileList.length > 0;

  // 是否有诊断结果
  const hasResults = batchResults.length > 0;

  return (
    <Layout className="min-h-screen bg-gray-50">
      <Content className="max-w-7xl mx-auto px-4 py-8">
        {/* 页面标题 */}
        <Card className="mb-6">
          <Title level={2} className="mb-2">
            批量诊断
          </Title>
          <Paragraph type="secondary" className="mb-0">
            上传多张花卉病害图片，系统将自动进行批量诊断，并提供详细的诊断结果和统计信息
          </Paragraph>
        </Card>

        {/* 主要内容区域 */}
        <Row gutter={[16, 16]}>
          {/* 左侧：上传和配置区域 */}
          <Col xs={24} lg={10}>
            {/* 批量图片上传 */}
            <Card title="批量上传图片" className="mb-4">
              <BatchImageUploader
                fileList={fileList}
                onChange={setFileList}
                maxCount={50}
                disabled={diagnosing}
                showUploader={!diagnosing || !hasImages}
              />
            </Card>

            {/* 诊断参数配置 */}
            <BatchDiagnosisForm
              flowerGenus={flowerGenus}
              onGenusChange={setFlowerGenus}
              onDiagnose={handleDiagnose}
              onClear={handleClear}
              diagnosing={diagnosing}
              hasImages={hasImages}
              imageCount={fileList.length}
            />
          </Col>

          {/* 右侧：进度和结果区域 */}
          <Col xs={24} lg={14}>
            {/* 诊断进度追踪 */}
            {(diagnosing || progress.total > 0) && (
              <BatchProgressTracker
                total={progress.total}
                completed={progress.completed}
                failed={progress.failed}
                inProgress={diagnosing}
                className="mb-4"
              />
            )}

            {/* 结果统计 */}
            {hasResults && (
              <div className="mb-4">
                <BatchStatistics results={batchResults} />
              </div>
            )}

            {/* 结果列表 */}
            {hasResults && (
              <div className="mb-4">
                <BatchResultList
                  results={batchResults}
                  imageSources={imageSources}
                  fileNames={fileNames}
                  selectedId={selectedResultId}
                  onSelectChange={setSelectedResultId}
                  onViewDetail={handleViewDetail}
                  pageSize={12}
                />
              </div>
            )}

            {/* 导出按钮 */}
            {hasResults && (
              <Card className="text-center">
                <BatchExport
                  results={batchResults}
                  fileNamePrefix="phyto_oracle_batch_diagnosis"
                  disabled={diagnosing}
                  size="large"
                />
              </Card>
            )}

            {/* 空状态提示 */}
            {!hasImages && !hasResults && (
              <Card className="text-center py-12">
                <div className="text-gray-400">
                  <svg
                    className="mx-auto h-12 w-12 mb-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                  <p className="text-lg font-medium">开始批量诊断</p>
                  <p className="text-sm">
                    上传图片后点击"开始批量诊断"，系统将自动分析所有图片
                  </p>
                </div>
              </Card>
            )}
          </Col>
        </Row>

        {/* 结果详情Modal */}
        {hasResults && (
          <BatchResultDetail
            visible={detailVisible}
            result={batchResults[selectedResultIndex] || null}
            onClose={() => setDetailVisible(false)}
            hasPrevious={selectedResultIndex > 0}
            hasNext={selectedResultIndex < batchResults.length - 1}
            onPrevious={handlePreviousDetail}
            onNext={handleNextDetail}
            currentIndex={selectedResultIndex}
            totalCount={batchResults.length}
          />
        )}
      </Content>
    </Layout>
  );
}

/**
 * 页面说明：
 *
 * 该页面是批量诊断的主页面，包含以下功能：
 *
 * 1. 批量图片上传（最多50张）
 * 2. 诊断参数配置（可选宿主属）
 * 3. 批量诊断执行和进度追踪
 * 4. 批量诊断结果展示（列表/详情）
 * 5. 结果统计汇总
 * 6. 批量导出（JSON/CSV）
 *
 * 路由：/batch-diagnosis
 */
