import React, { useEffect, useRef, useState } from 'react';
import { Bot, MessageCircle, Send, X } from 'lucide-react';
import { useApp } from '../contexts/AppContext';
import { useAssistantStore } from '../stores/useAssistantStore';

/**
 * Floating Assistant Chat Widget.
 * A toggleable panel that lets the user ask natural-language questions about
 * machine OEE and downtime. State (open/closed, messages, pending, error) is
 * held in `useAssistantStore` (Zustand) so the conversation survives the
 * widget being closed and reopened while navigating the app.
 */
export default function AssistantChat() {
  const { t } = useApp();
  const isOpen = useAssistantStore((state) => state.isOpen);
  const messages = useAssistantStore((state) => state.messages);
  const pending = useAssistantStore((state) => state.pending);
  const error = useAssistantStore((state) => state.error);
  const toggleOpen = useAssistantStore((state) => state.toggleOpen);
  const ask = useAssistantStore((state) => state.ask);

  const [draft, setDraft] = useState('');
  const scrollRef = useRef(null);

  // Auto-scroll Effect — keeps the latest message in view as the conversation grows.
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, pending, isOpen]);

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!draft.trim() || pending) return;
    ask(draft);
    setDraft('');
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
      {isOpen && (
        <div className="w-80 sm:w-96 h-[28rem] flex flex-col bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-white/10 shadow-2xl overflow-hidden animate-fade-in">
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-white/5 bg-slate-50 dark:bg-slate-900">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400">
                <Bot size={20} />
              </div>
              <div>
                <h3 className="font-bold text-sm text-slate-800 dark:text-white leading-tight">{t('assistant_title')}</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">{t('assistant_subtitle')}</p>
              </div>
            </div>
            <button
              onClick={toggleOpen}
              aria-label="close"
              className="p-2 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 dark:hover:bg-white/5 dark:hover:text-white transition-colors"
            >
              <X size={18} />
            </button>
          </div>

          {/* Message List */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
            {messages.length === 0 && (
              <ChatBubble role="assistant" text={t('assistant_welcome')} />
            )}
            {messages.map((message) => (
              <ChatBubble key={message.id} role={message.role} text={message.text} />
            ))}
            {pending && <ChatBubble role="assistant" text={t('assistant_thinking')} muted />}
            {error && <ChatBubble role="assistant" text={t(error)} muted />}
          </div>

          {/* Composer */}
          <form onSubmit={handleSubmit} className="flex items-center gap-2 px-4 py-3 border-t border-slate-200 dark:border-white/5">
            <input
              type="text"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder={t('assistant_placeholder')}
              disabled={pending}
              className="flex-1 bg-slate-100 dark:bg-slate-900 border-none outline-none rounded-full px-4 py-2.5 text-sm text-slate-700 dark:text-white placeholder-slate-400 disabled:opacity-60"
            />
            <button
              type="submit"
              disabled={pending || !draft.trim()}
              aria-label="send"
              className="p-2.5 rounded-full bg-blue-600 text-white hover:bg-blue-700 transition-colors disabled:opacity-40 disabled:hover:bg-blue-600"
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      )}

      {/* Toggle Button */}
      <button
        onClick={toggleOpen}
        aria-label="toggle assistant"
        className="p-4 rounded-full bg-blue-600 text-white shadow-xl hover:bg-blue-700 transition-all hover:scale-105"
      >
        {isOpen ? <X size={22} /> : <MessageCircle size={22} />}
      </button>
    </div>
  );
}

/**
 * Single chat message bubble.
 * Aligns and colors itself based on the sender (`user` vs `assistant`).
 */
const ChatBubble = ({ role, text, muted = false }) => {
  const isUser = role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-sm'
            : muted
            ? 'bg-slate-100 dark:bg-slate-900 text-slate-400 dark:text-slate-500 italic rounded-bl-sm'
            : 'bg-slate-100 dark:bg-slate-900 text-slate-700 dark:text-slate-200 rounded-bl-sm'
        }`}
      >
        {text}
      </div>
    </div>
  );
};
