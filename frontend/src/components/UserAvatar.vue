<template>
  <svg 
    viewBox="0 0 24 24" 
    fill="none" 
    xmlns="http://www.w3.org/2000/svg"
    :class="className"
  >
    <defs>
      <linearGradient id="avatarGradient" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">
        <stop stopColor="#60A5FA"/>
        <stop offset="1" stopColor="#34D399"/>
      </linearGradient>
    </defs>
    <circle cx="12" cy="12" r="10" fill="url(#avatarGradient)" />
    <path d="M12 15C15.3137 15 18 17.6863 18 21H6C6 17.6863 8.68629 15 12 15Z" fill="rgba(255,255,255,0.4)"/>
    <circle cx="12" cy="10" r="4" fill="rgba(255,255,200,0.4)"/>
  </svg>
</template>

<script setup lang="ts">
interface Props {
  className?: string;
}

withDefaults(defineProps<Props>(), {
  className: ''
});
</script>
