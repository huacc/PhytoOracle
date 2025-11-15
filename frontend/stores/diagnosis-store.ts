/**
 * PhytoOracle 诊断状态管理
 * 管理诊断相关的全局状态
 */

import { create } from 'zustand';
import { DiagnosisResult, FlowerGenus } from '@/types';
import { diagnosisApi } from '@/lib';

/**
 * 诊断状态接口
 */
interface DiagnosisState {
  /** 当前诊断结果 */
  currentResult: DiagnosisResult | null;
  /** 批量诊断结果列表 */
  batchResults: DiagnosisResult[];
  /** 当前查看的批量结果索引 */
  currentBatchIndex: number;
  /** 诊断加载状态 */
  isLoading: boolean;
  /** 诊断错误信息 */
  error: string | null;

  /** 执行单图诊断 */
  diagnoseSingle: (image: File, flowerGenus?: FlowerGenus) => Promise<void>;
  /** 执行批量诊断 */
  diagnoseBatch: (images: File[], flowerGenus?: FlowerGenus) => Promise<void>;
  /** 设置当前结果 */
  setCurrentResult: (result: DiagnosisResult | null) => void;
  /** 设置批量结果 */
  setBatchResults: (results: DiagnosisResult[]) => void;
  /** 切换批量结果索引 */
  setCurrentBatchIndex: (index: number) => void;
  /** 下一张 */
  nextBatchResult: () => void;
  /** 上一张 */
  previousBatchResult: () => void;
  /** 清除诊断数据 */
  clearDiagnosis: () => void;
  /** 提交反馈 */
  submitFeedback: (diagnosisId: string, feedback: 'correct' | 'incorrect') => Promise<void>;
}

/**
 * 诊断状态Store
 */
export const useDiagnosisStore = create<DiagnosisState>((set, get) => ({
  currentResult: null,
  batchResults: [],
  currentBatchIndex: 0,
  isLoading: false,
  error: null,

  /**
   * 执行单图诊断
   */
  diagnoseSingle: async (image: File, flowerGenus?: FlowerGenus) => {
    set({ isLoading: true, error: null });

    try {
      const result = await diagnosisApi.diagnoseSingle({
        image,
        flower_genus: flowerGenus,
      });

      set({ currentResult: result, isLoading: false });
    } catch (error: any) {
      set({
        error: error.message || '诊断失败',
        isLoading: false,
      });
      throw error;
    }
  },

  /**
   * 执行批量诊断
   */
  diagnoseBatch: async (images: File[], flowerGenus?: FlowerGenus) => {
    set({ isLoading: true, error: null });

    try {
      const result = await diagnosisApi.diagnoseBatch(images, flowerGenus);

      set({
        batchResults: result.results,
        currentBatchIndex: 0,
        currentResult: result.results[0] || null,
        isLoading: false,
      });
    } catch (error: any) {
      set({
        error: error.message || '批量诊断失败',
        isLoading: false,
      });
      throw error;
    }
  },

  /**
   * 设置当前结果
   */
  setCurrentResult: (result: DiagnosisResult | null) => {
    set({ currentResult: result });
  },

  /**
   * 设置批量结果
   */
  setBatchResults: (results: DiagnosisResult[]) => {
    set({
      batchResults: results,
      currentBatchIndex: 0,
      currentResult: results[0] || null,
    });
  },

  /**
   * 切换批量结果索引
   */
  setCurrentBatchIndex: (index: number) => {
    const { batchResults } = get();
    if (index >= 0 && index < batchResults.length) {
      set({
        currentBatchIndex: index,
        currentResult: batchResults[index],
      });
    }
  },

  /**
   * 下一张
   */
  nextBatchResult: () => {
    const { currentBatchIndex, batchResults } = get();
    if (currentBatchIndex < batchResults.length - 1) {
      const newIndex = currentBatchIndex + 1;
      set({
        currentBatchIndex: newIndex,
        currentResult: batchResults[newIndex],
      });
    }
  },

  /**
   * 上一张
   */
  previousBatchResult: () => {
    const { currentBatchIndex, batchResults } = get();
    if (currentBatchIndex > 0) {
      const newIndex = currentBatchIndex - 1;
      set({
        currentBatchIndex: newIndex,
        currentResult: batchResults[newIndex],
      });
    }
  },

  /**
   * 清除诊断数据
   */
  clearDiagnosis: () => {
    set({
      currentResult: null,
      batchResults: [],
      currentBatchIndex: 0,
      error: null,
    });
  },

  /**
   * 提交反馈
   */
  submitFeedback: async (diagnosisId: string, feedback: 'correct' | 'incorrect') => {
    try {
      await diagnosisApi.submitFeedback(diagnosisId, feedback);

      // 更新当前结果的反馈状态
      const { currentResult, batchResults, currentBatchIndex } = get();

      if (currentResult && currentResult.diagnosis_id === diagnosisId) {
        set({
          currentResult: {
            ...currentResult,
            user_feedback: feedback,
          },
        });
      }

      // 更新批量结果中的反馈状态
      if (batchResults.length > 0) {
        const updatedResults = batchResults.map((result) =>
          result.diagnosis_id === diagnosisId
            ? { ...result, user_feedback: feedback }
            : result
        );
        set({ batchResults: updatedResults });
      }
    } catch (error: any) {
      console.error('Submit feedback error:', error);
      throw error;
    }
  },
}));
