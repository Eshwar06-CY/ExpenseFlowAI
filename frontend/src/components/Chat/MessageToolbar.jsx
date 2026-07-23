import React, { useState } from 'react';
import { Copy, Check, RotateCcw, Trash2, ThumbsUp, ThumbsDown } from 'lucide-react';

const MessageToolbar = ({ text, onRegenerate, onDelete, isAssistant = true }) => {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState(null); // 'like' | 'dislike'

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy message:', err);
    }
  };

  const handleFeedback = (type) => {
    setFeedback(feedback === type ? null : type);
  };

  return (
    <div className="flex items-center space-x-1 mt-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
      <button
        type="button"
        onClick={handleCopy}
        title="Copy message"
        className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700/60 transition-colors"
      >
        {copied ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
      </button>

      {isAssistant && onRegenerate && (
        <button
          type="button"
          onClick={onRegenerate}
          title="Regenerate response"
          className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700/60 transition-colors"
        >
          <RotateCcw size={14} />
        </button>
      )}

      {isAssistant && (
        <>
          <button
            type="button"
            onClick={() => handleFeedback('like')}
            title="Helpful response"
            className={`p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700/60 transition-colors ${
              feedback === 'like' ? 'text-indigo-600 dark:text-indigo-400 font-bold' : ''
            }`}
          >
            <ThumbsUp size={14} />
          </button>
          <button
            type="button"
            onClick={() => handleFeedback('dislike')}
            title="Not helpful"
            className={`p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700/60 transition-colors ${
              feedback === 'dislike' ? 'text-rose-600 dark:text-rose-400 font-bold' : ''
            }`}
          >
            <ThumbsDown size={14} />
          </button>
        </>
      )}

      {onDelete && (
        <button
          type="button"
          onClick={onDelete}
          title="Delete message"
          className="p-1 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/40 text-gray-400 hover:text-rose-600 transition-colors"
        >
          <Trash2 size={14} />
        </button>
      )}
    </div>
  );
};

export default MessageToolbar;
