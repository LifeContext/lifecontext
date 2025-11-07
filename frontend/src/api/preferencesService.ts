const mapToPromptLanguage = (language: 'en' | 'zh-CN'): 'zh' | 'en' => {
  return language === 'zh-CN' ? 'zh' : 'en';
};

export const updateLanguagePreference = async (language: 'en' | 'zh-CN'): Promise<void> => {
  try {
    await fetch('/api/settings', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt_language: mapToPromptLanguage(language) }),
    });
  } catch (error) {
    console.error('Failed to persist language preference:', error);
  }
};
