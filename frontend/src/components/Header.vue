<template>
  <nav class="h-screen w-20 flex flex-col items-center justify-between p-2 z-20 flex-shrink-0">
    <div class="w-full flex flex-col items-center gap-4">
      <div class="h-14 flex items-center justify-center">
        <img src="../../Logo.png" :alt="t('header.logoAlt')" class="h-11 w-11" />
      </div>
      <div class="w-full space-y-2">
        <NavButton 
          :icon="ICONS.home"
          :label="t('header.nav.home')"
          :is-active="activeView === 'dashboard'"
          :on-click="() => onNavigate('dashboard')"
        />
        <NavButton 
          :icon="ICONS.chat"
          :label="t('header.nav.chat')"
          :is-active="activeView === 'chat'"
          :on-click="() => onNavigate('chat')"
        />
        <NavButton 
          :icon="ICONS.timeline"
          :label="t('header.nav.timeline')"
          :is-active="activeView === 'timeline'"
          :on-click="() => onNavigate('timeline')"
        />
      </div>
    </div>
    <div class="w-full flex flex-col items-center gap-2 pb-2">
      <NavButton
        :icon="ICONS.settings"
        :label="t('header.nav.settings')"
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
import { useI18n } from '../i18n';

interface Props {
  onSettingsClick: () => void;
  activeView: 'dashboard' | 'timeline' | 'chat';
  onNavigate: (view: 'dashboard' | 'timeline' | 'chat') => void;
}

defineProps<Props>();

const { t } = useI18n();

const ICONS = {
  home: 'M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z',
  chat: 'M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2z',
  timeline: 'M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z',
  settings: 'M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94L14.4 2.81c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41L9.25 5.35c-.59.24-1.13.56-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.22-.06.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.06-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z',
};
</script>
