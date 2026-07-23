import React, { useState, memo } from 'react';
import { User, Bot, Copy, Check, Terminal } from 'lucide-react';
import MessageToolbar from './MessageToolbar';

// Production-ready streaming markdown renderer that preserves every single line
const renderMarkdown = (text) => {
  if (!text) return null;

  // Split text into code blocks vs standard markdown
  const parts = text.split(/(```[\s\S]*?```)/g);

  return parts.map((part, index) => {
    if (part.startsWith('```') && part.endsWith('```')) {
      const firstLineEnd = part.indexOf('\n');
      let lang = 'code';
      let code = part.slice(3, -3);

      if (firstLineEnd !== -1 && firstLineEnd < 20) {
        lang = part.slice(3, firstLineEnd).trim() || 'code';
        code = part.slice(firstLineEnd + 1, -3);
      }

      return <CodeBlock key={index} language={lang} code={code.trim()} />;
    }

    // Process standard text lines without discarding non-bullet text
    const lines = part.split('\n');
    const elements = [];
    let currentList = [];

    const flushList = () => {
      if (currentList.length > 0) {
        elements.push(
          <ul key={`ul-${elements.length}`} className="list-disc list-inside space-y-1 text-xs text-gray-700 dark:text-gray-200 my-2 pl-2">
            {currentList.map((item, iIdx) => (
              <li key={iIdx}>{formatInlineMarkdown(item)}</li>
            ))}
          </ul>
        );
        currentList = [];
      }
    };

    lines.forEach((line, lIdx) => {
      const trimmed = line.trim();

      if (!trimmed) {
        flushList();
        return;
      }

      // Check if bullet point item
      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        const bulletText = trimmed.replace(/^[-*]\s+/, '');
        currentList.push(bulletText);
        return;
      }

      // Non-bullet line: flush any pending bullet list
      flushList();

      // Headers
      if (trimmed.startsWith('#### ')) {
        elements.push(
          <h5 key={lIdx} className="text-xs font-bold text-gray-900 dark:text-white mt-2 mb-1">
            {formatInlineMarkdown(trimmed.replace(/^####\s+/, ''))}
          </h5>
        );
      } else if (trimmed.startsWith('### ')) {
        elements.push(
          <h4 key={lIdx} className="text-sm font-bold text-gray-900 dark:text-white mt-3 mb-1">
            {formatInlineMarkdown(trimmed.replace(/^###\s+/, ''))}
          </h4>
        );
      } else if (trimmed.startsWith('## ')) {
        elements.push(
          <h3 key={lIdx} className="text-base font-bold text-gray-900 dark:text-white mt-4 mb-2">
            {formatInlineMarkdown(trimmed.replace(/^##\s+/, ''))}
          </h3>
        );
      } else if (trimmed.startsWith('# ')) {
        elements.push(
          <h2 key={lIdx} className="text-lg font-black text-gray-900 dark:text-white mt-4 mb-2">
            {formatInlineMarkdown(trimmed.replace(/^#\s+/, ''))}
          </h2>
        );
      } else {
        // Standard paragraph line
        elements.push(
          <p key={lIdx} className="text-xs text-gray-800 dark:text-gray-200 leading-relaxed my-1">
            {formatInlineMarkdown(trimmed)}
          </p>
        );
      }
    });

    flushList();

    return <div key={index} className="space-y-1">{elements}</div>;
  });
};

const formatInlineMarkdown = (text) => {
  if (!text) return text;

  // Split by bold (**text**) and inline code (`text`)
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);

  return parts.map((chunk, idx) => {
    if (chunk.startsWith('**') && chunk.endsWith('**')) {
      return <strong key={idx} className="font-semibold text-gray-900 dark:text-white">{chunk.slice(2, -2)}</strong>;
    }
    if (chunk.startsWith('`') && chunk.endsWith('`')) {
      return (
        <code key={idx} className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-indigo-600 dark:text-indigo-300 font-mono text-[11px]">
          {chunk.slice(1, -1)}
        </code>
      );
    }
    return chunk;
  });
};

const CodeBlock = ({ language, code }) => {
  const [copied, setCopied] = useState(false);

  const handleCopyCode = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  return (
    <div className="my-3 rounded-2xl bg-gray-900 text-gray-100 overflow-hidden border border-gray-800 shadow-md">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-950/80 border-b border-gray-800 text-xs">
        <div className="flex items-center space-x-2 text-gray-400">
          <Terminal size={14} />
          <span className="font-mono text-[11px] uppercase tracking-wider">{language}</span>
        </div>
        <button
          type="button"
          onClick={handleCopyCode}
          className="flex items-center space-x-1 text-[11px] text-gray-400 hover:text-white transition-colors"
        >
          {copied ? (
            <>
              <Check size={13} className="text-emerald-400" />
              <span className="text-emerald-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy size={13} />
              <span>Copy Code</span>
            </>
          )}
        </button>
      </div>
      <div className="p-4 overflow-x-auto font-mono text-xs text-gray-200 leading-relaxed">
        <pre>{code}</pre>
      </div>
    </div>
  );
};

const StreamingMessage = memo(({ message, onRegenerate, onDelete }) => {
  const isUser = message.role === 'user';
  const timestamp = message.timestamp ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
  const renderedContent = renderMarkdown(message.content);

  return (
    <div className={`flex items-start space-x-3 py-3 px-4 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className={`p-2 rounded-2xl flex-shrink-0 ${
          isUser
            ? 'bg-indigo-600 text-white shadow-md'
            : 'bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 border border-gray-100 dark:border-gray-700/60 shadow-sm'
        }`}
      >
        {isUser ? <User size={18} /> : <Bot size={18} />}
      </div>

      {/* Content Card */}
      <div className={`max-w-2xl ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`p-4 rounded-3xl shadow-sm text-xs leading-relaxed ${
            isUser
              ? 'bg-indigo-600 text-white rounded-tr-none'
              : 'bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700/60 text-gray-900 dark:text-white rounded-tl-none'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            renderedContent || (
              <span className="inline-flex items-center space-x-2 text-indigo-500 animate-pulse font-medium">
                <span>Generating response...</span>
              </span>
            )
          )}
        </div>

        {/* Timestamp & Toolbar */}
        <div className={`flex items-center space-x-2 px-1 text-[10px] text-gray-400 mt-1 ${isUser ? 'justify-end' : 'justify-start'}`}>
          {timestamp && <span>{timestamp}</span>}
          <MessageToolbar
            text={message.content}
            onRegenerate={isUser ? null : onRegenerate}
            onDelete={onDelete}
            isAssistant={!isUser}
          />
        </div>
      </div>
    </div>
  );
});

StreamingMessage.displayName = 'StreamingMessage';

export default StreamingMessage;
