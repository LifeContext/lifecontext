<template>
  <div 
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
    @click.self="onClose"
  >
    <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-xl w-full max-w-md mx-4 flex flex-col">
      <!-- Header -->
      <header class="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700">
        <h2 class="text-xl font-bold text-slate-900 dark:text-slate-100">{{ t('settings.title') }}</h2>
        <button 
          @click="onClose"
          class="p-2 rounded-full text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
          :aria-label="t('common.close')"
        >
          <Icon path="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" class="h-6 w-6" />
        </button>
      </header>

      <!-- Content -->
      <main class="flex-1 overflow-y-auto p-4 custom-scrollbar">
        <div v-if="isLoading" class="flex justify-center items-center py-8">
          <div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
            <div class="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <span class="text-sm">{{ t('settings.loading') }}</span>
          </div>
        </div>

        <div v-else-if="error" class="text-center py-8">
          <p class="text-sm text-red-500 dark:text-red-400 mb-3">{{ error }}</p>
          <button 
            @click="loadSettings"
            class="px-3 py-1.5 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
          >
            {{ t('settings.retry') }}
          </button>
        </div>

        <div v-else class="space-y-4">
          <!-- Tips Generation Interval Setting -->
          <div class="space-y-1">
            <div class="flex items-center justify-between gap-6">
              <label class="text-sm font-medium text-slate-700 dark:text-slate-300 flex-1">
                {{ t('settings.fields.tipsInterval') }}
              </label>
              <input
                v-model.number="localSettings.tips_interval_minutes"
                type="number"
                min="1"
                step="1"
                class="w-16 px-2 py-1 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none text-center"
                :placeholder="t('settings.placeholders.minutes')"
              />
            </div>
            <p v-if="localSettings.tips_interval_minutes < 1" class="text-xs text-red-500 text-right">
              {{ t('settings.errors.intervalPositive') }}
            </p>
          </div>

          <!-- Todo Generation Interval Setting -->
          <div class="space-y-1">
            <div class="flex items-center justify-between gap-6">
              <label class="text-sm font-medium text-slate-700 dark:text-slate-300 flex-1">
                {{ t('settings.fields.todoInterval') }}
              </label>
              <input
                v-model.number="localSettings.todo_interval_minutes"
                type="number"
                min="1"
                step="1"
                class="w-16 px-2 py-1 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none text-center"
                :placeholder="t('settings.placeholders.minutes')"
              />
            </div>
            <p v-if="localSettings.todo_interval_minutes < 1" class="text-xs text-red-500 text-right">
              {{ t('settings.errors.intervalPositive') }}
            </p>
          </div>

          <!-- Daily Report Generation Time Setting -->
          <div class="space-y-1">
            <div class="flex items-center justify-between gap-6">
              <label class="text-sm font-medium text-slate-700 dark:text-slate-300 flex-1">
                {{ t('settings.fields.dailyReportTime') }}
              </label>
              <div class="flex items-center gap-2">
                <input
                  v-model.number="localSettings.daily_report_hour"
                  type="number"
                  min="0"
                  max="23"
                  step="1"
                  class="w-16 px-2 py-1 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none text-center"
                  :placeholder="t('settings.placeholders.hour')"
                />
                <span class="text-slate-500 dark:text-slate-400">:</span>
                <input
                  v-model.number="localSettings.daily_report_minute"
                  type="number"
                  min="0"
                  max="59"
                  step="1"
                  class="w-16 px-2 py-1 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none text-center"
                  :placeholder="t('settings.placeholders.minute')"
                />
              </div>
            </div>
            <p v-if="localSettings.daily_report_hour < 0 || localSettings.daily_report_hour > 23" class="text-xs text-red-500 text-right">
              {{ t('settings.errors.hourRange') }}
            </p>
            <p v-if="localSettings.daily_report_minute < 0 || localSettings.daily_report_minute > 59" class="text-xs text-red-500 text-right">
              {{ t('settings.errors.minuteRange') }}
            </p>
          </div>

          <!-- Excluded Domains Setting -->
          <div class="space-y-2">
            <label class="text-sm font-medium text-slate-700 dark:text-slate-300 flex-1">
              {{ t('settings.fields.excludedDomains') }}
            </label>
            <!-- Input Type Selector -->
            <div class="flex gap-4 text-sm">
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  :value="'domain'"
                  v-model="excludedInputType"
                  class="w-4 h-4 text-blue-500 border-slate-300 dark:border-slate-600 focus:ring-2 focus:ring-blue-500"
                />
                <span class="text-slate-700 dark:text-slate-300">{{ t('settings.options.domain') }}</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  :value="'url'"
                  v-model="excludedInputType"
                  class="w-4 h-4 text-blue-500 border-slate-300 dark:border-slate-600 focus:ring-2 focus:ring-blue-500"
                />
                <span class="text-slate-700 dark:text-slate-300">{{ t('settings.options.Url') }}</span>
              </label>
            </div>
            <div class="flex gap-2">
              <input
                v-model="newExcludedDomain"
                type="text"
                class="flex-1 px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                :placeholder="excludedInputType === 'domain' ? t('settings.placeholders.excludedDomains') : t('settings.placeholders.excludedUrl')"
                @keydown.enter.prevent="addExcludedDomain"
                :disabled="isUpdatingDomains"
              />
              <button
                type="button"
                class="px-3 py-2 text-sm rounded-lg bg-blue-500 hover:bg-blue-600 text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                @click="addExcludedDomain"
                :disabled="isUpdatingDomains"
              >
                {{ t('common.add') }}
              </button>
            </div>
            <p v-if="excludedDomainError" class="text-xs text-red-500 dark:text-red-400">
              {{ excludedDomainError }}
            </p>
            <p v-else class="text-xs text-slate-500 dark:text-slate-400">
              {{ t('settings.hints.excludedDomains') }}
            </p>
            <ul v-if="urlBlacklist.length" class="space-y-2 max-h-40 overflow-y-auto custom-scrollbar-thin pr-1">
              <li
                v-for="entry in urlBlacklist"
                :key="entry.id ?? entry.url"
                class="flex items-center justify-between px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/40"
              >
                <span class="text-sm text-slate-700 dark:text-slate-200 break-all">{{ entry.url }}</span>
                <button
                  type="button"
                  class="text-xs text-red-500 hover:text-red-600 dark:text-red-400 dark:hover:text-red-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  @click="removeExcludedDomain(entry)"
                  :disabled="isUpdatingDomains"
                >
                  {{ t('common.delete') }}
                </button>
              </li>
            </ul>
            <p v-else class="text-xs text-slate-400 dark:text-slate-500">
              {{ t('settings.hints.noExcludedDomains') }}
            </p>
          </div>

          <!-- Language Setting -->
          <div class="space-y-1">
            <div class="flex items-center justify-between gap-6">
              <label class="text-sm font-medium text-slate-700 dark:text-slate-300 flex-1">
                {{ t('settings.fields.language') }}
              </label>
              <select
                :value="selectedLanguage"
                @change="handleLanguageChange"
                :disabled="isUpdatingLanguage"
                class="w-32 px-2.5 py-1 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="en">{{ t('languageSwitcher.english') }}</option>
                <option value="zh-CN">{{ t('languageSwitcher.chineseSimplified') }}</option>
              </select>
            </div>
            <p v-if="languageError" class="text-xs text-red-500 text-right">
              {{ languageError }}
            </p>
          </div>
        </div>
      </main>

      <!-- Footer -->
      <footer class="flex items-center justify-end gap-2 p-4 border-t border-slate-200 dark:border-slate-700">
        <button
          @click="onClose"
          class="px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
        >
          {{ t('settings.buttons.cancel') }}
        </button>
        <button
          @click="saveSettings"
          :disabled="isSaving || !isValid"
          class="px-3 py-1.5 text-sm rounded-lg bg-blue-500 hover:bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <span v-if="isSaving">{{ t('settings.buttons.saving') }}</span>
          <span v-else>{{ t('settings.buttons.save') }}</span>
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import Icon from './Icon.vue';
import { settingsService, type Settings } from '../api/settingsService';
import { updateLanguagePreference } from '../api/preferencesService';
import { useI18n } from '../i18n';

interface Props {
  onClose: () => void;
}

const props = defineProps<Props>();

const isLoading = ref(true);
const isSaving = ref(false);
const isUpdatingLanguage = ref(false);
const error = ref<string | null>(null);
const localSettings = ref<Settings>({
  tips_interval_minutes: 60,
  todo_interval_minutes: 30,
  daily_report_hour: 8,
  daily_report_minute: 0,
  excluded_domains: []
});

const languageError = ref<string | null>(null);
const { t, locale, setLocale } = useI18n();
const selectedLanguage = ref<'en' | 'zh-CN'>(locale.value);

watch(locale, (newLocale) => {
  selectedLanguage.value = newLocale;
});

const isValid = computed(() => {
  return (
    localSettings.value.tips_interval_minutes >= 1 &&
    localSettings.value.todo_interval_minutes >= 1 &&
    localSettings.value.daily_report_hour >= 0 &&
    localSettings.value.daily_report_hour <= 23 &&
    localSettings.value.daily_report_minute >= 0 &&
    localSettings.value.daily_report_minute <= 59
  );
});

interface UrlBlacklistEntry {
  id: number | null;
  url: string;
}

const urlBlacklist = ref<UrlBlacklistEntry[]>([]);
const newExcludedDomain = ref('');
const excludedDomainError = ref<string | null>(null);
const isUpdatingDomains = ref(false);
const excludedInputType = ref<'domain' | 'url'>('domain');

const normalizeDomain = (input: string): string => {
  const trimmed = input.trim();
  if (!trimmed) {
    return '';
  }
  
  if (excludedInputType.value === 'domain') {
    const withoutProtocol = trimmed.replace(/^\w+:\/\//, '');
    const withoutPath = withoutProtocol.replace(/\/.*$/, '');
    const domain = withoutPath.toLowerCase();
    return `https://${domain}`;
  } else {
    let url = trimmed;
    if (!/^https?:\/\//i.test(url)) {
      url = 'https://' + url;
    }
    url = url.replace(/\/+$/, '');
    return url;
  }
};

const validateInput = (input: string): boolean => {
  const trimmed = input.trim();
  if (!trimmed) {
    return false;
  }
  
  if (excludedInputType.value === 'domain') {
    const domainPattern = /^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$/i;
    const withoutProtocol = trimmed.replace(/^\w+:\/\//, '').replace(/\/.*$/, '');
    return domainPattern.test(withoutProtocol);
  } else {
    try {
      const url = /^https?:\/\//i.test(trimmed) ? trimmed : 'https://' + trimmed;
      new URL(url);
      return true;
    } catch {
      return false;
    }
  }
};

const syncExcludedDomains = () => {
  localSettings.value.excluded_domains = urlBlacklist.value.map((entry) => entry.url);
};

const addExcludedDomain = async () => {
  if (!validateInput(newExcludedDomain.value)) {
    excludedDomainError.value = excludedInputType.value === 'domain' 
      ? t('settings.errors.invalidDomain')
      : t('settings.errors.invalidUrl');
    return;
  }
  
  const normalized = normalizeDomain(newExcludedDomain.value);
  if (!normalized) {
    excludedDomainError.value = excludedInputType.value === 'domain'
      ? t('settings.errors.invalidDomain')
      : t('settings.errors.invalidUrl');
    return;
  }
  
  if (urlBlacklist.value.some((entry) => entry.url === normalized)) {
    excludedDomainError.value = t('settings.errors.duplicateDomain');
    return;
  }
  if (isUpdatingDomains.value) {
    return;
  }
  isUpdatingDomains.value = true;
  excludedDomainError.value = null;

  try {
    const created = await settingsService.createExcludedDomain(normalized);
    const createdUrl = created.url || normalized;
    const entry: UrlBlacklistEntry = {
      id: typeof created.id === 'number' ? created.id : Date.now(),
      url: createdUrl
    };
    urlBlacklist.value = [...urlBlacklist.value, entry];
    syncExcludedDomains();
    newExcludedDomain.value = '';
  } catch (err) {
    excludedDomainError.value = err instanceof Error ? err.message : t('settings.errors.save');
  } finally {
    isUpdatingDomains.value = false;
  }
};

const removeExcludedDomain = async (entry: UrlBlacklistEntry) => {
  if (isUpdatingDomains.value) {
    return;
  }

  if (entry.id === null || entry.id === undefined) {
    console.error('Invalid domain ID:', entry);
    excludedDomainError.value = t('settings.errors.invalidDomainId');
    return;
  }

  isUpdatingDomains.value = true;
  excludedDomainError.value = null;

  try {
    await settingsService.deleteExcludedDomain(entry.id);
    // 只有后端删除成功后才更新前端列表
    urlBlacklist.value = urlBlacklist.value.filter((item) => item.id !== entry.id);
    syncExcludedDomains();
  } catch (err) {
    excludedDomainError.value = err instanceof Error ? err.message : t('settings.errors.save');
    // 删除失败时不更新前端列表
  } finally {
    isUpdatingDomains.value = false;
  }
};

const loadSettings = async () => {
  isLoading.value = true;
  error.value = null;
  
  try {
    const [settings, domains] = await Promise.all([
      settingsService.getSettings(),
      settingsService.getExcludedDomains().catch((err) => {
        console.error('Failed to fetch excluded domains:', err);
        return null;
      })
    ]);
    const blacklistEntries: UrlBlacklistEntry[] = Array.isArray(domains)
      ? domains
          .map((domain, index) => {
            if (typeof domain === 'string') {
              const normalized = normalizeDomain(domain);
              return normalized ? { id: null, url: normalized } : null;
            }
            if (domain && typeof domain === 'object') {
              const item = domain as { id?: number; url?: string };
              const normalized = typeof item.url === 'string' ? normalizeDomain(item.url) : '';
              if (!normalized) return null;
              return {
                id: typeof item.id === 'number' ? item.id : null,
                url: normalized
              };
            }
            return null;
          })
          .filter((entry): entry is UrlBlacklistEntry => entry !== null)
      : Array.isArray(settings.excluded_domains)
        ? settings.excluded_domains
            .map((domain) => {
              const normalized = normalizeDomain(domain);
              return normalized ? { id: null, url: normalized } : null;
            })
            .filter((entry): entry is UrlBlacklistEntry => entry !== null)
        : [];
    console.log('blacklistEntries', blacklistEntries);

    localSettings.value = {
      tips_interval_minutes: settings.tips_interval_minutes ?? 60,
      todo_interval_minutes: settings.todo_interval_minutes ?? 30,
      daily_report_hour: settings.daily_report_hour ?? 8,
      daily_report_minute: settings.daily_report_minute ?? 0,
      excluded_domains: blacklistEntries.map((entry) => entry.url)
    };
    urlBlacklist.value = blacklistEntries;
    syncExcludedDomains();
  } catch (err) {
    error.value = err instanceof Error ? err.message : t('settings.errors.load');
    console.error('Failed to load settings:', err);
  } finally {
    isLoading.value = false;
  }
};

const saveSettings = async () => {
  if (!isValid.value || isSaving.value) {
    return;
  }

  syncExcludedDomains();

  isSaving.value = true;
  error.value = null;

  try {
    await settingsService.updateSettings(localSettings.value);
    props.onClose();
  } catch (err) {
    error.value = err instanceof Error ? err.message : t('settings.errors.save');
    console.error('Failed to save settings:', err);
  } finally {
    isSaving.value = false;
  }
};

const handleLanguageChange = async (event: Event) => {
  const target = event.target as HTMLSelectElement | null;
  if (!target) {
    return;
  }

  const nextLanguage = target.value as 'en' | 'zh-CN';
  const previousLanguage = locale.value;

  if (nextLanguage === previousLanguage || isUpdatingLanguage.value) {
    selectedLanguage.value = previousLanguage;
    return;
  }

  languageError.value = null;
  selectedLanguage.value = nextLanguage;
  setLocale(nextLanguage);
  isUpdatingLanguage.value = true;

  try {
    await updateLanguagePreference(nextLanguage);
  } catch (err) {
    console.error('Failed to update language preference:', err);
    languageError.value = t('settings.errors.languageUpdate');
    setLocale(previousLanguage);
    selectedLanguage.value = previousLanguage;
  } finally {
    isUpdatingLanguage.value = false;
  }
};

onMounted(() => {
  loadSettings();
});
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 4px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgb(203 213 225);
  border-radius: 4px;
  transition: background 0.2s;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgb(148 163 184);
}

/* 暗色模式 */
.dark .custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgb(51 65 85);
}

.dark .custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgb(71 85 105);
}

/* Firefox 滚动条样式 */
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: rgb(203 213 225) transparent;
}

.dark .custom-scrollbar {
  scrollbar-color: rgb(51 65 85) transparent;
}

.custom-scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 3px;
}

.custom-scrollbar-thin::-webkit-scrollbar-thumb {
  background: rgb(203 213 225);
  border-radius: 3px;
  transition: background 0.2s;
}

.custom-scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background: rgb(148 163 184);
}

/* 暗色模式 */
.dark .custom-scrollbar-thin::-webkit-scrollbar-thumb {
  background: rgb(51 65 85);
}

.dark .custom-scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background: rgb(71 85 105);
}

/* Firefox 滚动条样式 */
.custom-scrollbar-thin {
  scrollbar-width: thin;
  scrollbar-color: rgb(203 213 225) transparent;
}

.dark .custom-scrollbar-thin {
  scrollbar-color: rgb(51 65 85) transparent;
}
</style>
