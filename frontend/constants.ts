
import type { ChatSession } from './types';

const now = new Date();

export const chatSessions: ChatSession[] = [
    {
        id: 1,
        title: '提醒每天早上10点开会',
        createdAt: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 1w ago
        messages: [{id: 1, text: '提醒每天早上10点开会', sender: 'user', timestamp: '10:00 AM'}]
    },
    {
        id: 2,
        title: '创建任务跟踪器',
        createdAt: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 1w ago
        messages: [{id: 1, text: '创建任务跟踪器', sender: 'user', timestamp: '11:00 AM'}]
    },
    {
        id: 3,
        title: '查询swift代码',
        createdAt: new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000).toISOString(), // 2w ago
        messages: [{id: 1, text: '查询swift代码', sender: 'user', timestamp: '2:00 PM'}]
    },
    {
        id: 4,
        title: '北京推荐景点',
        createdAt: new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000).toISOString(), // 2w ago
        messages: [{id: 1, text: '北京推荐景点', sender: 'user', timestamp: '3:00 PM'}]
    },
    {
        id: 5,
        title: '生成介绍PPT',
        createdAt: new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000).toISOString(), // 2w ago
        messages: [{id: 1, text: '生成介绍PPT', sender: 'user', timestamp: '4:00 PM'}]
    },
    {
        id: 6,
        title: '生成介绍视频',
        createdAt: new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000).toISOString(), // 2w ago
        messages: [{id: 1, text: '生成介绍视频', sender: 'user', timestamp: '5:00 PM'}]
    }
];

export const suggestedQuestions: string[] = [
    "Summarize my daily report from yesterday.",
    "What are my high-priority tasks for today?",
    "Draft a follow-up email about the Q3 marketing strategy.",
    "Are there any blockers I should be aware of?",
    "Generate a project plan based on the Acme Corp kick-off.",
    "What's the latest update on Project Phoenix?",
    "Help me prepare for my UX design sync.",
    "Brainstorm some ideas for video content.",
    "Who should I talk to about the database scaling issues?",
];
