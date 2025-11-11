const mapToPromptLanguage = (language: 'en' | 'zh-CN'): 'zh' | 'en' => (language === 'zh-CN' ? 'zh' : 'en');
const mapFromPromptLanguage = (language: unknown): 'en' | 'zh-CN' | null => {
  if (language === 'zh') return 'zh-CN';
  if (language === 'en') return 'en';
  return null;
};

export const updateLanguagePreference = async (language: 'en' | 'zh-CN'): Promise<void> => {
  try {
    await fetch('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt_language: mapToPromptLanguage(language) }),
    });
  } catch (error) {
    console.error('Failed to persist language preference:', error);
  }
};

export const fetchLanguagePreference = async (): Promise<'en' | 'zh-CN' | null> => {
  try {
    const response = await fetch('/api/settings', { method: 'GET', headers: { 'Content-Type': 'application/json' } });
    if (!response.ok) return null;
    const data = await response.json();
    return mapFromPromptLanguage(data.prompt_language);
  } catch (error) {
    console.error('Failed to fetch language preference:', error);
    return null;
  }
};
