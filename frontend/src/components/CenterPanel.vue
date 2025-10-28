<template>
  <div class="flex flex-col h-full min-h-0">
    <div :style="{ height: `${promptHeight}px` }" class="flex-shrink-0">
      <TipsPanel :on-select-tip="onSelectTip" />
    </div>
    
    <div class="h-4 flex-shrink-0 relative">
      <ResizeHandle
        direction="horizontal"
        :on-drag-start="handleResizeStart"
        :on-resize="handleResize"
      />
    </div>

    <TodoList 
      :todos="todos" 
      :set-todos="setTodos"
      :is-loading="isLoading"
      :error="error"
      :refresh-todos="refreshTodos"
      @addTodo="(text, priority) => { $emit('addTodo', text, priority); }"
      @toggleTodo="(id) => { $emit('toggleTodo', id); }"
      @updateTodo="(id, text, priority) => { $emit('updateTodo', id, text, priority); }"
      @deleteTodo="(id) => { $emit('deleteTodo', id); }"
      class="flex-1 min-h-0" 
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import TipsPanel from './AIPrompt.vue';
import TodoList from './TodoList.vue';
import ResizeHandle from './ResizeHandle.vue';
import type { TodoItem, Tip } from '../../types';

interface Props {
  todos: TodoItem[];
  setTodos: (todos: TodoItem[]) => void;
  onSelectTip: (tip: Tip) => void;
  isLoading?: boolean;
  error?: string | null;
  refreshTodos?: () => Promise<void>;
}

const props = defineProps<Props>();

// 定义 emit 事件
const emit = defineEmits<{
  addTodo: [text: string, priority: 'low' | 'medium' | 'high'];
  toggleTodo: [id: number];
  updateTodo: [id: number, text: string, priority: 'low' | 'medium' | 'high'];
  deleteTodo: [id: number];
}>();

const promptHeight = ref(320);
const dragStartHeight = ref(0);

const handleResizeStart = () => {
  dragStartHeight.value = promptHeight.value;
};

const handleResize = (deltaY: number) => {
  const newHeight = dragStartHeight.value + deltaY;
  const constrainedHeight = Math.max(150, Math.min(400, newHeight));
  promptHeight.value = constrainedHeight;
};
</script>