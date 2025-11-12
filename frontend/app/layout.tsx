import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PhytoOracle - 花卉疾病诊断系统",
  description: "基于本体建模的花卉疾病诊断系统",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.Node;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
