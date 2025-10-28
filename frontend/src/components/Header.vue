<template>
  <nav class="h-screen w-20 flex flex-col items-center justify-between p-2 z-20 flex-shrink-0">
    <div class="w-full flex flex-col items-center gap-4">
      <div class="h-14 flex items-center justify-center">
        <img src="../../Logo.png" alt="LifeContext" class="h-11 w-11" />
      </div>
      <div class="w-full space-y-2">
        <NavButton 
          :icon="ICONS.home"
          label="Home"
          :is-active="activeView === 'dashboard'"
          :on-click="() => onNavigate('dashboard')"
        />
        <NavButton 
          :icon="ICONS.chat"
          label="Chat"
          :is-active="activeView === 'chat'"
          :on-click="() => onNavigate('chat')"
        />
        <NavButton 
          :icon="ICONS.timeline"
          label="Timeline"
          :is-active="activeView === 'timeline'"
          :on-click="() => onNavigate('timeline')"
        />
      </div>
    </div>
    <div class="w-full flex flex-col items-center gap-2 pb-2">
      <NavButton
        :icon="ICONS.settings"
        label="Settings"
        :is-active="false"
        :on-click="onSettingsClick"
      />
      <UserAvatar class="h-10 w-10 mt-2" />
    </div>
  </nav>
</template>

<script setup lang="ts">
import UserAvatar from './UserAvatar.vue';
import NavButton from './NavButton.vue';

interface Props {
  onSettingsClick: () => void;
  activeView: 'dashboard' | 'timeline' | 'chat';
  onNavigate: (view: 'dashboard' | 'timeline' | 'chat') => void;
}

defineProps<Props>();

const ICONS = {
  home: 'M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z',
  chat: 'M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2z',
  timeline: 'M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z',
  settings: 'M19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.3-.61-.22l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65C14.46 2.18 14.25 2 14 2h-4c-.25 0-.46.18-.49.42L9.13 5.07c-.61.25-1.17.59-1.69.98l-2.49-1c-.23-.09-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19-.15-.24-.42-.12-.64l2 3.46c.12.22.39.3.61.22l2.49 1c.52.4 1.08.73 1.69.98l.38 2.65C9.54 21.82 9.75 22 10 22h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59 1.69-.98l2.49 1c.23-.09.49 0-.61.22l2-3.46c.12-.22.07-.49-.12-.64L19.43 12.98z M12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5s3.5 1.57 3.5 3.5S13.93 15.5 12 15.5z',
};
</script>