#!/bin/bash

# AI News MCP 快速测试脚本

echo "🧪 测试 AI News MCP Server..."
echo ""

# 测试 MCP Server 是否正常启动
echo "1️⃣ 测试服务器启动..."
timeout 3 node /Users/zewujiang/Desktop/AICo/codebuddy/ai-news-mcp/dist/index.js > /dev/null 2>&1 &
SERVER_PID=$!

sleep 1

if ps -p $SERVER_PID > /dev/null; then
    echo "✅ MCP Server 启动成功"
    kill $SERVER_PID 2>/dev/null
else
    echo "❌ MCP Server 启动失败"
    exit 1
fi

echo ""
echo "2️⃣ 检查文件结构..."

# 检查必要文件
files=(
    "dist/index.js"
    "package.json"
    "README.md"
    "IMPLEMENTATION_GUIDE.md"
    "scripts/daily-report.sh"
    "scripts/weekly-report.sh"
)

for file in "${files[@]}"; do
    if [ -f "/Users/zewujiang/Desktop/AICo/codebuddy/ai-news-mcp/$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file 缺失"
    fi
done

echo ""
echo "3️⃣ 检查报告目录..."

if [ -d "$HOME/AI-Reports/daily" ] && [ -d "$HOME/AI-Reports/weekly" ]; then
    echo "✅ 报告目录已创建"
else
    echo "⚠️  报告目录不存在，正在创建..."
    mkdir -p "$HOME/AI-Reports/daily" "$HOME/AI-Reports/weekly"
    echo "✅ 报告目录已创建"
fi

echo ""
echo "4️⃣ 检查 MCP 配置..."

MCP_CONFIG="$HOME/.codebuddy/mcp.json"
if [ -f "$MCP_CONFIG" ]; then
    if grep -q "ai-news" "$MCP_CONFIG"; then
        echo "✅ MCP 配置已添加"
    else
        echo "⚠️  MCP 配置未找到 ai-news"
    fi
else
    echo "❌ MCP 配置文件不存在"
fi

echo ""
echo "======================================"
echo "✅ AI News MCP 安装测试完成！"
echo "======================================"
echo ""
echo "📌 下一步操作："
echo "   1. 重启 CodeBuddy 以加载 MCP 配置"
echo "   2. 在 CodeBuddy 中测试命令："
echo "      > 使用 ai-news 获取今日 AI 资讯"
echo ""
echo "📖 详细文档："
echo "   - 使用指南: ai-news-mcp/IMPLEMENTATION_GUIDE.md"
echo "   - README: ai-news-mcp/README.md"
echo ""
echo "🎯 推荐工作流："
echo "   - 每日: ./ai-news-mcp/scripts/daily-report.sh"
echo "   - 每周: ./ai-news-mcp/scripts/weekly-report.sh"
