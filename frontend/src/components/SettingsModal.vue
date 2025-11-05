<template>
  <div 
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
    @click.self="onClose"
  >
    <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-xl w-full max-w-md mx-4 flex flex-col">
      <!-- Header -->
      <header class="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700">
        <h2 class="text-xl font-bold text-slate-900 dark:text-slate-100">Settings</h2>
        <button 
          @click="onClose"
          class="p-2 rounded-full text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
          aria-label="Close settings"
        >
          <Icon path="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" class="h-6 w-6" />
        </button>
      </header>

      <!-- Content -->
      <main class="flex-1 overflow-y-auto p-4">
        <div v-if="isLoading" class="flex justify-center items-center py-8">
          <div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
            <div class="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <span class="text-sm">Loading settings...</span>
          </div>
        </div>

        <div v-else-if="error" class="text-center py-8">
          <p class="text-sm text-red-500 dark:text-red-400 mb-3">{{ error }}</p>
          <button 
            @click="loadSettings"
            class="px-3 py-1.5 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>

        <div v-else class="space-y-4">
          <!-- Tips Generation Interval Setting -->
          <div class="space-y-1.5">
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Tips Generation Interval (minutes)
            </label>
            <div class="flex items-center gap-3">
              <input
                v-model.number="localSettings.tips_interval_minutes"
                type="number"
                min="1"
                step="1"
                class="flex-1 px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                placeholder="Enter minutes"
              />
              <span class="text-xs text-slate-500 dark:text-slate-400 whitespace-nowrap">
                minutes
              </span>
            </div>
            <p v-if="localSettings.tips_interval_minutes < 1" class="text-xs text-red-500 mt-0.5">
              Interval must be greater than 0
            </p>
          </div>

          <!-- Todo Generation Interval Setting -->
          <div class="space-y-1.5">
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Todo Generation Interval (minutes)
            </label>
            <div class="flex items-center gap-3">
              <input
                v-model.number="localSettings.todo_interval_minutes"
                type="number"
                min="1"
                step="1"
                class="flex-1 px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                placeholder="Enter minutes"
              />
              <span class="text-xs text-slate-500 dark:text-slate-400 whitespace-nowrap">
                minutes
              </span>
            </div>
            <p v-if="localSettings.todo_interval_minutes < 1" class="text-xs text-red-500 mt-0.5">
              Interval must be greater than 0
            </p>
          </div>

          <!-- Daily Report Generation Time Setting -->
          <div class="space-y-1.5">
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Daily Report Generation Time
            </label>
            <p class="text-xs text-slate-500 dark:text-slate-400 mb-1.5">
              Set the time for generating daily reports
            </p>
            <div class="flex items-center gap-3">
              <div class="flex items-center gap-2">
                <label class="text-xs text-slate-600 dark:text-slate-400">Hour</label>
                <input
                  v-model.number="localSettings.daily_report_hour"
                  type="number"
                  min="0"
                  max="23"
                  step="1"
                  class="w-16 px-2.5 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                  placeholder="HH"
                />
              </div>
              <span class="text-slate-500 dark:text-slate-400">:</span>
              <div class="flex items-center gap-2">
                <label class="text-xs text-slate-600 dark:text-slate-400">Minute</label>
                <input
                  v-model.number="localSettings.daily_report_minute"
                  type="number"
                  min="0"
                  max="59"
                  step="1"
                  class="w-16 px-2.5 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                  placeholder="MM"
                />
              </div>
            </div>
            <p v-if="localSettings.daily_report_hour < 0 || localSettings.daily_report_hour > 23" class="text-xs text-red-500 mt-0.5">
              Hour must be between 0-23
            </p>
            <p v-if="localSettings.daily_report_minute < 0 || localSettings.daily_report_minute > 59" class="text-xs text-red-500 mt-0.5">
              Minute must be between 0-59
            </p>
          </div>
        </div>
      </main>

      <!-- Footer -->
      <footer class="flex items-center justify-end gap-2 p-4 border-t border-slate-200 dark:border-slate-700">
        <button
          @click="onClose"
          class="px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
        >
          Cancel
        </button>
        <button
          @click="saveSettings"
          :disabled="isSaving || !isValid"
          class="px-3 py-1.5 text-sm rounded-lg bg-blue-500 hover:bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <span v-if="isSaving">Saving...</span>
          <span v-else>Save</span>
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import Icon from './Icon.vue';
import { settingsService, type Settings } from '../api/settingsService';

interface Props {
  onClose: () => void;
}

const props = defineProps<Props>();

const isLoading = ref(true);
const isSaving = ref(false);
const error = ref<string | null>(null);
const localSettings = ref<Settings>({
  tips_interval_minutes: 60,
  todo_interval_minutes: 30,
  daily_report_hour: 8,
  daily_report_minute: 0
});

const isValid = computed(() => {
  return (
    localSettings.value.tips_interval_minutes >= 1 &&
    localSettings.value.todo_interval_minutes >= 1 &&
    localSettings.value.daily_report_hour >= 0 &&
    localSettings.value.daily_report_hour <= 23 &&
    localSettings.value.daily_report_minute >= 0 &&
    localSettings.value.daily_report_minute <= 59
  );
});

const formatTime = (hour: number, minute: number): string => {
  return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
};

const loadSettings = async () => {
  isLoading.value = true;
  error.value = null;
  
  try {
    const settings = await settingsService.getSettings();
    localSettings.value = settings;
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load settings';
    console.error('Failed to load settings:', err);
  } finally {
    isLoading.value = false;
  }
};

const saveSettings = async () => {
  if (!isValid.value || isSaving.value) {
    return;
  }

  isSaving.value = true;
  error.value = null;

  try {
    await settingsService.updateSettings(localSettings.value);
    props.onClose();
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to save settings';
    console.error('Failed to save settings:', err);
  } finally {
    isSaving.value = false;
  }
};

onMounted(() => {
  loadSettings();
});
</script>

