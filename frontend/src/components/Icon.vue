<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    :class="className"
  >
    <path fill-rule="evenodd" :d="path" clip-rule="evenodd" />
  </svg>
</template>

<script setup lang="ts">
interface Props {
  path: string;
  className?: string;
}

withDefaults(defineProps<Props>(), {
  className: 'h-6 w-6'
});
</script>
