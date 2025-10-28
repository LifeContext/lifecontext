
import type { DailyReport, TodoItem, ChatSession, Tip, ChatMessage, TimelineItem } from './types';

export const dailyReports: DailyReport[] = [
  {
    id: 1,
    date: 'July 29, 2024',
    title: 'Project Phoenix Sprint Review',
    preview: 'Completed 8 story points, identified 3 new blockers. Key takeaway: need to refine backend API for performance...',
  },
  {
    id: 2,
    date: 'July 28, 2024',
    title: 'Q3 Marketing Strategy Session',
    preview: 'Finalized budget allocation for social media campaigns. AI analysis suggests focusing on video content for higher engagement.',
  },
  {
    id: 3,
    date: 'July 27, 2024',
    title: 'UX Design Sync on New Feature',
    preview: 'User feedback on prototypes was positive. Agreed on a timeline for high-fidelity mockups. Next step: A/B testing copy.',
  },
    {
    id: 4,
    date: 'July 26, 2024',
    title: 'Client Kick-off: Acme Corp',
    preview: 'Successful first meeting. Established project goals and communication channels. AI will generate a draft project plan overnight.',
  },
  {
    id: 5,
    date: 'July 25, 2024',
    title: 'Weekly Team Stand-up',
    preview: 'All team members are on track. Discussed potential risks for the upcoming holiday season and mitigation strategies.',
  },
];

export const todoItems: TodoItem[] = [
  { id: 1, text: 'Draft email to the marketing team about Q3 results', completed: false, priority: 'high' },
  { id: 2, text: 'Prepare presentation slides for Project Phoenix review', completed: false, priority: 'high' },
  { id: 3, text: 'Schedule a follow-up meeting with the UX design team', completed: true, priority: 'medium' },
  { id: 4, text: 'Review and approve new budget proposals', completed: false, priority: 'low' },
  { id: 5, text: 'Research competitors\' new product launches', completed: false, priority: 'medium' },
];

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

export const floatingChatMessages: ChatMessage[] = [
  {
    id: 1,
    text: "Hello! I'm your proactive life engine. How can I help you be more productive today?",
    sender: 'ai',
    timestamp: '9:00 AM'
  },
  {
    id: 2,
    text: "Summarize my daily report from yesterday.",
    sender: 'user',
    timestamp: '9:01 AM'
  },
  {
    id: 3,
    text: "Of course. Yesterday's report for 'Project Phoenix Sprint Review' highlights that you completed 8 story points and identified 3 new blockers. The key recommendation is to refine the backend API for better performance.",
    sender: 'ai',
    timestamp: '9:01 AM'
  }
];


export const tips: Tip[] = [
  { 
    id: 1, 
    createdAt: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    title: 'Prioritize Marketing Email', 
    content: {
      summary: 'The marketing team needs Q3 results for their campaign adjustments. It is crucial to draft this email with key data points promptly.',
      rationale: 'Providing timely data to the marketing team allows them to optimize ongoing campaigns, justify budget allocations, and pivot strategies effectively, maximizing return on investment.',
      steps: [
        'Gather Q3 performance metrics from the analytics dashboard.',
        'Identify 3-5 key takeaways and achievements.',
        'Draft a concise email summarizing the results.',
        'Send the draft to leadership for a quick review before sending to the entire team.'
      ]
    },
    category: 'task'
  },
  { 
    id: 2, 
    createdAt: new Date(now.getTime() - 25 * 60 * 60 * 1000).toISOString(), // ~1 day ago
    title: 'Follow-up on UX Feedback', 
    content: {
      summary: 'Maintain momentum from positive prototype feedback by scheduling a follow-up with the UX team to discuss A/B testing copy.',
      rationale: 'Capitalizing on positive feedback quickly keeps the project moving and ensures that design decisions are made while the context is fresh for everyone involved.',
      steps: [
        'Identify key copy variations to test.',
        'Create a shared document for collaboration.',
        'Send a meeting invite with a clear agenda.'
      ]
    },
    category: 'collaboration'
  },
  { 
    id: 3, 
    createdAt: new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days ago
    title: 'Address Project Blockers', 
    content: {
      summary: 'The 3 new database scaling blockers for Project Phoenix are critical. Collaborate with the backend team to brainstorm solutions and prevent delays.',
      rationale: 'Unaddressed blockers can cascade, causing significant project delays and impacting team morale. Proactive collaboration is key to mitigation.',
      steps: [
        'Organize a 30-minute brainstorming session.',
        'Document all proposed solutions and their trade-offs.',
        'Assign an owner for each potential solution to investigate further.',
        'Set a deadline for the investigation phase.'
      ]
    },
    category: 'blocker'
  },
  { 
    id: 4, 
    createdAt: new Date(now.getTime() - 32 * 24 * 60 * 60 * 1000).toISOString(), // ~1 month ago
    title: 'Review Budget Proposals', 
    content: {
      summary: 'The budget proposals are currently low-priority but should be reviewed. Schedule 30 minutes to ensure they align with the Q3 video content strategy.',
      rationale: 'Even low-priority items need to be addressed to prevent them from becoming urgent. Aligning them with strategic goals ensures cohesive planning.',
      steps: [
        'Block time on your calendar for the review.',
        'Cross-reference the proposals with the Q3 strategy document.',
        'Leave comments or questions for the finance team directly in the proposal document.'
      ]
    },
    category: 'planning'
  },
  { 
    id: 5, 
    createdAt: new Date(now.getTime() - 35 * 24 * 60 * 60 * 1000).toISOString(), // ~1 month ago
    title: 'Prep for Competitor Research', 
    content: {
      summary: 'To make your competitor research more effective, create a document outlining key areas to investigate. This will help you stay focused.',
      rationale: 'Structured research is more efficient and yields more actionable insights than unstructured browsing. A clear plan prevents wasted time.',
      steps: [
        'Define 3-4 key competitors to analyze.',
        'List categories for comparison (e.g., pricing, features, marketing).',
        'Create a template in a shared document to fill out for each competitor.'
      ]
    },
    category: 'research'
  },
  { 
    id: 6, 
    createdAt: new Date(now.getTime() - 65 * 24 * 60 * 60 * 1000).toISOString(), // ~2 months ago
    title: 'Hold End of Day Sync-up', 
    content: {
      summary: 'Consider a quick sync-up with project leads to ensure all blockers have an action plan, ensuring a smooth start for tomorrow.',
      rationale: 'A brief end-of-day check-in can surface hidden issues and ensure alignment, preventing overnight delays and fostering a proactive team culture.',
      steps: [
        'Keep the meeting to 15 minutes or less.',
        'Focus only on blockers and their next steps.',
        'Confirm that every blocker has a designated owner.'
      ]
    },
    category: 'collaboration'
  },
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

// Helper to create a date for today at a specific time
const todayAt = (hours: number, minutes: number, seconds: number): string => {
    const d = new Date();
    d.setHours(hours, minutes, seconds, 0);
    return d.toISOString();
};

export const timelineItems: TimelineItem[] = [
    // Segment 1: Morning Research (9:05 - 9:15)
    { id: 1, timestamp: todayAt(9, 5, 12), url: 'https://react.dev/learn', domain: 'react.dev', title: 'Learn React - Quick Start', thumbnailUrl: '' },
    { id: 2, timestamp: todayAt(9, 7, 45), url: 'https://tailwindcss.com/docs/installation', domain: 'tailwindcss.com', title: 'Installation: Tailwind CSS', thumbnailUrl: '' },
    { id: 3, timestamp: todayAt(9, 15, 3), url: 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/Reduce', domain: 'developer.mozilla.org', title: 'Array.prototype.reduce() - MDN', thumbnailUrl: '' },

    // Segment 2: Design & Project Management (10:30 - 10:45) - 1h 15m gap
    { id: 4, timestamp: todayAt(10, 30, 21), url: 'https://www.figma.com/community', domain: 'figma.com', title: 'Figma Community - Home', thumbnailUrl: '' },
    { id: 5, timestamp: todayAt(10, 33, 58), url: 'https://m3.material.io/', domain: 'm3.material.io', title: 'Material Design', thumbnailUrl: '' },
    { id: 11, timestamp: todayAt(10, 35, 15), url: 'https://dribbble.com/', domain: 'dribbble.com', title: 'Dribbble - Discover the World’s Top Designers', thumbnailUrl: '' },
    { id: 12, timestamp: todayAt(10, 38, 0), url: 'https://coolors.co/', domain: 'coolors.co', title: 'Coolors - The super fast color schemes generator', thumbnailUrl: '' },
    { id: 13, timestamp: todayAt(10, 40, 45), url: 'https://fonts.google.com/', domain: 'fonts.google.com', title: 'Google Fonts: Browse Fonts', thumbnailUrl: '' },
    { id: 14, timestamp: todayAt(10, 42, 30), url: 'https://trello.com/', domain: 'trello.com', title: 'Trello | Bring everyone together and move projects forward.', thumbnailUrl: '' },
    { id: 6, timestamp: todayAt(10, 44, 10), url: 'https://github.com/features/copilot', domain: 'github.com', title: 'GitHub Copilot · Your AI pair programmer', thumbnailUrl: '' },


    // Segment 3: Afternoon Debugging (14:00 - 14:05) - ~3h gap
    { id: 7, timestamp: todayAt(14, 0, 55), url: 'https://stackoverflow.com/questions/5623838/rgb-to-hex-and-hex-to-rgb', domain: 'stackoverflow.com', title: 'Convert RGB to Hex and vice-versa', thumbnailUrl: '' },
    { id: 8, timestamp: todayAt(14, 5, 19), url: 'https://developer.mozilla.org/en-US/docs/Web/API/Node/contains', domain: 'developer.mozilla.org', title: 'Node.contains() - Web APIs | MDN', thumbnailUrl: '' },
    
    // Some old items to ensure filtering works
    { id: 9, timestamp: new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000).toISOString(), url: 'https://vitejs.dev/', domain: 'vitejs.dev', title: 'Vite | Next Generation Frontend Tooling', thumbnailUrl: '' },
    { id: 10, timestamp: new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000).toISOString(), url: 'https://www.typescriptlang.org/docs/', domain: 'typescriptlang.org', title: 'TypeScript Documentation', thumbnailUrl: '' },
];
