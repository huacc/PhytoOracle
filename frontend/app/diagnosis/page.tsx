/**
 * PhytoOracle - 单图诊断页面
 * 功能：花卉病害单图诊断的完整功能页面
 *
 * @author PhytoOracle Team
 * @version 1.0.0
 */

'use client';

import React, { useState } from 'react';
import { message } from 'antd';
import { ImageUploader } from '@/components/diagnosis/ImageUploader';
import { DiagnosisForm } from '@/components/diagnosis/DiagnosisForm';
import { DiagnosisResult } from '@/components/diagnosis/DiagnosisResult';
import { useDiagnosisStore } from '@/stores/diagnosis-store';
import { FlowerGenus } from '@/types';

/**
 * 单图诊断页面组件
 *
 * 功能流程：
 * 1. 用户上传图片（ImageUploader）
 * 2. 用户选择花卉种属（可选）并点击开始诊断（DiagnosisForm）
 * 3. 调用诊断API（useDiagnosisStore）
 * 4. 展示诊断结果（DiagnosisResult）
 * 5. 用户提供反馈（正确/错误）
 *
 * 状态管理：
 * - selectedFile: 当前选择的图片文件
 * - flowerGenus: 当前选择的花卉种属
 * - Zustand Store: loading, error, currentResult
 *
 * @returns 单图诊断页面
 */
export default function DiagnosisPage() {
  // 本地状态：选择的文件
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  // 本地状态：选择的花卉种属
  const [flowerGenus, setFlowerGenus] = useState<FlowerGenus | undefined>(undefined);

  // Zustand 全局状态：诊断相关状态
  const {
    currentResult,
    isLoading,
    error,
    diagnoseSingle,
    setCurrentResult,
    clearDiagnosis,
  } = useDiagnosisStore();

  /**
   * 处理图片文件选择
   * @param file - 选择的图片文件
   */
  const handleFileSelect = (file: File | null) => {
    setSelectedFile(file);
    // 选择新文件时清空之前的诊断结果和错误
    if (file) {
      setCurrentResult(null);
    }
  };

  /**
   * 处理花卉种属变更
   * @param genus - 选择的花卉种属
   */
  const handleGenusChange = (genus: FlowerGenus | undefined) => {
    setFlowerGenus(genus);
  };

  /**
   * 开始诊断
   * 调用Zustand store的diagnoseSingle方法
   */
  const handleDiagnose = async () => {
    // 验证是否选择了文件
    if (!selectedFile) {
      message.warning('请先上传图片');
      return;
    }

    try {
      // 调用诊断API（通过Zustand store）
      await diagnoseSingle(selectedFile, flowerGenus);

      // 诊断成功提示
      message.success('诊断完成！');
    } catch (err) {
      // 错误处理已在store中完成
      console.error('诊断失败:', err);
      message.error('诊断失败，请重试');
    }
  };

  /**
   * 重置表单
   * 清空所有状态，回到初始状态
   */
  const handleReset = () => {
    setSelectedFile(null);
    setFlowerGenus(undefined);
    clearDiagnosis();
    message.info('已重置，请重新上传图片');
  };

  /**
   * 处理反馈：诊断正确
   * @param resultId - 诊断结果ID
   */
  const handleFeedbackCorrect = async (resultId: string) => {
    try {
      // TODO: 调用反馈API（需要在P5.3阶段实现）
      console.log('诊断正确反馈:', resultId);
      message.success('感谢您的反馈！');
    } catch (err) {
      console.error('提交反馈失败:', err);
      message.error('提交反馈失败，请重试');
    }
  };

  /**
   * 处理反馈：诊断错误
   * @param resultId - 诊断结果ID
   */
  const handleFeedbackIncorrect = async (resultId: string) => {
    try {
      // TODO: 调用反馈API（需要在P5.3阶段实现）
      console.log('诊断错误反馈:', resultId);
      message.warning('感谢您的反馈，我们会改进诊断准确率！');
    } catch (err) {
      console.error('提交反馈失败:', err);
      message.error('提交反馈失败，请重试');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🌸 单图诊断
          </h1>
          <p className="text-gray-600">
            上传花卉病害图片，使用视觉语言模型进行智能诊断
          </p>
        </div>

        {/* 主要内容区域 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 左侧：图片上传和诊断表单 */}
          <div className="space-y-6">
            {/* 图片上传区域 */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4">📤 上传图片</h2>
              <ImageUploader
                value={selectedFile}
                onFileSelect={handleFileSelect}
                disabled={isLoading}
              />
            </div>

            {/* 诊断参数表单 */}
            <DiagnosisForm
              flowerGenus={flowerGenus}
              onGenusChange={handleGenusChange}
              onDiagnose={handleDiagnose}
              onReset={handleReset}
              diagnosing={isLoading}
              hasImage={!!selectedFile}
            />
          </div>

          {/* 右侧：诊断结果展示 */}
          <div>
            <DiagnosisResult
              result={currentResult}
              loading={isLoading}
              error={error}
              onFeedbackCorrect={handleFeedbackCorrect}
              onFeedbackIncorrect={handleFeedbackIncorrect}
            />
          </div>
        </div>

        {/* 页面底部说明 */}
        <div className="mt-12 p-6 bg-white rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold mb-4 text-gray-900">
            💡 使用说明
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm text-gray-600">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">1. 上传图片</h4>
              <p>支持拖拽上传或点击选择，文件大小不超过10MB</p>
              <p className="mt-1">支持格式：JPG、PNG、HEIC、WEBP</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">2. 选择种属</h4>
              <p>可选择花卉种属以提高诊断准确率</p>
              <p className="mt-1">留空则系统自动识别（需约300-500ms额外时间）</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">3. 查看结果</h4>
              <p>诊断结果包含疾病信息、特征分析和推理过程</p>
              <p className="mt-1">请提供反馈以帮助改进诊断系统</p>
            </div>
          </div>
        </div>

        {/* 技术说明 */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-xs text-blue-800">
            <strong>技术说明：</strong>
            本系统使用视觉语言模型(VLM)提取特征向量，并通过本体推理匹配疾病。
            诊断过程包括Q0阶段过滤(Q0.0-Q0.5)和特征提取(Q1-Q6)，最终通过加权评分算法得出诊断结果。
          </p>
        </div>
      </div>
    </div>
  );
}
