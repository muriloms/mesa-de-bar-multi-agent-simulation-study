/**
 * Sistema mínimo de i18n.
 *
 * Lê as strings de pt.json/en.json e expõe `t(key, vars)` que faz lookup
 * por path (ex: "table.your_proposal") e substitui vars `{x}`.
 *
 * Uso:
 *   import { t, useT, getLanguage, setLanguage } from '../i18n/i18n';
 *
 *   // fora de componentes
 *   t('table.your_proposal')
 *
 *   // dentro de componentes (re-renderiza quando idioma muda)
 *   const t = useT();
 *   return <div>{t('table.your_proposal')}</div>;
 */
import { useEffect, useState } from 'react';
import pt from './pt.json';
import en from './en.json';

const STRINGS = { pt, en };

let currentLanguage = (() => {
  try {
    const stored = localStorage.getItem('mdb_language');
    if (stored === 'pt' || stored === 'en') return stored;
  } catch (e) {}
  return 'pt';
})();

const listeners = new Set();

function lookup(key, lang) {
  const parts = key.split('.');
  let node = STRINGS[lang];
  for (const part of parts) {
    if (node && typeof node === 'object' && part in node) {
      node = node[part];
    } else {
      return null;
    }
  }
  return typeof node === 'string' ? node : null;
}

function interpolate(template, vars) {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (_, name) => {
    return vars[name] !== undefined ? String(vars[name]) : `{${name}}`;
  });
}

export function t(key, vars) {
  const tryLang = lookup(key, currentLanguage);
  if (tryLang !== null) return interpolate(tryLang, vars);
  // Fallback pra PT
  const fallback = lookup(key, 'pt');
  if (fallback !== null) return interpolate(fallback, vars);
  // Sem tradução — devolve a chave (debug)
  return key;
}

export function getLanguage() {
  return currentLanguage;
}

export function setLanguage(lang) {
  if (lang !== 'pt' && lang !== 'en') return;
  currentLanguage = lang;
  try {
    localStorage.setItem('mdb_language', lang);
  } catch (e) {}
  listeners.forEach((cb) => cb(lang));
}

/**
 * Hook que devolve `t()` e força re-render quando o idioma muda.
 */
export function useT() {
  const [, setTick] = useState(0);
  useEffect(() => {
    const cb = () => setTick((n) => n + 1);
    listeners.add(cb);
    return () => listeners.delete(cb);
  }, []);
  return t;
}

/**
 * Hook que dá acesso ao idioma atual com re-render quando muda.
 */
export function useLanguage() {
  const [lang, setLang] = useState(currentLanguage);
  useEffect(() => {
    const cb = (newLang) => setLang(newLang);
    listeners.add(cb);
    return () => listeners.delete(cb);
  }, []);
  return [lang, setLanguage];
}
