import { beforeEach, describe, expect, it, vi } from 'vitest';

import { askAssistant } from '../services/assistantApi';
import { useAssistantStore } from './useAssistantStore';

vi.mock('../services/assistantApi', () => ({
  askAssistant: vi.fn(),
}));

describe('useAssistantStore', () => {
  beforeEach(() => {
    useAssistantStore.setState({ isOpen: false, messages: [], pending: false, error: null });
    vi.mocked(askAssistant).mockReset();
  });

  it('toggles the widget open and closed', () => {
    useAssistantStore.getState().toggleOpen();
    expect(useAssistantStore.getState().isOpen).toBe(true);

    useAssistantStore.getState().toggleOpen();
    expect(useAssistantStore.getState().isOpen).toBe(false);
  });

  it('closes the widget regardless of its current state', () => {
    useAssistantStore.setState({ isOpen: true });

    useAssistantStore.getState().close();

    expect(useAssistantStore.getState().isOpen).toBe(false);
  });

  it('clears the conversation back to its initial shape', () => {
    useAssistantStore.setState({
      messages: [{ id: 1, role: 'user', text: 'hi' }],
      pending: true,
      error: 'assistant_error',
    });

    useAssistantStore.getState().reset();

    expect(useAssistantStore.getState()).toMatchObject({ messages: [], pending: false, error: null });
  });

  it('appends the question immediately and marks the request as pending', () => {
    askAssistant.mockReturnValue(new Promise(() => {})); // never resolves in this test

    useAssistantStore.getState().ask('What is CNC-03 OEE this week?');

    const state = useAssistantStore.getState();
    expect(state.pending).toBe(true);
    expect(state.error).toBeNull();
    expect(state.messages).toEqual([
      expect.objectContaining({ role: 'user', text: 'What is CNC-03 OEE this week?' }),
    ]);
  });

  it('appends the answer and clears pending once the assistant responds', async () => {
    askAssistant.mockResolvedValue('CNC-03 is running at 67% OEE this week.');

    await useAssistantStore.getState().ask('What is CNC-03 OEE this week?');

    const state = useAssistantStore.getState();
    expect(state.pending).toBe(false);
    expect(state.messages.map((message) => [message.role, message.text])).toEqual([
      ['user', 'What is CNC-03 OEE this week?'],
      ['assistant', 'CNC-03 is running at 67% OEE this week.'],
    ]);
  });

  it('records a translatable error notice and clears pending when the request fails', async () => {
    askAssistant.mockRejectedValue(new Error('network down'));

    await useAssistantStore.getState().ask('What is CNC-03 OEE this week?');

    const state = useAssistantStore.getState();
    expect(state.pending).toBe(false);
    expect(state.error).toBe('assistant_error');
    // The question itself still lands in the conversation even though the answer failed.
    expect(state.messages).toHaveLength(1);
  });

  it('ignores blank questions', async () => {
    await useAssistantStore.getState().ask('   ');

    expect(askAssistant).not.toHaveBeenCalled();
    expect(useAssistantStore.getState().messages).toEqual([]);
  });

  it('ignores a new question while one is still pending', async () => {
    askAssistant.mockReturnValue(new Promise(() => {}));
    useAssistantStore.getState().ask('first question');

    await useAssistantStore.getState().ask('second question');

    expect(askAssistant).toHaveBeenCalledTimes(1);
    expect(askAssistant).toHaveBeenCalledWith('first question');
  });
});
