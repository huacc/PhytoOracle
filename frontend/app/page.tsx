/**
 * PhytoOracle 首页
 * 系统主页，展示系统介绍和快速入口
 */

'use client';

import React from 'react';
import { Card, Row, Col, Typography, Button, Space, Statistic } from 'antd';
import {
  FileImageOutlined,
  FolderOpenOutlined,
  HistoryOutlined,
  DatabaseOutlined,
  BookOutlined,
  RightOutlined,
} from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import { Layout } from '@/components/common';
import { ROUTES, APP_INFO } from '@/constants';

const { Title, Paragraph, Text } = Typography;

/**
 * 首页组件
 */
export default function HomePage() {
  const router = useRouter();

  // 功能卡片数据
  const featureCards = [
    {
      key: 'single-diagnosis',
      title: '单图诊断',
      description: '上传单张花卉图片，快速获取疾病诊断结果和详细分析',
      icon: <FileImageOutlined style={{ fontSize: 32, color: '#1890ff' }} />,
      path: ROUTES.SINGLE_DIAGNOSIS,
      color: '#e6f7ff',
    },
    {
      key: 'batch-diagnosis',
      title: '批量诊断',
      description: '一次性上传多张图片，批量诊断并导出结果报告',
      icon: <FolderOpenOutlined style={{ fontSize: 32, color: '#52c41a' }} />,
      path: ROUTES.BATCH_DIAGNOSIS,
      color: '#f6ffed',
    },
    {
      key: 'history',
      title: '诊断历史',
      description: '查看历史诊断记录，追踪诊断结果和统计数据',
      icon: <HistoryOutlined style={{ fontSize: 32, color: '#faad14' }} />,
      path: ROUTES.DIAGNOSIS_HISTORY,
      color: '#fffbe6',
    },
    {
      key: 'ontology',
      title: '本体管理',
      description: '查看和管理系统的本体结构定义和特征维度',
      icon: <DatabaseOutlined style={{ fontSize: 32, color: '#722ed1' }} />,
      path: ROUTES.ONTOLOGY_MANAGEMENT,
      color: '#f9f0ff',
    },
    {
      key: 'knowledge',
      title: '知识管理',
      description: '管理疾病知识库，编辑特征描述和VLM可理解的描述',
      icon: <BookOutlined style={{ fontSize: 32, color: '#eb2f96' }} />,
      path: ROUTES.KNOWLEDGE_MANAGEMENT,
      color: '#fff0f6',
    },
  ];

  // 系统特点
  const highlights = [
    {
      title: '本体建模',
      description: '基于植物病理学本体，结构化知识表示',
    },
    {
      title: 'VLM理解',
      description: '利用视觉大模型提取图像特征',
    },
    {
      title: '多维匹配',
      description: '特征向量匹配，精准诊断疾病',
    },
    {
      title: '可解释性',
      description: '提供完整的推理过程和诊断依据',
    },
  ];

  return (
    <Layout>
      {/* Hero Section */}
      <div className="mb-12 text-center">
        <div className="mb-4 text-6xl">🌸</div>
        <Title level={1} className="mb-4">
          {APP_INFO.NAME}
        </Title>
        <Paragraph className="text-lg text-gray-600">
          {APP_INFO.DESCRIPTION}
        </Paragraph>
        <Paragraph className="text-sm text-gray-500">
          版本 {APP_INFO.VERSION}
        </Paragraph>

        <Space size="large" className="mt-6">
          <Button
            type="primary"
            size="large"
            icon={<FileImageOutlined />}
            onClick={() => router.push(ROUTES.SINGLE_DIAGNOSIS)}
          >
            开始诊断
          </Button>
          <Button
            size="large"
            onClick={() => router.push('/docs')}
          >
            查看文档
          </Button>
        </Space>
      </div>

      {/* 功能卡片 */}
      <Title level={2} className="mb-6 text-center">
        核心功能
      </Title>

      <Row gutter={[24, 24]} className="mb-12">
        {featureCards.map((card) => (
          <Col key={card.key} xs={24} sm={12} md={8} lg={8}>
            <Card
              hoverable
              className="h-full transition-all hover:shadow-lg"
              onClick={() => router.push(card.path)}
            >
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-lg" style={{ backgroundColor: card.color }}>
                {card.icon}
              </div>
              <Title level={4} className="mb-2">
                {card.title}
              </Title>
              <Paragraph className="mb-4 text-gray-600">
                {card.description}
              </Paragraph>
              <Button type="link" className="p-0">
                立即使用 <RightOutlined />
              </Button>
            </Card>
          </Col>
        ))}
      </Row>

      {/* 系统特点 */}
      <Title level={2} className="mb-6 text-center">
        系统特点
      </Title>

      <Row gutter={[24, 24]} className="mb-12">
        {highlights.map((item, index) => (
          <Col key={index} xs={24} sm={12} md={6}>
            <Card className="h-full text-center">
              <div className="mb-2 text-4xl font-bold text-primary-500">
                {(index + 1).toString().padStart(2, '0')}
              </div>
              <Title level={5} className="mb-2">
                {item.title}
              </Title>
              <Text className="text-gray-600">{item.description}</Text>
            </Card>
          </Col>
        ))}
      </Row>

      {/* 统计数据（示例） */}
      <Card className="mb-8">
        <Row gutter={16}>
          <Col xs={24} sm={12} md={6}>
            <Statistic title="支持花卉种属" value={5} suffix="种" />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic title="知识库疾病" value={22} suffix="种" />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic title="特征维度" value={8} suffix="个" />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic title="诊断准确率" value={92} suffix="%" precision={0} />
          </Col>
        </Row>
      </Card>

      {/* 快速开始 */}
      <Card className="bg-gradient-to-r from-primary-50 to-blue-50">
        <div className="text-center">
          <Title level={3} className="mb-4">
            准备好开始了吗？
          </Title>
          <Paragraph className="mb-6 text-gray-600">
            上传您的花卉图片，让PhytoOracle帮您快速诊断疾病
          </Paragraph>
          <Space size="large">
            <Button
              type="primary"
              size="large"
              icon={<FileImageOutlined />}
              onClick={() => router.push(ROUTES.SINGLE_DIAGNOSIS)}
            >
              单图诊断
            </Button>
            <Button
              size="large"
              icon={<FolderOpenOutlined />}
              onClick={() => router.push(ROUTES.BATCH_DIAGNOSIS)}
            >
              批量诊断
            </Button>
          </Space>
        </div>
      </Card>
    </Layout>
  );
}
