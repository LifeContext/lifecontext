<template>
  <div 
    :class="`bg-slate-100 dark:bg-slate-900 rounded-2xl shadow-lg p-4 flex flex-col h-full max-h-full overflow-hidden ${className} border border-slate-200 dark:border-slate-600`"
    ref="todoContainer"
  >
    <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100 mb-4">Todo</h2>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="flex justify-center items-center py-8 text-slate-500 dark:text-slate-400">
      <div class="flex items-center gap-2">
        <div class="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <span>Loading tasks...</span>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="text-center py-8 px-4">
      <p class="text-red-500 dark:text-red-400 mb-4">{{ error }}</p>
      <button 
        @click="refreshTodos?.()"
        class="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
      >
        Try Again
      </button>
    </div>

    <!-- 主要内容 -->
    <div v-else class="flex flex-col h-full min-h-0">
      <div class="mb-4 flex-shrink-0">
        <div class="flex justify-between text-sm mb-1">
          <span class="text-slate-600 dark:text-slate-400">Progress</span>
          <span class="font-medium text-slate-700 dark:text-slate-300">{{ completedTodos }} / {{ todos.length }} Completed</span>
        </div>
        <div class="h-2 bg-slate-300 dark:bg-slate-700 rounded-full overflow-hidden">
          <div 
            class="h-full rounded-full transition-all duration-500 ease-out"
            :style="{
              width: `${progressPercentage}%`,
              backgroundColor: progressColor
            }"
          ></div>
        </div>
      </div>
      
      <!-- 任务列表容器 -->
      <div class="space-y-2 flex-1 overflow-y-auto min-h-0" ref="listContainer">
        <!-- 空状态 -->
        <div v-if="todos.length === 0" class="flex flex-col items-center justify-center py-12 text-slate-500 dark:text-slate-400 animate-fade-in-up">
          <div class="mb-4 p-4 rounded-full bg-slate-100 dark:bg-slate-800 animate-float">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="currentColor" class="text-slate-400 dark:text-slate-500" viewBox="0 0 16 16">
              <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
              <path d="M5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"/>
            </svg>
          </div>
          <h3 class="text-lg font-medium text-slate-600 dark:text-slate-300 mb-2">No tasks yet</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400">Create your first task to get started</p>
        </div>

        <template v-for="(todo, index) in displayTodos" :key="todo.id">
          <!-- 分隔线：在第一个已完成的 todo 前显示 -->
          <div 
            v-if="index > 0 && !displayTodos[index - 1].status && todo.status"
            class="border-t border-slate-300 dark:border-slate-600 my-3"
          >
            <div class="text-xs text-slate-500 dark:text-slate-400 text-center -mt-2 bg-slate-100 dark:bg-slate-900 px-2 inline-block">
              Completed
            </div>
          </div>
          
          <div 
            class="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-300/50 dark:hover:bg-slate-700/50"
            :class="{ 'opacity-60': todo.status }"
          >
            <input 
              type="checkbox" 
              :checked="todo.status"
              @change="() => toggleTodo(todo.id)"
              class="w-4 h-4"
            />
            
            <div v-if="editingId !== todo.id" class="flex-1">
              <span :class="`block ${todo.status ? 'line-through text-slate-500' : 'text-slate-700 dark:text-slate-300'}`">
                {{ todo.description }}
              </span>
            </div>
            
            <div v-else class="flex-1 flex gap-2 items-center">
              <input
                v-model="editingText"
                @keyup.enter="saveEdit"
                @keyup.escape="cancelEdit"
                type="text"
                class="flex-1 px-2 py-1 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none"
                ref="editInput"
              />
              <select
                v-model="editingPriority"
                class="px-2 py-1 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 text-sm"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
            
            <span v-if="editingId !== todo.id" :class="`text-xs px-2 py-1 rounded ${ 
              todo.priority === 3 ? 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300' :
              todo.priority === 2 ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/50 dark:text-yellow-300' :
              'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' 
            }`">
              {{ todo.priority === 3 ? 'High' : todo.priority === 2 ? 'Medium' : 'Low' }}
            </span>
            
            <div v-if="editingId !== todo.id" class="flex gap-1">
              <button
                @click="startEdit(todo)"
                class="p-1 text-slate-500 hover:text-blue-500 transition-colors"
                title="Edit"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pencil-square" viewBox="0 0 16 16">
                  <path d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z"/>
                  <path fill-rule="evenodd" d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5v11z"/>
                </svg>
              </button>
              <button
                @click="confirmDelete(todo.id)"
                class="p-1 text-slate-500 hover:text-red-500 transition-colors"
                title="Delete"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
                  <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                  <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                </svg>
              </button>
            </div>
            
            <div v-else class="flex gap-1">
              <button
                @click="saveEdit"
                class="p-1 text-slate-500 hover:text-green-500 transition-colors"
                title="Save"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-check2" viewBox="0 0 16 16">
                  <path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/>
                </svg>
              </button>
              <button
                @click="cancelEdit"
                class="p-1 text-slate-500 hover:text-slate-700 transition-colors"
                title="Cancel"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-x-lg" viewBox="0 0 16 16">
                  <path d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z"/>
                </svg>
              </button>
            </div>
          </div>
        </template>
      </div>
      
      <div class="flex-shrink-0 pt-4 border-t border-slate-300 dark:border-slate-600 mt-auto">
        <div class="flex items-center gap-2">
          <input
            v-model="newTodoText"
            @keyup.enter="addTodo"
            type="text"
            placeholder="Add a new task..."
            class="flex-1 px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            v-model="newTodoPriority"
            class="px-2 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="low">Low Priority</option>
            <option value="medium">Medium Priority</option>
            <option value="high">High Priority</option>
          </select>
          <button
            @click="addTodo"
            class="px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
          >
            Add
          </button>
        </div>
      </div>
      
      <!-- 确认删除对话框 -->
      <div v-if="showDeleteConfirm" class="fixed inset-0 flex items-center justify-center bg-black/50 z-50">
        <div class="bg-white dark:bg-slate-800 rounded-lg p-4 shadow-xl">
          <p class="text-slate-700 dark:text-slate-200 mb-4">Are you sure you want to delete this task?</p>
          <div class="flex justify-end gap-2">
            <button
              @click="showDeleteConfirm = false"
              class="px-3 py-1 border border-slate-300 dark:border-slate-600 rounded text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700"
            >
              Cancel
            </button>
            <button
              @click="deleteTodo"
              class="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TodoItem } from '../../types';
import { computed, ref, onMounted, onUnmounted, watch, nextTick } from 'vue';

interface Props {
  todos: TodoItem[];
  setTodos: (todos: TodoItem[]) => void;
  className?: string;
  isLoading?: boolean;
  error?: string | null;
  refreshTodos?: () => Promise<void>;
}

const props = defineProps<Props>();

const todoContainer = ref<HTMLElement | null>(null);
const listContainer = ref<HTMLElement | null>(null);

// New todo input state
const newTodoText = ref('');
const newTodoPriority = ref<'low' | 'medium' | 'high'>('medium');

// Editing state
const editingId = ref<number | null>(null);
const editingText = ref('');
const editingPriority = ref<'low' | 'medium' | 'high'>('medium');
const editInput = ref<HTMLInputElement | null>(null);

// Delete confirmation state
const showDeleteConfirm = ref(false);
const todoToDelete = ref<number | null>(null);

// 计算应该显示的任务数量的状态
const itemHeight = ref(60);
const visibleCount = ref(0);
let resizeObserver: ResizeObserver | null = null;

// 从父组件接收的API方法
const emit = defineEmits<{
  addTodo: [text: string, priority: 'low' | 'medium' | 'high'];
  toggleTodo: [id: number];
  updateTodo: [id: number, text: string, priority: 'low' | 'medium' | 'high'];
  deleteTodo: [id: number];
}>();

// Calculate completed todos count
const completedTodos = computed(() => {
  return props.todos.filter(todo => todo.status).length;
});

// Sort todos: incomplete first, then completed
const sortedTodos = computed(() => {
  return [...props.todos].sort((a, b) => {
    // 未完成的 todo 排在前面 (status: false = 0, true = 1)
    // 如果状态相同，按 id 排序保持稳定
    if (a.status !== b.status) {
      return a.status ? 1 : -1;
    }
    return a.id - b.id;
  });
});

// 显示所有任务，通过滚动条查看
const displayTodos = computed(() => {
  return sortedTodos.value;
});

// Calculate progress percentage
const progressPercentage = computed(() => {
  if (props.todos.length === 0) return 0;
  return Math.round((completedTodos.value / props.todos.length) * 100);
});

// Set progress bar color based on progress
const progressColor = computed(() => {
  const percentage = progressPercentage.value;
  if (percentage === 100) return '#10b981';
  if (percentage >= 75) return '#3b82f6';
  if (percentage >= 50) return '#f59e0b';
  if (percentage >= 25) return '#f97316';
  return '#ef4444';
});

// Toggle todo completion status
const toggleTodo = (id: number) => {
  emit('toggleTodo', id);
};

// Add a new todo
const addTodo = async () => {
  if (!newTodoText.value.trim()) return; // Don't add empty text
  
  try {
    await emit('addTodo', newTodoText.value.trim(), newTodoPriority.value);
    
    // Clear input
    newTodoText.value = '';
    newTodoPriority.value = 'medium'; // Reset priority to default
    
    // 任务添加后重新计算显示数量
    nextTick(() => {
      calculateVisibleItems();
    });
  } catch (error) {
    console.error('Error adding todo:', error);
  }
};

// Start editing a todo
const startEdit = (todo: TodoItem) => {
  editingId.value = todo.id;
  editingText.value = todo.description;
  editingPriority.value = 
    todo.priority === 3 ? 'high' : 
    todo.priority === 2 ? 'medium' : 'low';
  
  // Focus the input field after DOM updates
  nextTick(() => {
    editInput.value?.focus();
  });
};

// Save edited todo
const saveEdit = async () => {
  if (!editingText.value.trim() || editingId.value === null) return;
  
  try {
    await emit('updateTodo', editingId.value, editingText.value.trim(), editingPriority.value);
    cancelEdit();
    
    // 编辑完成后重新计算显示数量
    nextTick(() => {
      calculateVisibleItems();
    });
  } catch (error) {
    console.error('Error saving todo:', error);
  }
};

// Cancel editing
const cancelEdit = () => {
  editingId.value = null;
  editingText.value = '';
  editingPriority.value = 'medium';
};

// Show delete confirmation
const confirmDelete = (id: number) => {
  todoToDelete.value = id;
  showDeleteConfirm.value = true;
};

// Delete todo
const deleteTodo = async () => {
  if (todoToDelete.value === null) return;
  
  try {
    await emit('deleteTodo', todoToDelete.value);
    
    // Reset delete state
    showDeleteConfirm.value = false;
    todoToDelete.value = null;
    
    // 任务删除后重新计算显示数量
    nextTick(() => {
      calculateVisibleItems();
    });
  } catch (error) {
    console.error('Error deleting todo:', error);
  }
};

// 计算可见任务数量
const calculateVisibleItems = () => {
  if (!listContainer.value) return;
  
  // 获取列表容器的实际可用高度
  const containerHeight = listContainer.value.clientHeight;
  
  // 计算可以显示的任务数量
  const calculatedCount = Math.floor(containerHeight / itemHeight.value);
  
  // 如果计算的数量小于实际任务数量，则设置可见数量，否则显示所有任务
  if (calculatedCount < sortedTodos.value.length) {
    visibleCount.value = calculatedCount;
  } else {
    visibleCount.value = 0; // 0表示显示所有任务
  }
};

// 设置 ResizeObserver 监听
const setupResizeObserver = () => {
  // 确保先断开之前的观察器（如果存在）
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
  
  // 检查浏览器是否支持 ResizeObserver
  if (typeof ResizeObserver !== 'undefined' && listContainer.value) {
    resizeObserver = new ResizeObserver(() => {
      // 使用微任务队列确保在DOM更新后执行
      Promise.resolve().then(() => {
        calculateVisibleItems();
      });
    });
    
    try {
      resizeObserver.observe(listContainer.value);
    } catch (error) {
      console.warn('Failed to observe element:', error);
    }
  }
};

// 添加轮询机制作为后备方案
let resizePollingInterval: number | null = null;
const setupResizePolling = () => {
  // 如果已经有轮询定时器，先清除
  if (resizePollingInterval !== null) {
    clearInterval(resizePollingInterval);
  }
  
  // 设置每200毫秒检查一次尺寸变化（作为ResizeObserver的后备方案）
  resizePollingInterval = window.setInterval(() => {
    calculateVisibleItems();
  }, 200);
};

// 组件挂载时初始化
onMounted(() => {
  // 初始计算
  const initialize = async () => {
    // 等待DOM完全渲染
    await nextTick();
    
    // 计算可见任务数量
    calculateVisibleItems();
    
    // 设置 ResizeObserver 监听
    setupResizeObserver();
    
    // 设置轮询作为后备方案
    setupResizePolling();
  };
  
  initialize();
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    calculateVisibleItems();
  });
});

// 组件卸载时清理
onUnmounted(() => {
  // 断开 ResizeObserver 连接
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
  
  // 清除轮询定时器
  if (resizePollingInterval !== null) {
    clearInterval(resizePollingInterval);
    resizePollingInterval = null;
  }
  
  // 移除窗口尺寸变化监听
  window.removeEventListener('resize', calculateVisibleItems);
});

// 监听 todos 列表变化
watch(() => props.todos, () => {
  nextTick(() => {
    calculateVisibleItems();
  });
}, { deep: true, immediate: true });

// 监听编辑状态变化
watch([editingId, editingText, editingPriority], () => {
  nextTick(() => {
    calculateVisibleItems();
  });
});
</script>

<style scoped>
.transition-all {
  transition-property: all;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}

.duration-500 {
  transition-duration: 500ms;
}

.ease-out {
  transition-timing-function: cubic-bezier(0, 0, 0.2, 1);
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-float {
  animation: float 3s ease-in-out infinite;
}

.animate-fade-in-up {
  animation: fadeInUp 0.6s ease-out;
}

.overflow-y-auto::-webkit-scrollbar {
  width: 10px;
  background: rgba(0, 0, 0, 0.1);
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 5px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  border-radius: 5px;
  border: 2px solid rgba(0, 0, 0, 0.1);
}

/* 深色模式下的滚动条 */
.dark .overflow-y-auto::-webkit-scrollbar {
  background: rgba(255, 255, 255, 0.1);
}

.dark .overflow-y-auto::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
}

.dark .overflow-y-auto::-webkit-scrollbar-thumb {
  background: rgb(71 85 105);
}

.dark .overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: rgb(100 116 139);
}

/* Firefox 滚动条样式 */
.overflow-y-auto {
  scrollbar-width: thin;
  scrollbar-color: rgb(148 163 184) transparent;
}

.dark .overflow-y-auto {
  scrollbar-color: rgb(71 85 105) transparent;
}
</style>
