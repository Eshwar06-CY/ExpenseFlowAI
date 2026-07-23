import React, { useState, useRef, useEffect } from 'react';
import { Send, Square, Sparkles, Calendar } from 'lucide-react';

const ChatInput = ({ onSend, onStop, isGenerating = false, period = "30d", onPeriodChange }) => {
  const [prompt, setPrompt] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [prompt]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if (!prompt.trim() || isGenerating) return;
    onSend(prompt.trim());
    setPrompt('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-4">
      <div className="relative bg-white dark:bg-gray-800 rounded-3xl border border-gray-200 dark:border-gray-700 shadow-xl focus-within:ring-2 focus-within:ring-indigo-500/30 transition-all p-3">
        
        {/* Top Controls Bar */}
        <div className="flex items-center justify-between px-2 pb-2 mb-1 border-b border-gray-100 dark:border-gray-700/50">
          <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
            <Sparkles size={14} className="text-indigo-500" />
            <span className="font-semibold text-gray-700 dark:text-gray-300">ExpenseFlow Personal CFO</span>
          </div>

          <div className="flex items-center space-x-2">
            <Calendar size={13} className="text-gray-400" />
            <select
              value={period}
              onChange={(e) => onPeriodChange(e.target.value)}
              className="text-[11px] font-semibold bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 border-0 rounded-lg px-2 py-0.5 outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="7d">7 Days</option>
              <option value="30d">30 Days</option>
              <option value="90d">90 Days</option>
              <option value="1y">1 Year</option>
            </select>
          </div>
        </div>

        {/* Text Area Input */}
        <textarea
          ref={textareaRef}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask your AI CFO about spending, budgets, savings, or goals... (Press Enter to send, Shift+Enter for new line)"
          rows={1}
          disabled={isGenerating}
          className="w-full bg-transparent text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 outline-none resize-none px-2 py-1 max-h-44"
        />

        {/* Action Button Bar */}
        <div className="flex items-center justify-between pt-2 px-1">
          <div className="text-[11px] text-gray-400">
            {isGenerating ? (
              <span className="text-indigo-500 dark:text-indigo-400 animate-pulse font-medium">
                Streaming response from Gemini 2.5 Flash...
              </span>
            ) : (
              <span>Shift+Enter for newline</span>
            )}
          </div>

          {isGenerating ? (
            <button
              type="button"
              onClick={onStop}
              className="inline-flex items-center px-3.5 py-1.5 rounded-xl text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 shadow-md transition-all animate-pulse"
            >
              <Square size={13} className="mr-1.5 fill-current" />
              Stop Generating
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!prompt.trim()}
              className="inline-flex items-center p-2.5 rounded-2xl text-white bg-indigo-600 hover:bg-indigo-700 shadow-md shadow-indigo-600/30 transition-all disabled:opacity-40 disabled:hover:bg-indigo-600"
            >
              <Send size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatInput;
