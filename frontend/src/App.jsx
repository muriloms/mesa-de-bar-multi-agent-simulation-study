import { useState, useEffect } from 'react';
import {
  setupGame, sendIdea, passTurn, sendPick, advanceRound,
  endConversation,
  postTelemetry, downloadSessionZip,
  getInstrument, submitInstrumentResponse,
  startStudy,
  getPlatformConfig,
} from './services/api';
import SetupScreen from './pages/SetupScreen';
import LoginScreen from './pages/LoginScreen';
import TableScreen from './pages/TableScreen';
import CatPanel from './pages/CatPanel';
import AdminScreen from './pages/AdminScreen';
import SimulationScreen from './pages/SimulationScreen';
import EndGameSummary from './pages/EndGameSummary';
import SessionResults from './pages/SessionResults';
import InstrumentForm from './components/InstrumentForm/InstrumentForm';
import LoadingOverlay from './components/LoadingOverlay';
import { useT } from './i18n/i18n';
import './App.css';

const App = () => {
  const t = useT();
  // Views: 'login' | 'setup' | 'instrument' | 'table' | 'summary' | 'results'
  const [view, setView] = useState('login');
  const [participantName, setParticipantName] = useState('');
  const [platformConfig, setPlatformConfig] = useState(null);
  const [gameState, setGameState] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [userAvatar, setUserAvatar] = useState(null);
  const [activeInstrument, setActiveInstrument] = useState(null);

  const [llmConfig, setLlmConfig] = useState(() => {
    try {
      const cachedConfig = localStorage.getItem('llmConfig');
      if (cachedConfig) return JSON.parse(cachedConfig);
    } catch (error) {
      console.error("Erro ao ler configuração do cache:", error);
    }
    return { provider: 'google', model: 'gemini-1.5-flash', apiKey: '' };
  });

  useEffect(() => {
    try {
      localStorage.setItem('llmConfig', JSON.stringify(llmConfig));
    } catch (error) {
      console.error("Erro ao salvar configuração no cache:", error);
    }
  }, [llmConfig]);

  // Carrega a configuração da plataforma (o que está aberto/ativo).
  useEffect(() => {
    getPlatformConfig()
      .then((res) => setPlatformConfig(res.data))
      .catch(() => setPlatformConfig(null));
  }, []);

  // Acesso inicial: fixa OpenAI (ChatGPT) + gpt-4o-mini com a chave digitada.
  // Credenciais já foram validadas na tela de login.
  const handleLogin = ({ apiKey }) => {    setLlmConfig({ provider: 'openai', model: 'gpt-4o-mini', apiKey });
    setError(null);
    setView('setup');
  };

  const loadInstrumentDefinition = async (instrumentId) => {
    try {
      const res = await getInstrument(instrumentId);
      return res.data;
    } catch (err) {
      console.error(`Falha ao carregar instrumento ${instrumentId}:`, err);
      return null;
    }
  };

  const handleGameSetup = async (setupData, imageBase64) => {
    setIsLoading(true);
    setError(null);
    try {
      const fullSetupData = { ...setupData, global_llm_config: llmConfig };
      const response = await setupGame(fullSetupData);
      setGameState(response.data);
      setUserAvatar(imageBase64);

      const preId = response.data.pre_session_instrument;
      if (preId) {
        const def = await loadInstrumentDefinition(preId);
        if (def) {
          setActiveInstrument({ definition: def, moment: 'pre_session' });
          setView('instrument');
          return;
        }
      }
      setView('table');
    } catch (err) {
      console.error("Erro ao configurar o jogo:", err);
      setError("Ocorreu um erro ao arrumar a mesa. Tente novamente.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartStudy = async (studyId, userName, choices = {}) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await startStudy(studyId, userName, llmConfig, choices);
      setGameState(response.data);
      setUserAvatar(null);
      const preId = response.data.pre_session_instrument;
      if (preId) {
        const def = await loadInstrumentDefinition(preId);
        if (def) {
          setActiveInstrument({ definition: def, moment: 'pre_session' });
          setView('instrument');
          return;
        }
      }
      setView('table');
    } catch (err) {
      console.error("Erro ao iniciar estudo:", err);
      setError("Não foi possível iniciar o estudo. Verifique a configuração e tente novamente.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleApiCall = async (apiFunc) => {
    if (!gameState) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiFunc();
      setGameState(response.data);
      if (response.data.game_phase === 'finished') {
        setView('summary');
      }
    } catch (err) {
      console.error("Erro de API:", err);
      setError(t('common.error_generic'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleContinueFromSummary = async () => {
    if (!gameState) return;
    const postId = gameState.post_session_instrument;
    if (postId) {
      setIsLoading(true);
      const def = await loadInstrumentDefinition(postId);
      setIsLoading(false);
      if (def) {
        setActiveInstrument({ definition: def, moment: 'post_session' });
        setView('instrument');
        return;
      }
    }
    setView('results');
  };

  const handleInstrumentSubmit = async (responsePayload) => {
    if (!activeInstrument || !gameState) return;
    setIsLoading(true);
    try {
      await submitInstrumentResponse(
        gameState.session_id,
        activeInstrument.definition.id,
        responsePayload,
      );
    } catch (err) {
      console.warn("Falha ao gravar respostas; seguindo mesmo assim:", err);
    } finally {
      setIsLoading(false);
    }

    const moment = activeInstrument.moment;
    setActiveInstrument(null);
    if (moment === 'pre_session') setView('table');
    else if (moment === 'post_session') setView('results');
  };

  const handleInstrumentSkip = () => {
    if (!activeInstrument) return;
    const moment = activeInstrument.moment;
    setActiveInstrument(null);
    if (moment === 'pre_session') setView('table');
    else if (moment === 'post_session') setView('results');
  };

  // --- Loop de rodada (v2) ---
  const handleSendIdea = (ideaText) => handleApiCall(() => sendIdea(gameState.session_id, ideaText));
  const handlePass = (justification) => handleApiCall(() => passTurn(gameState.session_id, justification));
  const handlePick = (pickRef) => handleApiCall(() => sendPick(gameState.session_id, pickRef));
  const handleAdvance = async (agreeJudge) => {
    if (!gameState) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await advanceRound(gameState.session_id, agreeJudge);
      // Última rodada concluída → encerra automaticamente (síntese do Dono).
      if (res.data?.phase_name === 'closing') {
        const endRes = await endConversation(gameState.session_id);
        setGameState(endRes.data);
        setView('summary');
      } else {
        setGameState(res.data);
      }
    } catch (err) {
      console.error("Erro ao avançar rodada:", err);
      setError(t('common.error_generic'));
    } finally {
      setIsLoading(false);
    }
  };
  const handleEndConversation = () => handleApiCall(() => endConversation(gameState.session_id));

  const handleTelemetry = (kind, { events, metrics }) => {
    if (!gameState) return;
    postTelemetry(gameState.session_id, kind, events, metrics).catch((err) => {
      console.warn("Telemetria falhou:", err);
    });
  };

  const handleDownloadZip = () => {
    if (!gameState) return;
    downloadSessionZip(gameState.session_id);
  };

  const handleReset = () => {
    setView('login');
    setGameState(null);
    setUserAvatar(null);
    setActiveInstrument(null);
    setError(null);
    setIsLoading(false);
  };

  return (
    <div className="App">
      {(() => {
        const params = new URLSearchParams(window.location.search);
        if (params.get('admin') === '1') return <AdminScreen />;
        const catStudy = params.get('cat');
        if (catStudy) return <CatPanel studyId={catStudy} />;
        if (platformConfig?.mode === 'simulation') return <SimulationScreen />;
        return null;
      })()}
      {(() => {
        const params = new URLSearchParams(window.location.search);
        return params.get('admin') === '1' || params.get('cat') ||
          platformConfig?.mode === 'simulation';
      })() ? null : (
      <>
      {error && <p className="error-banner">{error}</p>}
      {isLoading && <LoadingOverlay />}

      {view === 'login' &&
        <LoginScreen
          onLogin={handleLogin}
          isLoading={isLoading}
          platformConfig={platformConfig}
        />}

      {view === 'setup' &&
        <SetupScreen
          onGameSetup={handleGameSetup}
          onStartStudy={handleStartStudy}
          isLoading={isLoading}
          defaultName={participantName}
          platformConfig={platformConfig}
        />}

      {view === 'instrument' && activeInstrument && (
        <InstrumentForm
          instrument={activeInstrument.definition}
          onSubmit={handleInstrumentSubmit}
          allowSkip={false}
        />
      )}

      {view === 'table' && (
        <TableScreen
          gameState={gameState}
          userAvatar={userAvatar}
          onSendIdea={handleSendIdea}
          onPass={handlePass}
          onPick={handlePick}
          onAdvance={handleAdvance}
          onTelemetry={handleTelemetry}
          onEndConversation={handleEndConversation}
          onDownloadZip={handleDownloadZip}
          onReset={handleReset}
          isLoading={isLoading}
        />
      )}

      {view === 'summary' && gameState && (
        <EndGameSummary
          summary={gameState.final_summary}
          onContinue={handleContinueFromSummary}
        />
      )}

      {view === 'results' && gameState && (
        <SessionResults
          sessionId={gameState.session_id}
          gameState={gameState}
          onReset={handleReset}
        />
      )}
      </>
      )}
    </div>
  );
}

export default App;
