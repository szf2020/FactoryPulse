import { create } from 'zustand';
import { askAssistant } from '../services/assistantApi';

let nextMessageId = 1;
const newMessageId = () => nextMessageId++;

/**
 * Assistant Chat Store (Zustand).
 * Holds the conversation shown in the chat widget and talks to the
 * FactoryPulse Assistant service. Kept outside React state so the
 * conversation survives the widget being closed/reopened or remounted.
 */
export const useAssistantStore = create((set, get) => ({
  isOpen: false,
  messages: [],
  pending: false,
  error: null,

  toggleOpen: () => set((state) => ({ isOpen: !state.isOpen })),
  close: () => set({ isOpen: false }),

  /**
   * Sends a question to the assistant, appending the user message immediately
   * and the assistant's reply (or an error notice) once it resolves.
   * @param {string} question
   */
  ask: async (question) => {
    const trimmed = question.trim();
    if (!trimmed || get().pending) return;

    set((state) => ({
      messages: [...state.messages, { id: newMessageId(), role: 'user', text: trimmed }],
      pending: true,
      error: null,
    }));

    try {
      const answer = await askAssistant(trimmed);
      set((state) => ({
        messages: [...state.messages, { id: newMessageId(), role: 'assistant', text: answer }],
        pending: false,
      }));
    } catch {
      set({ pending: false, error: 'assistant_error' });
    }
  },

  reset: () => set({ messages: [], pending: false, error: null }),
}));
