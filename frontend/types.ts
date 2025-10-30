
export interface DailyReport {
  id: number;
  create_time: string;
  title: string;
  content: string;
}

export type Priority = 3 | 2 | 1;

export interface TodoItem {
  id: number;
  description: string;
  status: boolean;
  priority: Priority;
}

export interface ChatMessage {
  workflow_id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: string;
}

export interface ChatSession {
  id: number;
  title: string;
  createdAt: string;
  messages: ChatMessage[];
}

export type TipCategory = 'DEEP_DIVE' | 'RESOURCE_RECOMMENDATION' | 'RISK_ANALYSIS' | 'KNOWLEDGE_EXPANSION' | 'ALTERNATIVE_PERSPECTIVE';

export interface Tip {
  id: number;
  create_time: string;
  title: string;
  content: string;
  tip_type: string;
}

export interface TimelineItem {
  url: string;
}

export interface TimelineSegment {
  id: number;
  title: string;
  start_time: string;
  items: TimelineItem[];
}
