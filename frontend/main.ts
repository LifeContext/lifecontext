import { createApp } from 'vue';
import App from './App.vue';
import { installI18n, initializeLocaleFromBrowser, setAppLocale } from './src/i18n';
import { fetchLanguagePreference } from './src/api/preferencesService';
import router from './src/router';

const app = createApp(App);
installI18n(app);
app.use(router);

// 包装在异步函数中以避免 top-level await 的兼容性问题
async function initializeApp() {
  try {
    const preferredLanguage = await fetchLanguagePreference();
    if (preferredLanguage) {
      setAppLocale(preferredLanguage);
    } else {
      initializeLocaleFromBrowser();
    }
  } catch (error) {
    console.warn('Failed to fetch language preference, using browser default:', error);
    initializeLocaleFromBrowser();
  }
  
  app.mount('#app');
}

initializeApp();
