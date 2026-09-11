import { describe, expect, it } from 'vitest';
import i18n, { localeOptions } from './i18n';

describe('localization', () => {
  it('has a usable translation for every locale', () => {
    for (const locale of localeOptions) {
      expect(i18n.getResource(locale.code, 'translation', 'chat')).toBeTruthy();
      expect(i18n.getResource(locale.code, 'translation', 'switchLanguage')).toBeTruthy();
    }
  });

  it('falls back to English for missing keys', async () => {
    await i18n.changeLanguage('ja');
    expect(i18n.t('missing.key')).toBe('missing.key');
    expect(i18n.t('chat')).toBe('チャット');
    await i18n.changeLanguage('en');
  });
});
