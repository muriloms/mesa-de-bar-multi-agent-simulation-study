import { useState, useEffect } from 'react';
import './LlmConfigModal.css';

const AVAILABLE_MODELS = {
  google: ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro'],
  openai: ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'],
};

const LlmConfigModal = ({ isOpen, onClose, config, onSave }) => {
  const [localConfig, setLocalConfig] = useState(config);

  useEffect(() => {
    setLocalConfig(config);
  }, [config, isOpen]);

  if (!isOpen) return null;

  const handleProviderChange = (e) => {
    const newProvider = e.target.value;
    setLocalConfig({
      ...localConfig,
      provider: newProvider,
      model: AVAILABLE_MODELS[newProvider][0],
    });
  };

  const handleChange = (e) => {
    setLocalConfig({ ...localConfig, [e.target.name]: e.target.value });
  };

  const handleSave = () => {
    onSave(localConfig);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2>Configurações de LLM</h2>
        <p>Defina o provedor e modelo padrão para a geração de conteúdo por IA.</p>
        <div className="modal-form">
          <label>Provedor</label>
          <select name="provider" value={localConfig.provider} onChange={handleProviderChange}>
            <option value="google">Google</option>
            <option value="openai">OpenAI</option>
          </select>

          <label>Modelo</label>
          <select name="model" value={localConfig.model} onChange={handleChange}>
            {AVAILABLE_MODELS[localConfig.provider].map(modelName => (
              <option key={modelName} value={modelName}>{modelName}</option>
            ))}
          </select>

          <label>Chave de API (API Key)</label>
          <input type="password" name="apiKey" value={localConfig.apiKey} onChange={handleChange} placeholder="Cole sua chave de API aqui" />
        </div>
        <div className="modal-actions">
          <button onClick={onClose}>Cancelar</button>
          <button onClick={handleSave} className="save-btn">Salvar</button>
        </div>
      </div>
    </div>
  );
};

export default LlmConfigModal;