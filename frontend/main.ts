import { createApp } from 'vue';
import App from './App.vue';
import { installI18n, initializeLocaleFromBrowser } from './src/i18n';

const app = createApp(App);
installI18n(app);
initializeLocaleFromBrowser();
app.mount('#app');
