<template>
  <div 
    :class="`absolute inset-0 cursor-${direction === 'horizontal' ? 'ns-resize' : 'ew-resize'} flex items-center justify-center`"
    @mousedown="handleMouseDown"
  >
    <div :class="`bg-slate-400 dark:bg-slate-600 rounded-full ${
      direction === 'horizontal' ? 'w-8 h-1' : 'h-8 w-1'
    }`"></div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  direction: 'horizontal' | 'vertical';
  onDragStart: () => void;
  onResize: (delta: number) => void;
}

const props = defineProps<Props>();

const handleMouseDown = (e: MouseEvent) => {
  e.preventDefault();
  props.onDragStart();
  
  const startY = e.clientY;
  
  const handleMouseMove = (e: MouseEvent) => {
    const deltaY = e.clientY - startY;
    props.onResize(deltaY);
  };
  
  const handleMouseUp = () => {
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
  };
  
  document.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('mouseup', handleMouseUp);
};
</script>
