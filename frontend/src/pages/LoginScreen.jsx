import { useEffect, useState } from 'react';
import { useT, setLanguage } from '../i18n/i18n';
import './LoginScreen.css';

/**
 * Tela inicial de acesso (com validação real de credenciais).
 *
 * Nesta fase, o acesso é liberado apenas com o e-mail e a senha corretos.
 * A chave da API digitada é usada como a chave do provedor para a sessão.
 *
 * Atenção de segurança: a checagem de credenciais é feita no frontend, então
 * é contornável por quem inspecionar o código. Serve como porta de entrada
 * desta fase; autenticação real exigiria verificação no backend.
 */
const ACCESS_EMAIL = 'pesquisa@mesabar.br';
const ACCESS_PASSWORD = 'mesa62Bar02';

export default function LoginScreen({ onLogin, isLoading, platformConfig }) {
  const t = useT();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');

  // Se a plataforma fornece a chave (plataforma.yaml), o campo some.
  const needKey = platformConfig?.api?.user_provides_key !== false;

  // Esta fase usa pt-br como padrão (sem seletor de idioma).
  useEffect(() => {
    setLanguage('pt');
  }, []);

  const ready = email.trim() && password.trim() && (!needKey || apiKey.trim());

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!ready || isLoading) return;
    const emailOk = email.trim().toLowerCase() === ACCESS_EMAIL;
    const passOk = password === ACCESS_PASSWORD;
    if (!emailOk || !passOk) {
      setError(t('login.invalid'));
      return;
    }
    setError('');
    onLogin({ apiKey: needKey ? apiKey.trim() : '' });
  };

  return (
    <div className="login">
      <form className="login-card" onSubmit={handleSubmit}>
        <p className="login-eyebrow">{t('login.eyebrow')}</p>
        <h1 className="login-title">
          <span>MESA</span>
          <span className="login-title-de">de</span>
          <span className="login-title-neon">BAR</span>
        </h1>
        <p className="login-subtitle">{t('login.subtitle')}</p>

        <label className="login-field">
          <span className="login-label">{t('login.email')}</span>
          <input
            type="email"
            value={email}
            onChange={(e) => { setEmail(e.target.value); if (error) setError(''); }}
            placeholder={t('login.email_ph')}
            autoComplete="username"
          />
        </label>

        <label className="login-field">
          <span className="login-label">{t('login.password')}</span>
          <input
            type="password"
            value={password}
            onChange={(e) => { setPassword(e.target.value); if (error) setError(''); }}
            placeholder={t('login.password_ph')}
            autoComplete="current-password"
          />
        </label>

        {needKey && (
          <label className="login-field">
            <span className="login-label">{t('login.apikey')}</span>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={t('login.apikey_ph')}
              autoComplete="off"
              spellCheck={false}
            />
            <span className="login-hint">{t('login.apikey_hint')}</span>
          </label>
        )}
        {error && <p className="login-error">{error}</p>}

        <button type="submit" className="login-btn" disabled={!ready || isLoading}>
          {isLoading ? t('login.entering') : t('login.enter')}
        </button>

        {!ready && !error && <p className="login-note">{t('login.need_all')}</p>}
      </form>
    </div>
  );
}
