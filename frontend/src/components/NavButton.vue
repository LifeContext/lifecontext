<template>
  <button
    @click="onClick"
    :class="`w-full flex flex-col items-center justify-center aspect-square rounded-xl transition-all duration-200 group ${
      isActive
      ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
      : 'text-slate-600 dark:text-slate-400 hover:bg-white dark:hover:bg-slate-700 hover:-translate-y-0.5 hover:shadow-md'
    }`"
  >
    <Icon :path="icon" class="h-6 w-6" />
    <span class="mt-1 text-xs font-medium tracking-wide">{{ label }}</span>
  </button>
</template>

<script setup lang="ts">
import Icon from './Icon.vue';

interface Props {
  icon: string;
  label: string;
  isActive: boolean;
  onClick: () => void;
}

defineProps<Props>();
</script>
