import { useState, useEffect } from 'react';
import './PersonaEditorModal.css';

const AVAILABLE_MODELS = {
  google: ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro'],
  openai: ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'],
};

const PersonaEditorModal = ({ isOpen, onClose, personaData, onSave, templates, globalLlmConfig }) => {
  const [formData, setFormData] = useState(personaData);
  const [selectedTeam, setSelectedTeam] = useState('');
  const [isOverrideVisible, setIsOverrideVisible] = useState(false);

  useEffect(() => {
    if (personaData) {
      setFormData({
        ...personaData,
        llmOverride: personaData.llmOverride || { provider: '', model: '', apiKey: '' }
      });
    }
    setSelectedTeam('');
  }, [personaData, isOpen]);

  if (!isOpen || !formData) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleLlmChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      llmOverride: { ...prev.llmOverride, [name]: value }
    }));
  };

  const handleLlmProviderChange = (e) => {
    const newProvider = e.target.value;
    const newModel = newProvider ? AVAILABLE_MODELS[newProvider][0] : '';
    setFormData(prev => ({
      ...prev,
      llmOverride: { ...prev.llmOverride, provider: newProvider, model: newModel }
    }));
  };

  const handleClearOverride = () => {
    setFormData(prev => ({
      ...prev,
      llmOverride: { provider: '', model: '', apiKey: '' }
    }));
  };
  
  const handleTeamSelect = (e) => {
    setSelectedTeam(e.target.value);
  };

  const handlePersonaSelect = (e) => {
    const personaName = e.target.value;
    if (!personaName || !selectedTeam) return;
    
    const team = templates.personaTemplates[selectedTeam];
    const selectedPersona = team.find(p => p.name === personaName);

    if (selectedPersona) {
      setFormData(prev => ({ ...prev, ...selectedPersona }));
    }
  };

  const handleSave = () => {
    onSave(formData);
    onClose();
  };

  const llmOverride = formData.llmOverride || {};

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2>Editar Participante</h2>

        <div className="template-loader">
        </div>

        <div className="modal-form">
          <label>Nome</label>
          <input name="name" value={formData.name} onChange={handleChange} />
          <label>Descrição</label>
          <textarea name="description" value={formData.description} onChange={handleChange} rows="3" />
          <label>Papel na Discussão</label>
          <input name="role" value={formData.role} onChange={handleChange} />
          <label>Objetivo Principal</label>
          <input name="goal" value={formData.goal} onChange={handleChange} />
          <label>Instruções de Comportamento</label>
          <textarea name="instructions" value={formData.instructions} onChange={handleChange} rows="4" />
        </div>

        <div className="collapsible-section">
          <button type="button" className="collapse-toggle" onClick={() => setIsOverrideVisible(!isOverrideVisible)}>
            Sobrescrever Configuração de LLM (Opcional) {isOverrideVisible ? '▲' : '▼'}
          </button>
          {isOverrideVisible && (
            <div className="llm-override-form">
              <label>Provedor (Padrão Global: {globalLlmConfig.provider})</label>
              <select name="provider" value={llmOverride.provider} onChange={handleLlmProviderChange}>
                <option value="">Usar Global</option>
                <option value="google">Google</option>
                <option value="openai">OpenAI</option>
              </select>

              <label>Modelo (Padrão Global: {globalLlmConfig.model})</label>
              <select name="model" value={llmOverride.model} onChange={handleLlmChange} disabled={!llmOverride.provider}>
                {llmOverride.provider && AVAILABLE_MODELS[llmOverride.provider].map(modelName => (
                  <option key={modelName} value={modelName}>{modelName}</option>
                ))}
              </select>

              <label>Chave de API (Opcional, sobrescreve a global)</label>
              <input type="password" name="apiKey" value={llmOverride.apiKey} onChange={handleLlmChange} placeholder="Deixe em branco para usar a chave global" />
              <button type="button" className="clear-override-btn" onClick={handleClearOverride}>Limpar Sobrescrita</button>
            </div>
          )}
        </div>

        <div className="modal-actions">
          <button onClick={onClose}>Cancelar</button>
          <button onClick={handleSave} className="save-btn">Salvar Alterações</button>
        </div>
      </div>
    </div>
  );
};

export default PersonaEditorModal;