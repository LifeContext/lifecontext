import { createApp } from 'vue';
import App from './App.vue';
import { installI18n, initializeLocaleFromBrowser, setAppLocale } from './src/i18n';
import { fetchLanguagePreference } from './src/api/preferencesService';
import router from './src/router';

const app = createApp(App);
installI18n(app);
app.use(router);

async function bootstrap() {
  try {
    const preferredLanguage = await fetchLanguagePreference();
    if (preferredLanguage) {
      setAppLocale(preferredLanguage);
    } else {
      initializeLocaleFromBrowser();
    }
  } catch (error) {
    console.error('语言偏好获取失败，使用浏览器默认语言', error);
    initializeLocaleFromBrowser();
  }

  app.mount('#app');
}

void bootstrap();
