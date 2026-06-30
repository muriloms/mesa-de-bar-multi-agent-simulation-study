import { useT } from '../i18n/i18n';
import './LoadTeamModal.css';

/**
 * Modal de seleção de composição (time pré-pronto).
 *
 * Aceita duas formas:
 *  - `compositions` (Fase 6): array de {id, title, description, tags, personas}
 *  - `teamsData` (legado): objeto {nome: [...personas]}
 */
const LoadTeamModal = ({ isOpen, onClose, compositions, teamsData, onSelectTeam }) => {
  const t = useT();
  if (!isOpen) return null;

  // Se vier de uma composição YAML, repassa o id; se vier de teamsData legado, passa null.
  const handleSelect = (team, compositionId) => {
    onSelectTeam(team, compositionId);
    onClose();
  };

  // Constrói lista unificada {key, title, description, tags, personas, isComposition}
  let items = [];
  if (Array.isArray(compositions) && compositions.length > 0) {
    items = compositions.map(c => ({
      key: c.id,
      title: c.title,
      description: c.description,
      tags: c.tags || [],
      personas: c.personas || [],
      isComposition: true,  // tem id rastreável
    }));
  } else if (teamsData) {
    items = Object.entries(teamsData).map(([name, personas]) => ({
      key: name,
      title: name,
      description: '',
      tags: [],
      personas,
      isComposition: false,  // legado, sem id
    }));
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content team-modal" onClick={(e) => e.stopPropagation()}>
        <div className="team-modal-header">
          <h2>{t('setup.load_team')}</h2>
          <button type="button" className="team-modal-close" onClick={onClose} aria-label="Fechar">×</button>
        </div>
        <div className="team-grid">
          {items.length === 0 && (
            <p className="team-empty">{t('common.loading')}</p>
          )}
          {items.map(item => (
            <div key={item.key} className="team-card" onClick={() => handleSelect(item.personas, item.isComposition ? item.key : null)}>
              <h3>{item.title}</h3>
              {item.description && <p className="team-desc">{item.description}</p>}
              {item.tags.length > 0 && (
                <div className="team-tags">
                  {item.tags.map(t => <span key={t} className="team-tag">{t}</span>)}
                </div>
              )}
              <ul className="team-personas">
                {item.personas.map(p => (
                  <li key={p.name}>
                    <strong>{p.name}</strong>
                    {p.role && <span className="team-persona-role"> — {p.role}</span>}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LoadTeamModal;
