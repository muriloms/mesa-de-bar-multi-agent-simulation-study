// src/services/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
});

// ---------------------------------------------------------------------------
// Setup / personas
// ---------------------------------------------------------------------------
export const setupGame = (setupData) => api.post('/setup', setupData);
export const generatePersonas = (payload) => api.post('/generate-personas', payload);

// Estudos (runner experimental)
export const listStudies = () => api.get('/studies');
export const getCatalog = () => api.get('/catalog');
export const getPlatformConfig = () => api.get('/platform-config');
export const getSimulationConfig = () => api.get('/simulation/config');
export const startSimulation = (overrides = {}) => api.post('/simulation/start', overrides);
export const getSimulationStatus = (runId) => api.get(`/simulation/status/${runId}`);
export const startStudy = (studyId, userName, globalLlmConfig, extra = {}) =>
  api.post('/study/start', {
    study_id: studyId, user_name: userName, global_llm_config: globalLlmConfig,
    chosen_topic: extra.chosenTopic ?? null,
    chosen_composition: extra.chosenComposition ?? null,
  });
export const getStudyBalance = (studyId) => api.get(`/studies/${studyId}/balance`);

// Painel CAT (avaliação cega)
export const getCatItems = (studyId) => api.get(`/cat/${studyId}/items`);
export const submitCatRatings = (studyId, judgeId, ratings) =>
  api.post(`/cat/${studyId}/ratings`, { judge_id: judgeId, ratings });

// ---------------------------------------------------------------------------
// Loop de rodada (v2)
// ---------------------------------------------------------------------------
// 1) Humano submete a ideia da rodada (sem aposta)
export const sendIdea = (sessionId, ideaText) =>
  api.post('/idea', { session_id: sessionId, idea_text: ideaText });

// 1b) Humano passa a vez
export const passTurn = (sessionId, justification = "") =>
  api.post('/pass', { session_id: sessionId, justification });

// 2) Humano escolhe a melhor ideia (referência anônima)
export const sendPick = (sessionId, pickRef) =>
  api.post('/pick', { session_id: sessionId, pick_ref: pickRef });

// 3) Avança a rodada após revelação (agree_judge só no mismatch)
export const advanceRound = (sessionId, agreeJudge = null) =>
  api.post('/advance', { session_id: sessionId, agree_judge: agreeJudge });

// Encerramento (síntese do Dono)
export const endConversation = (sessionId) =>
  api.post('/end', { session_id: sessionId });

// Telemetria comportamental
export const postTelemetry = (sessionId, kind, events, metrics) =>
  api.post('/telemetry', { session_id: sessionId, kind, events, metrics });

// ---------------------------------------------------------------------------
// Dados da sessão
// ---------------------------------------------------------------------------
export const getSessionCosts = (sessionId) =>
  api.get(`/sessions/${sessionId}/costs`);

export const getSessionStats = (sessionId) =>
  api.get(`/sessions/${sessionId}/stats`);

export const getSessionIdea = (sessionId) =>
  api.get(`/sessions/${sessionId}/idea`);

export const downloadSessionIdeaJson = async (sessionId) => {
  const res = await api.get(`/sessions/${sessionId}/idea`);
  const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `mesa-de-bar-${sessionId}-ideia.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

export const downloadSessionIdeaMarkdown = (sessionId) => {
  const url = `${api.defaults.baseURL}/sessions/${sessionId}/idea/markdown`;
  const a = document.createElement('a');
  a.href = url;
  a.download = `mesa-de-bar-${sessionId}-ideia.md`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
};

export const downloadSessionZip = (sessionId) => {
  const url = `${api.defaults.baseURL}/sessions/${sessionId}/export`;
  const a = document.createElement('a');
  a.href = url;
  a.download = `mesa-de-bar-${sessionId}.zip`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
};

export const listSessions = () => api.get('/sessions');
export const listProtocols = () => api.get('/protocols');
export const listCompositions = () => api.get('/compositions');

// ---------------------------------------------------------------------------
// Instrumentos de pesquisa
// ---------------------------------------------------------------------------
export const getInstrument = (instrumentId) => api.get(`/instruments/${instrumentId}`);
export const submitInstrumentResponse = (sessionId, instrumentId, payload) =>
  api.post(`/sessions/${sessionId}/instruments/${instrumentId}/responses`, payload);

export default api;
