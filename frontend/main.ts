import { createApp } from 'vue';
import App from './App.vue';
import { installI18n, initializeLocaleFromBrowser, setAppLocale } from './src/i18n';
import { fetchLanguagePreference } from './src/api/preferencesService';
import router from './src/router';

const app = createApp(App);
installI18n(app);
app.use(router);

const preferredLanguage = await fetchLanguagePreference();
if (preferredLanguage) {
  setAppLocale(preferredLanguage);
} else {
  initializeLocaleFromBrowser();
}

app.mount('#app');
