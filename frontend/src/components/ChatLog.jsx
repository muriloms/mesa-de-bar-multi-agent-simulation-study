// src/components/ChatLog.jsx
import './ChatLog.css';

const ChatLog = ({ conversation = [] }) => {
  return (
    <div className="chat-log-container">
      {conversation.map((msg, index) => (
        <div key={index} className="chat-message">
          <strong>{msg.player_name}:</strong> {msg.message}
        </div>
      ))}
    </div>
  );
};

export default ChatLog;