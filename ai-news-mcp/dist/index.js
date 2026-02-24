#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema, } from '@modelcontextprotocol/sdk/types.js';
import Parser from 'rss-parser';
import axios from 'axios';
import * as cheerio from 'cheerio';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
// RSS Feed 配置
const AI_NEWS_SOURCES = [
    // 顶级 AI 研究机构博客
    { name: 'OpenAI Blog', url: 'https://openai.com/blog/rss.xml', category: 'research' },
    { name: 'Anthropic Blog', url: 'https://www.anthropic.com/news/rss.xml', category: 'research' },
    { name: 'DeepMind Blog', url: 'https://deepmind.google/blog/rss.xml', category: 'research' },
    { name: 'Google AI Blog', url: 'https://blog.research.google/feeds/posts/default', category: 'research' },
    // AI 资讯平台
    { name: 'MIT Technology Review AI', url: 'https://www.technologyreview.com/feed/', category: 'news' },
    { name: 'VentureBeat AI', url: 'https://venturebeat.com/category/ai/feed/', category: 'news' },
    { name: 'The Verge AI', url: 'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml', category: 'news' },
    // 游戏行业 AI 应用
    { name: 'GameDeveloper AI', url: 'https://www.gamedeveloper.com/rss.xml', category: 'gaming' },
    { name: 'Gamasutra', url: 'https://www.gamasutra.com/rss.xml', category: 'gaming' },
];
// arXiv AI/ML 论文分类
const ARXIV_CATEGORIES = [
    'cs.AI', // Artificial Intelligence
    'cs.LG', // Machine Learning
    'cs.CV', // Computer Vision
    'cs.CL', // Computation and Language (NLP)
    'cs.GR', // Graphics (for gaming AI)
];
class AINewsServer {
    server;
    parser;
    constructor() {
        this.server = new Server({
            name: 'ai-news-mcp-server',
            version: '1.0.0',
        }, {
            capabilities: {
                tools: {},
            },
        });
        this.parser = new Parser({
            timeout: 10000,
            headers: {
                'User-Agent': 'AI-News-MCP-Server/1.0',
            },
        });
        this.setupToolHandlers();
        // 错误处理
        this.server.onerror = (error) => console.error('[MCP Error]', error);
        process.on('SIGINT', async () => {
            await this.server.close();
            process.exit(0);
        });
    }
    setupToolHandlers() {
        // 列出所有可用工具
        this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
            tools: [
                {
                    name: 'fetch_ai_news',
                    description: '获取最新 AI 资讯（支持按时间范围、分类、来源筛选）',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            timeRange: {
                                type: 'string',
                                description: '时间范围：daily(今日)、weekly(本周)、monthly(本月)',
                                enum: ['daily', 'weekly', 'monthly'],
                                default: 'daily',
                            },
                            category: {
                                type: 'string',
                                description: '资讯分类：all(全部)、research(研究机构)、news(新闻)、gaming(游戏)',
                                enum: ['all', 'research', 'news', 'gaming'],
                                default: 'all',
                            },
                            limit: {
                                type: 'number',
                                description: '返回条数限制（默认20条）',
                                default: 20,
                            },
                        },
                    },
                },
                {
                    name: 'fetch_arxiv_papers',
                    description: '获取 arXiv 最新 AI/ML 论文',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            category: {
                                type: 'string',
                                description: '论文分类：cs.AI(人工智能)、cs.LG(机器学习)、cs.CV(计算机视觉)、cs.CL(NLP)、cs.GR(图形学)',
                                enum: ['cs.AI', 'cs.LG', 'cs.CV', 'cs.CL', 'cs.GR', 'all'],
                                default: 'all',
                            },
                            maxResults: {
                                type: 'number',
                                description: '返回论文数量（默认10篇）',
                                default: 10,
                            },
                        },
                    },
                },
                {
                    name: 'generate_daily_report',
                    description: '生成每日 AI 资讯摘要报告（MBB 咨询风格）',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            includeCategories: {
                                type: 'array',
                                items: {
                                    type: 'string',
                                    enum: ['research', 'news', 'gaming', 'papers'],
                                },
                                description: '包含的资讯类别',
                                default: ['research', 'news', 'gaming'],
                            },
                        },
                    },
                },
                {
                    name: 'generate_weekly_report',
                    description: '生成每周 AI 战略分析报告（MBB 风格，含趋势预测）',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            focusAreas: {
                                type: 'array',
                                items: {
                                    type: 'string',
                                },
                                description: '重点关注领域（如：游戏AI、生成式AI、多模态等）',
                                default: ['gaming', 'generative-ai', 'multimodal'],
                            },
                        },
                    },
                },
            ],
        }));
        // 处理工具调用
        this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
            const { name, arguments: args } = request.params;
            try {
                switch (name) {
                    case 'fetch_ai_news':
                        return await this.fetchAINews(args);
                    case 'fetch_arxiv_papers':
                        return await this.fetchArxivPapers(args);
                    case 'generate_daily_report':
                        return await this.generateDailyReport(args);
                    case 'generate_weekly_report':
                        return await this.generateWeeklyReport(args);
                    default:
                        throw new Error(`未知工具: ${name}`);
                }
            }
            catch (error) {
                const errorMessage = error instanceof Error ? error.message : String(error);
                return {
                    content: [
                        {
                            type: 'text',
                            text: `错误: ${errorMessage}`,
                        },
                    ],
                };
            }
        });
    }
    async fetchAINews(args) {
        const { timeRange = 'daily', category = 'all', limit = 20 } = args;
        const now = new Date();
        const timeRangeMs = {
            daily: 24 * 60 * 60 * 1000,
            weekly: 7 * 24 * 60 * 60 * 1000,
            monthly: 30 * 24 * 60 * 60 * 1000,
        };
        const cutoffTime = new Date(now.getTime() - timeRangeMs[timeRange]);
        // 筛选 RSS 源
        const sources = category === 'all'
            ? AI_NEWS_SOURCES
            : AI_NEWS_SOURCES.filter(s => s.category === category);
        const allNews = [];
        // 并发抓取所有源
        await Promise.allSettled(sources.map(async (source) => {
            try {
                const feed = await this.parser.parseURL(source.url);
                feed.items.forEach(item => {
                    const pubDate = item.pubDate ? new Date(item.pubDate) : new Date();
                    if (pubDate >= cutoffTime) {
                        allNews.push({
                            title: item.title || '无标题',
                            link: item.link || '',
                            pubDate: format(pubDate, 'yyyy-MM-dd HH:mm', { locale: zhCN }),
                            source: source.name,
                            category: source.category,
                            summary: item.contentSnippet?.substring(0, 200),
                            author: item.creator || item.author,
                        });
                    }
                });
            }
            catch (error) {
                console.error(`获取 ${source.name} 失败:`, error);
            }
        }));
        // 按时间排序，最新的在前
        allNews.sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime());
        const result = allNews.slice(0, limit);
        // 生成 Markdown 格式报告
        let report = `# 🤖 AI 资讯汇总\n\n`;
        report += `**时间范围**: ${timeRange === 'daily' ? '今日' : timeRange === 'weekly' ? '本周' : '本月'}\n`;
        report += `**分类**: ${category === 'all' ? '全部' : category}\n`;
        report += `**共 ${result.length} 条资讯**\n\n`;
        report += `---\n\n`;
        result.forEach((news, index) => {
            report += `## ${index + 1}. ${news.title}\n\n`;
            report += `- **来源**: ${news.source} (${news.category})\n`;
            report += `- **时间**: ${news.pubDate}\n`;
            if (news.author)
                report += `- **作者**: ${news.author}\n`;
            report += `- **链接**: ${news.link}\n`;
            if (news.summary)
                report += `\n${news.summary}...\n`;
            report += `\n---\n\n`;
        });
        return {
            content: [
                {
                    type: 'text',
                    text: report,
                },
            ],
        };
    }
    async fetchArxivPapers(args) {
        const { category = 'all', maxResults = 10 } = args;
        const categories = category === 'all' ? ARXIV_CATEGORIES : [category];
        const searchQuery = categories.map(cat => `cat:${cat}`).join('+OR+');
        const apiUrl = `http://export.arxiv.org/api/query?search_query=${searchQuery}&sortBy=submittedDate&sortOrder=descending&max_results=${maxResults}`;
        try {
            const response = await axios.get(apiUrl, {
                timeout: 15000,
                headers: { 'User-Agent': 'AI-News-MCP-Server/1.0' },
            });
            const $ = cheerio.load(response.data, { xmlMode: true });
            let report = `# 📄 arXiv 最新论文\n\n`;
            report += `**分类**: ${category}\n`;
            report += `**数量**: ${maxResults} 篇\n\n`;
            report += `---\n\n`;
            $('entry').each((index, element) => {
                const title = $(element).find('title').text().trim();
                const summary = $(element).find('summary').text().trim().substring(0, 300);
                const authors = $(element).find('author name').map((_, el) => $(el).text()).get().join(', ');
                const link = $(element).find('id').text();
                const published = $(element).find('published').text();
                report += `## ${index + 1}. ${title}\n\n`;
                report += `- **作者**: ${authors}\n`;
                report += `- **发布**: ${format(new Date(published), 'yyyy-MM-dd', { locale: zhCN })}\n`;
                report += `- **链接**: ${link}\n\n`;
                report += `**摘要**: ${summary}...\n\n`;
                report += `---\n\n`;
            });
            return {
                content: [{ type: 'text', text: report }],
            };
        }
        catch (error) {
            throw new Error(`获取 arXiv 论文失败: ${error}`);
        }
    }
    async generateDailyReport(args) {
        const { includeCategories = ['research', 'news', 'gaming'] } = args;
        let report = `# 📊 AI 前沿资讯 - 每日简报\n\n`;
        report += `**日期**: ${format(new Date(), 'yyyy年MM月dd日', { locale: zhCN })}\n\n`;
        report += `---\n\n`;
        // 获取各分类资讯
        for (const cat of includeCategories) {
            const newsResult = await this.fetchAINews({
                timeRange: 'daily',
                category: cat,
                limit: 5,
            });
            report += `## ${this.getCategoryName(cat)}\n\n`;
            report += newsResult.content[0].text.split('---\n\n').slice(1).join('');
            report += `\n`;
        }
        // 添加 MBB 风格的关键洞察
        report += `\n## 💡 关键洞察 (Key Insights)\n\n`;
        report += `1. **趋势观察**: [待 AI 分析填充]\n`;
        report += `2. **竞争动态**: [待 AI 分析填充]\n`;
        report += `3. **战略建议**: [待 AI 分析填充]\n\n`;
        return {
            content: [{ type: 'text', text: report }],
        };
    }
    async generateWeeklyReport(args) {
        const { focusAreas = ['gaming', 'generative-ai', 'multimodal'] } = args;
        let report = `# 📈 AI 战略分析 - 每周深度报告\n\n`;
        report += `**周期**: ${format(new Date(), 'yyyy年第ww周', { locale: zhCN })}\n\n`;
        report += `---\n\n`;
        report += `## 一、核心发现 (Executive Summary)\n\n`;
        report += `[待填充：本周最重要的3-5个发现]\n\n`;
        report += `## 二、行业动态 (Industry Trends)\n\n`;
        const weeklyNews = await this.fetchAINews({
            timeRange: 'weekly',
            category: 'all',
            limit: 30,
        });
        report += weeklyNews.content[0].text;
        report += `\n## 三、战略建议 (Strategic Recommendations)\n\n`;
        report += `### 3.1 短期行动 (0-3个月)\n`;
        report += `- [待 AI 分析填充]\n\n`;
        report += `### 3.2 中期规划 (3-12个月)\n`;
        report += `- [待 AI 分析填充]\n\n`;
        report += `### 3.3 长期展望 (1-3年)\n`;
        report += `- [待 AI 分析填充]\n\n`;
        report += `## 四、风险与机遇 (Risks & Opportunities)\n\n`;
        report += `**机遇**:\n- [待分析]\n\n`;
        report += `**风险**:\n- [待分析]\n\n`;
        return {
            content: [{ type: 'text', text: report }],
        };
    }
    getCategoryName(category) {
        const names = {
            research: '🔬 顶级研究机构',
            news: '📰 行业新闻',
            gaming: '🎮 游戏行业',
            papers: '📄 学术论文',
        };
        return names[category] || category;
    }
    async run() {
        const transport = new StdioServerTransport();
        await this.server.connect(transport);
        console.error('AI News MCP Server 运行中...');
    }
}
const server = new AINewsServer();
server.run().catch(console.error);
//# sourceMappingURL=index.js.map