import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import AssistantChat from './AssistantChat';

// Translation copy belongs to AppContext's own tests; stubbing t() as the
// identity function keeps these assertions about behaviour, not wording.
vi.mock('../contexts/AppContext', () => ({
  useApp: () => ({ t: (key) => key }),
}));

let mockState;

vi.mock('../stores/useAssistantStore', () => ({
  useAssistantStore: (selector) => selector(mockState),
}));

describe('AssistantChat', () => {
  beforeEach(() => {
    mockState = {
      isOpen: true,
      messages: [],
      pending: false,
      error: null,
      toggleOpen: vi.fn(),
      ask: vi.fn(),
    };
  });

  it('shows the welcome message before any question has been asked', () => {
    render(<AssistantChat />);

    expect(screen.getByText('assistant_welcome')).toBeInTheDocument();
  });

  it('renders each message of the conversation in order', () => {
    mockState.messages = [
      { id: 1, role: 'user', text: 'What is CNC-03 OEE this week?' },
      { id: 2, role: 'assistant', text: 'CNC-03 is running at 67% OEE this week.' },
    ];

    render(<AssistantChat />);

    expect(screen.getByText('What is CNC-03 OEE this week?')).toBeInTheDocument();
    expect(screen.getByText('CNC-03 is running at 67% OEE this week.')).toBeInTheDocument();
    expect(screen.queryByText('assistant_welcome')).not.toBeInTheDocument();
  });

  it('shows a thinking bubble while the assistant is working on an answer', () => {
    mockState.pending = true;

    render(<AssistantChat />);

    expect(screen.getByText('assistant_thinking')).toBeInTheDocument();
  });

  it('surfaces a translatable notice when the last request failed', () => {
    mockState.error = 'assistant_error';

    render(<AssistantChat />);

    expect(screen.getByText('assistant_error')).toBeInTheDocument();
  });

  it('asks the assistant the typed question and clears the composer', async () => {
    const user = userEvent.setup();
    render(<AssistantChat />);

    const input = screen.getByPlaceholderText('assistant_placeholder');
    await user.type(input, 'What is DB-01 OEE today?');
    await user.click(screen.getByRole('button', { name: 'send' }));

    expect(mockState.ask).toHaveBeenCalledWith('What is DB-01 OEE today?');
    expect(input).toHaveValue('');
  });

  it('keeps the send button disabled until something is typed', () => {
    render(<AssistantChat />);

    expect(screen.getByRole('button', { name: 'send' })).toBeDisabled();
  });

  it('disables the composer while a request is pending', () => {
    mockState.pending = true;

    render(<AssistantChat />);

    expect(screen.getByPlaceholderText('assistant_placeholder')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'send' })).toBeDisabled();
  });

  it('keeps the conversation panel hidden until the widget is opened', async () => {
    mockState.isOpen = false;
    const user = userEvent.setup();
    render(<AssistantChat />);

    expect(screen.queryByPlaceholderText('assistant_placeholder')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'toggle assistant' }));

    expect(mockState.toggleOpen).toHaveBeenCalledTimes(1);
  });
});
