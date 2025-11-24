#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         LifeContext 便携包构建工具 (Unix/macOS)             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 找不到 Python3"
    echo "   请先安装 Python 3.8 或更高版本"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 找不到 Node.js"
    echo "   请先安装 Node.js 18 或更高版本"
    exit 1
fi

# 检查 PyInstaller
if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo "⚠️  警告: 未安装 PyInstaller"
    echo "   正在安装 PyInstaller..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo "❌ PyInstaller 安装失败"
        exit 1
    fi
fi

echo ""
echo "✅ 环境检查通过"
echo ""
echo "开始构建便携包..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 运行构建脚本
python3 build_portable.py

if [ $? -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ 构建完成！"
    echo ""
    echo "📦 输出目录: LifeContext-Portable/"
    echo "📦 ZIP 文件: LifeContext-Portable-$(uname -s).zip"
    echo ""
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ 构建失败！"
    echo "请查看上方的错误信息"
    echo ""
    exit 1
fi

