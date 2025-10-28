<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white dark:bg-slate-800 rounded-2xl p-6 max-w-md w-full mx-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-bold text-slate-900 dark:text-slate-100">Settings</h2>
        <button 
          @click="onClose"
          class="p-2 rounded-full text-slate-500 dark:text-slate-400 hover:bg-slate-300 dark:hover:bg-slate-700"
        >
          <Icon path="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" class="h-6 w-6" />
        </button>
      </div>
      <div class="space-y-4">
        <p class="text-slate-600 dark:text-slate-400">Settings content goes here...</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Icon from './Icon.vue';

interface Props {
  onClose: () => void;
}

defineProps<Props>();
</script>
