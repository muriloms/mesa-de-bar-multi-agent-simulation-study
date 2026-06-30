import { useState, useEffect } from 'react';
import './LabScreen.css';

const LabScreen = ({ labData, onReset }) => {
  const [formData, setFormData] = useState(labData);
  
  useEffect(() => {
    setFormData({
      ...labData,
      key_features: labData.key_features.join('\n'),
    });
  }, [labData]);

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFinalSubmit = (e) => {
    e.preventDefault();
    // TODO Fase 4 (Exportação): substituir este alert por download do ZIP da sessão.
    // Hoje a LabIdea editada não é persistida em lugar nenhum — é o gap mais
    // crítico do fluxo atual e a Fase 4 vai resolver com export.zip.
    alert("Proposta enviada ao Laboratório com sucesso!");
  };

  const handleReturnHome = () => {
    if (onReset) onReset();
  };

  return (
    <div className="lab-page-container">
      <div className="lab-content-wrapper">
        <div className="lab-header">
          <h1>Laboratório da Ideia</h1>
          <p>A discussão foi consolidada em uma proposta de projeto. Revise e edite os campos gerados pela IA, preencha seus dados e submeta para análise.</p>
        </div>

        <form className="lab-form" onSubmit={handleFinalSubmit}>
          <div className="lab-form-grid">
            
            <div className="form-group-lab">
              <label>Seu Nome</label>
              <input name="userName" type="text" placeholder="Digite seu nome completo" onChange={handleFormChange} required />
            </div>

            <div className="form-group-lab">
              <label>Seu Email</label>
              <input name="userEmail" type="email" placeholder="seu.email@empresa.com" onChange={handleFormChange} required />
            </div>

            <div className="form-group-lab full-width">
              <label>Título do Projeto</label>
              <input name="title" type="text" value={formData.title} onChange={handleFormChange} required />
            </div>

            <div className="form-group-lab full-width">
              <label>Problema a ser Resolvido</label>
              <textarea name="problem_statement" value={formData.problem_statement} onChange={handleFormChange} rows="3" required />
            </div>

            <div className="form-group-lab full-width">
              <label>Solução Proposta</label>
              <textarea name="core_solution" value={formData.core_solution} onChange={handleFormChange} rows="5" required />
            </div>

            <div className="form-group-lab">
              <label>Funcionalidades Chave (uma por linha)</label>
              <textarea name="key_features" value={formData.key_features} onChange={handleFormChange} rows="6" required />
            </div>

            <div className="form-group-lab">
              <label>Público-Alvo</label>
              <textarea name="target_audience" value={formData.target_audience} onChange={handleFormChange} rows="6" required />
            </div>

            <div className="form-group-lab">
              <label>Impacto Potencial</label>
              <textarea name="potential_impact" value={formData.potential_impact} onChange={handleFormChange} rows="6" required />
            </div>

            <div className="form-group-lab">
              <label>Próximos Passos</label>
              <textarea name="next_steps" value={formData.next_steps} onChange={handleFormChange} rows="6" required />
            </div>
          </div>
          
          <div className="lab-actions">
            <button type="button" className="secondary-button" onClick={handleReturnHome}>
              Criar Nova Ideia
            </button>
            <button type="submit" className="primary-button">
              Enviar ao Lab
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LabScreen;