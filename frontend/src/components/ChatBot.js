import React, { useEffect, useMemo, useRef, useState } from 'react';
import SendIcon from '@mui/icons-material/Send';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import CloseIcon from '@mui/icons-material/Close';
import MicIcon from '@mui/icons-material/Mic';
import PersonIcon from '@mui/icons-material/Person';
import ForumIcon from '@mui/icons-material/Forum';
import { chatWithAI } from '../services/api';
import './ChatBot.css';

const STARTER_MESSAGE = {
  type: 'bot',
  text: 'Hi. I am your multilingual stock assistant. You can ask in English, Tamil, Hindi, or Tanglish.',
  timestamp: new Date().toISOString(),
};

const PLACEHOLDER_BY_LANG = {
  tanglish: 'ippa endha stock analyze pannanum?',
  ta: '??????? ???? ??????? ??????????? ????? ?????????',
  hi: '?? ?? ??? ????? ?? ???????? ???? ????? ????',
  en: 'What stock do you want to analyze now?',
};

const detectMessageLanguage = (text) => {
  const value = String(text || '').trim();
  if (!value) return 'en';

  if (/[\u0B80-\u0BFF]/.test(value)) return 'ta';
  if (/[\u0900-\u097F]/.test(value)) return 'hi';

  const normalized = value.toLowerCase();
  const tanglishMarkers = [
    'intha', 'indha', 'nalla', 'iruka', 'irukka', 'vangalama', 'pannalama',
    'vaangalama', 'enna', 'epdi', 'ipo', 'ippo', 'stock', 'buy', 'sell',
  ];

  const hits = tanglishMarkers.filter((word) => normalized.includes(word)).length;
  if (hits >= 2) return 'tanglish';

  return 'en';
};

const ChatBot = ({ symbol, stockName, recommendation, prediction }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([STARTER_MESSAGE]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatLanguage, setChatLanguage] = useState('auto');
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  const quickQuestions = useMemo(
    () => [
      'Should I buy this stock now?',
      'intha stock nalla iruka?',
      '???? ?? ????? ?????? ??? ???',
      'Give a simple risk explanation',
      'Explain this prediction in simple words',
    ],
    []
  );

  const dynamicPlaceholder = useMemo(() => {
    const lastUserMessage = [...messages].reverse().find((item) => item.type === 'user');
    const lang = detectMessageLanguage(lastUserMessage?.text);
    return PLACEHOLDER_BY_LANG[lang] || PLACEHOLDER_BY_LANG.en;
  }, [messages]);

  useEffect(() => {
    if (!isOpen) return;
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isOpen]);

  useEffect(() => {
    if (!symbol) return;
    setMessages((prev) => {
      const notice = {
        type: 'bot',
        text: `Context switched to ${stockName || symbol}. Ask for analysis, recommendation, prediction, risk, or portfolio suggestions.`,
        timestamp: new Date().toISOString(),
      };
      const next = [...prev, notice];
      return next.slice(-40);
    });
  }, [symbol, stockName]);

  const addMessage = (type, text) => {
    setMessages((prev) => {
      const next = [...prev, { type, text, timestamp: new Date().toISOString() }];
      return next.slice(-50);
    });
  };

  const sendMessage = async () => {
    const userMessage = input.trim();
    if (!userMessage || loading) return;

    addMessage('user', userMessage);
    setInput('');
    setLoading(true);

    try {
      const selectedLanguage = chatLanguage === 'auto' ? undefined : chatLanguage;
      const response = await chatWithAI(userMessage, symbol, selectedLanguage, {
        stockName,
        recommendation,
        prediction,
      });

      addMessage('bot', response.response || 'I could not generate a response right now.');
    } catch (error) {
      console.error('Chat error:', error);
      addMessage('bot', 'I hit an error while processing that. Please retry.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const handleQuickQuestion = (question) => {
    setInput(question);
  };

  const toggleVoiceInput = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      addMessage('bot', 'Voice input is not supported in this browser.');
      return;
    }

    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang =
      chatLanguage === 'ta'
        ? 'ta-IN'
        : chatLanguage === 'hi'
          ? 'hi-IN'
          : 'en-IN';

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => {
      setIsListening(false);
      addMessage('bot', 'Voice capture failed. Please try again.');
    };
    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript;
      if (transcript) {
        setInput((prev) => (prev ? `${prev} ${transcript}` : transcript));
      }
    };

    recognition.start();
  };

  return (
    <div className="chatbot-fab-wrap">
      <button
        type="button"
        className="chatbot-fab"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label="Toggle chatbot"
      >
        {isOpen ? <CloseIcon /> : <ForumIcon />}
      </button>

      {isOpen && (
        <div className="chatbot-panel" role="dialog" aria-label="AI stock chatbot">
          <div className="chatbot-header">
            <div className="chatbot-title">
              <SmartToyIcon />
              <div>
                <div>AI Stock Chat</div>
                <small>{symbol ? `Tracking: ${symbol}` : 'General finance mode'}</small>
              </div>
            </div>

            <select
              className="chatbot-lang-select"
              value={chatLanguage}
              onChange={(e) => setChatLanguage(e.target.value)}
              title="Chat language"
            >
              <option value="auto">Auto Detect</option>
              <option value="en">English</option>
              <option value="ta">Tamil</option>
              <option value="hi">Hindi</option>
              <option value="tanglish">Tanglish</option>
            </select>
          </div>

          <div className="chatbot-messages">
            {messages.map((message, index) => (
              <div
                key={`${message.type}-${index}-${message.timestamp}`}
                className={`message ${message.type === 'user' ? 'user-message' : 'bot-message'}`}
              >
                <div className="message-icon">
                  {message.type === 'user' ? <PersonIcon fontSize="small" /> : <SmartToyIcon fontSize="small" />}
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
                  <SmartToyIcon fontSize="small" />
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

          {!loading && messages.length <= 3 && (
            <div className="quick-questions">
              {quickQuestions.map((question, index) => (
                <button
                  key={`quick-${index}`}
                  type="button"
                  className="quick-question-btn"
                  onClick={() => handleQuickQuestion(question)}
                >
                  {question}
                </button>
              ))}
            </div>
          )}

          <div className="chatbot-input">
            <button
              type="button"
              className={`voice-btn ${isListening ? 'listening' : ''}`}
              onClick={toggleVoiceInput}
              title="Voice input"
            >
              <MicIcon fontSize="small" />
            </button>
            <textarea
              rows={2}
              placeholder={dynamicPlaceholder}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            <button type="button" onClick={sendMessage} disabled={loading || !input.trim()}>
              <SendIcon fontSize="small" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatBot;
