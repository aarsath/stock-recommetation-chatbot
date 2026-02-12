import React, { useState, useRef, useEffect } from 'react';
import { chatWithAI } from '../services/api';
import SendIcon from '@mui/icons-material/Send';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import './ChatBot.css';

const ChatBot = ({ symbol, stockName }) => {
  const [messages, setMessages] = useState([
    {
      type: 'bot',
      text: `Hello! I'm your AI stock analyst. Ask me anything about ${stockName || 'the selected stock'}!`,
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatLanguage, setChatLanguage] = useState('auto');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    if (!symbol) {
      addMessage('bot', 'Please select a stock first to get specific analysis.');
      return;
    }

    const userMessage = input.trim();
    setInput('');

    addMessage('user', userMessage);
    setLoading(true);

    try {
      const selectedLanguage = chatLanguage === 'auto' ? undefined : chatLanguage;
      const response = await chatWithAI(userMessage, symbol, selectedLanguage);
      addMessage('bot', response.response || 'Sorry, I could not generate a response.');
    } catch (error) {
      console.error('Chat error:', error);
      addMessage('bot', 'Sorry, there was an error processing your request. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const addMessage = (type, text) => {
    setMessages((prev) => [
      ...prev,
      {
        type,
        text,
        timestamp: new Date().toISOString(),
      },
    ]);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const quickQuestions = [
    'Should I buy this stock?',
    'What is the current price?',
    'What are the key technical indicators?',
    'What is the risk level?',
    'What is the price prediction?',
  ];

  const handleQuickQuestion = (question) => {
    setInput(question);
  };

  return (
    <div className="chatbot-container">
      <div className="chatbot-header">
        <div className="chatbot-title">
          <SmartToyIcon />
          <span>AI Stock Analyst</span>
        </div>
        <select
          className="chatbot-lang-select"
          value={chatLanguage}
          onChange={(e) => setChatLanguage(e.target.value)}
          title="Chat language"
        >
          <option value="auto">Auto Detect</option>
          <option value="en">English</option>
          <option value="hi">Hindi</option>
          <option value="ta">Tamil</option>
          <option value="te">Telugu</option>
          <option value="ml">Malayalam</option>
          <option value="kn">Kannada</option>
        </select>
      </div>

      <div className="chatbot-messages">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`message ${message.type === 'user' ? 'user-message' : 'bot-message'}`}
          >
            <div className="message-icon">
              {message.type === 'user' ? <PersonIcon /> : <SmartToyIcon />}
            </div>
            <div className="message-content">
              <div className="message-text">{message.text}</div>
              <div className="message-time">
                {new Date(message.timestamp).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="message bot-message">
            <div className="message-icon">
              <SmartToyIcon />
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {!loading && messages.length <= 2 && (
        <div className="quick-questions">
          <div className="quick-questions-label">Quick Questions:</div>
          {quickQuestions.map((question, index) => (
            <button
              key={index}
              className="quick-question-btn"
              onClick={() => handleQuickQuestion(question)}
            >
              {question}
            </button>
          ))}
        </div>
      )}

      <div className="chatbot-input">
        <input
          type="text"
          placeholder="Ask me anything about the stock..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}>
          <SendIcon />
        </button>
      </div>
    </div>
  );
};

export default ChatBot;
