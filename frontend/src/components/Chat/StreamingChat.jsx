import React, { useState, useEffect, useRef } from 'react';
import { Sparkles, Bot, Trash2, RefreshCw, AlertCircle, MessageSquare } from 'lucide-react';
import StreamingMessage from './StreamingMessage';
import TypingIndicator from './TypingIndicator';
import ChatInput from './ChatInput';
import api, { getAccessToken } from '../../services/api';

const LOCAL_STORAGE_KEY = 'ef_chat_history_v2';

const SUGGESTIONS = [
  'How can I optimize my monthly expenses?',
  'What if I buy a ₹1.5 lakh bike?',
  'Calculate my 90-day cashflow forecast',
  'What are my top spending anomalies?'
];

const StreamingChat = () => {
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(LOCAL_STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [period, setPeriod] = useState('30d');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [streamError, setStreamError] = useState(null);

  const abortControllerRef = useRef(null);
  const chatContainerRef = useRef(null);
  const userScrolledUpRef = useRef(false);

  // Save conversation history locally
  useEffect(() => {
    try {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(messages.slice(-20)));
    } catch (err) {
      console.error('Failed to persist chat history:', err);
    }
  }, [messages]);

  // Handle scroll detection
  const handleScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 60;
    userScrolledUpRef.current = !isAtBottom;
  };

  const scrollToBottom = (force = false) => {
    if (chatContainerRef.current && (force || !userScrolledUpRef.current)) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isConnecting]);

  const handleSendMessage = async (promptText) => {
    if (!promptText.trim() || isGenerating) return;

    // 0. Cancel any active existing stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    setStreamError(null);
    userScrolledUpRef.current = false;

    // 1. Create User & Assistant Message Placeholders
    const userMsgId = Date.now().toString();
    const assistantMsgId = (Date.now() + 1).toString();

    const userMsg = {
      id: userMsgId,
      role: 'user',
      content: promptText,
      timestamp: new Date().toISOString()
    };

    const assistantMsg = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString()
    };

    // 2. Atomically Append Both Messages to State BEFORE Fetch
    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsConnecting(true);
    setIsGenerating(true);

    abortControllerRef.current = new AbortController();

    try {
      // 3. Initiate Fetch Stream Request
      const token = getAccessToken() || localStorage.getItem('token') || localStorage.getItem('ef_token') || localStorage.getItem('access_token');
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8080/api/v1';
      const streamUrl = `${baseUrl.replace(/\/$/, '')}/ai/chat/stream`;

      console.log('[Streaming Pipeline Audit] Initiating SSE fetch to:', streamUrl);

      const response = await fetch(streamUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify({
          prompt: promptText,
          period: period,
          chat_history: messages.slice(-4).map((m) => ({ role: m.role, content: m.content }))
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`Server returned status ${response.status}`);
      }

      setIsConnecting(false);

      // 4. Read SSE Stream Chunks
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const rawChunk = decoder.decode(value, { stream: true });
        console.log('[Streaming Pipeline Audit] Incoming Raw Chunk:', rawChunk);

        buffer += rawChunk;
        const eventBlocks = buffer.split('\n\n');
        buffer = eventBlocks.pop() || '';

        for (const eventBlock of eventBlocks) {
          const lines = eventBlock.split('\n');
          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('data: ')) {
              const jsonStr = trimmed.slice(6).trim();
              if (!jsonStr) continue;
              try {
                const data = JSON.parse(jsonStr);
                console.log('[Streaming Pipeline Audit] Parsed SSE Payload:', data);

                if (data.type === 'token' && data.content !== undefined) {
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMsgId
                        ? { ...msg, content: msg.content + data.content }
                        : msg
                    )
                  );
                  scrollToBottom();
                } else if (data.type === 'done') {
                  console.log('[Streaming Pipeline Audit] Stream marked DONE by server.');
                  setIsGenerating(false);
                } else if (data.type === 'error') {
                  console.error('[Streaming Pipeline Audit] Stream returned Error:', data.message);
                  setStreamError(data.message);
                  setIsGenerating(false);
                }
              } catch (err) {
                console.error('[Streaming Pipeline Audit] SSE JSON parse error:', err, 'raw line:', trimmed);
              }
            }
          }
        }
      }

      // Process any trailing leftover chunk in buffer
      if (buffer.trim()) {
        const lines = buffer.split('\n');
        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data: ')) {
            try {
              const data = JSON.parse(trimmed.slice(6).trim());
              if (data.type === 'token' && data.content !== undefined) {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMsgId
                      ? { ...msg, content: msg.content + data.content }
                      : msg
                  )
                );
              }
            } catch (err) {
              console.error('Trailing buffer parse error:', err);
            }
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        console.log('Stream cancelled by user.');
      } else {
        console.error('Streaming chat failed:', err);
        setStreamError(err.message || 'Connection lost. Unable to stream response.');
      }
    } finally {
      setIsConnecting(false);
      setIsGenerating(false);
      abortControllerRef.current = null;
    }
  };

  const handleStopGenerating = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsGenerating(false);
      setIsConnecting(false);
    }
  };

  const handleClearHistory = () => {
    setMessages([]);
    localStorage.removeItem(LOCAL_STORAGE_KEY);
  };

  const handleDeleteMessage = (id) => {
    setMessages((prev) => prev.filter((m) => m.id !== id));
  };

  const handleRegenerate = (msgIndex) => {
    const prevUserMsg = messages[msgIndex - 1];
    if (prevUserMsg && prevUserMsg.role === 'user') {
      handleSendMessage(prevUserMsg.content);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)] max-w-5xl mx-auto bg-gray-50 dark:bg-gray-900 rounded-3xl overflow-hidden border border-gray-100 dark:border-gray-800 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-white dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700/60">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-2xl bg-indigo-600 text-white shadow-md shadow-indigo-600/30">
            <Sparkles size={20} />
          </div>
          <div>
            <h2 className="text-base font-bold text-gray-900 dark:text-white">AI Personal CFO Assistant</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">Real-time streaming powered by ExpenseFlow FinanceEngine & Google Gemini 3.6 Flash</p>
          </div>
        </div>

        {messages.length > 0 && (
          <button
            type="button"
            onClick={handleClearHistory}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-gray-500 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-all"
          >
            <Trash2 size={14} />
            <span>Clear History</span>
          </button>
        )}
      </div>

      {/* Messages Scroll Area */}
      <div
        ref={chatContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 space-y-2 scroll-smooth"
      >
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-6">
            <div className="p-4 rounded-3xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 border border-indigo-100 dark:border-indigo-800">
              <Bot size={36} />
            </div>
            <div className="max-w-md">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">Welcome to ExpenseFlow AI Chat</h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Ask your Personal CFO anything about your cashflow, budgets, goals, or upcoming bill projections.
              </p>
            </div>

            {/* Suggestion Chips */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-lg">
              {SUGGESTIONS.map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSendMessage(s)}
                  className="p-3 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-left text-xs font-medium text-gray-700 dark:text-gray-200 hover:border-indigo-500 hover:text-indigo-600 dark:hover:text-indigo-400 shadow-sm transition-all flex items-center space-x-2"
                >
                  <MessageSquare size={14} className="text-indigo-500 flex-shrink-0" />
                  <span className="line-clamp-2">{s}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <StreamingMessage
              key={msg.id || idx}
              message={msg}
              onRegenerate={() => handleRegenerate(idx)}
              onDelete={() => handleDeleteMessage(msg.id)}
            />
          ))
        )}

        {isConnecting && <TypingIndicator />}

        {streamError && (
          <div className="p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertCircle size={16} />
              <span>{streamError}</span>
            </div>
            <button
              type="button"
              onClick={() => handleSendMessage(messages[messages.length - 1]?.content || 'Hello')}
              className="inline-flex items-center px-3 py-1 rounded-xl text-xs font-semibold bg-rose-600 text-white hover:bg-rose-700 shadow-sm"
            >
              <RefreshCw size={12} className="mr-1.5" />
              Retry
            </button>
          </div>
        )}
      </div>

      {/* Input Dock */}
      <ChatInput
        onSend={handleSendMessage}
        onStop={handleStopGenerating}
        isGenerating={isGenerating || isConnecting}
        period={period}
        onPeriodChange={setPeriod}
      />
    </div>
  );
};

export default StreamingChat;