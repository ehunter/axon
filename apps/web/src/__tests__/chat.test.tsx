/**
 * Chat Components Tests
 * 
 * Tests for the chat view components matching Oskar Figma design.
 * Using existing theme tokens - no custom styles.
 */

import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ChatMessage } from '@/components/chat/chat-message';
import { ChatInput } from '@/components/chat/chat-input';
import { ChatHeader } from '@/components/chat/chat-header';

describe('ChatMessage Component', () => {
  describe('User Message', () => {
    it('renders user message with correct content', () => {
      render(
        <ChatMessage
          role="user"
          content="How many samples do you have?"
        />
      );
      expect(screen.getByText('How many samples do you have?')).toBeInTheDocument();
    });

    it('renders user message right-aligned', () => {
      render(
        <ChatMessage
          role="user"
          content="Test message"
        />
      );
      const container = screen.getByText('Test message').closest('div[data-message-container]');
      expect(container).toHaveClass('justify-end');
    });

    it('renders user message with secondary background', () => {
      render(
        <ChatMessage
          role="user"
          content="Test message"
        />
      );
      const bubble = screen.getByText('Test message').closest('div[data-message-bubble]');
      expect(bubble).toHaveClass('bg-secondary');
    });

    it('renders user message with border', () => {
      render(
        <ChatMessage
          role="user"
          content="Test message"
        />
      );
      const bubble = screen.getByText('Test message').closest('div[data-message-bubble]');
      expect(bubble).toHaveClass('border', 'border-border');
    });
  });

  describe('Agent Message', () => {
    it('renders agent message with correct content', () => {
      render(
        <ChatMessage
          role="assistant"
          content="The database contains 17,870 brain tissue samples."
        />
      );
      expect(screen.getByText(/The database contains/)).toBeInTheDocument();
    });

    it('renders agent message left-aligned', () => {
      render(
        <ChatMessage
          role="assistant"
          content="Test response"
        />
      );
      const container = screen.getByText('Test response').closest('div[data-message-container]');
      expect(container).toHaveClass('justify-start');
    });

    it('renders agent message without background', () => {
      render(
        <ChatMessage
          role="assistant"
          content="Test response"
        />
      );
      const bubble = screen.getByText('Test response').closest('div[data-message-bubble]');
      expect(bubble).not.toHaveClass('bg-secondary');
    });
  });
});

describe('ChatInput Component', () => {
  it('renders with placeholder text', () => {
    render(<ChatInput onSend={jest.fn()} />);
    expect(screen.getByPlaceholderText('Ask anything')).toBeInTheDocument();
  });

  it('renders send button', () => {
    render(<ChatInput onSend={jest.fn()} />);
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('calls onSend when send button is clicked with content', () => {
    const onSend = jest.fn();
    render(<ChatInput onSend={onSend} />);
    
    const input = screen.getByPlaceholderText('Ask anything');
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));
    
    expect(onSend).toHaveBeenCalledWith('Test message');
  });

  it('clears input after sending', () => {
    const onSend = jest.fn();
    render(<ChatInput onSend={onSend} />);
    
    const input = screen.getByPlaceholderText('Ask anything') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));
    
    expect(input.value).toBe('');
  });

  it('does not call onSend when input is empty', () => {
    const onSend = jest.fn();
    render(<ChatInput onSend={onSend} />);
    
    fireEvent.click(screen.getByRole('button', { name: /send/i }));
    
    expect(onSend).not.toHaveBeenCalled();
  });

  it('calls onSend when Enter is pressed', () => {
    const onSend = jest.fn();
    render(<ChatInput onSend={onSend} />);
    
    const input = screen.getByPlaceholderText('Ask anything');
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    
    expect(onSend).toHaveBeenCalledWith('Test message');
  });

  it('renders with pill shape (rounded-full)', () => {
    render(<ChatInput onSend={jest.fn()} />);
    const container = screen.getByPlaceholderText('Ask anything').closest('div[data-input-container]');
    expect(container).toHaveClass('rounded-full');
  });

  it('uses bg-input for background', () => {
    render(<ChatInput onSend={jest.fn()} />);
    const container = screen.getByPlaceholderText('Ask anything').closest('div[data-input-container]');
    expect(container).toHaveClass('bg-input');
  });

  it('can be disabled', () => {
    render(<ChatInput onSend={jest.fn()} disabled />);
    expect(screen.getByPlaceholderText('Ask anything')).toBeDisabled();
  });
});

describe('ChatHeader Component', () => {
  it('renders conversation title', () => {
    render(<ChatHeader title="Sample Inventory Count" />);
    expect(screen.getByText('Sample Inventory Count')).toBeInTheDocument();
  });

  it('renders dropdown indicator', () => {
    render(<ChatHeader title="Sample Inventory Count" />);
    // Should have a chevron/caret icon for dropdown
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
  });

  it('renders with border styling on button', () => {
    render(<ChatHeader title="Test Chat" />);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('border', 'border-border');
  });

  it('renders with bottom border on container', () => {
    render(<ChatHeader title="Test Chat" />);
    // The outer div contains the border-b class
    const button = screen.getByRole('button');
    const container = button.parentElement;
    expect(container).toHaveClass('border-b', 'border-border');
  });

  it('calls onDropdownClick when clicked', () => {
    const onDropdownClick = jest.fn();
    render(<ChatHeader title="Test Chat" onDropdownClick={onDropdownClick} />);
    
    fireEvent.click(screen.getByRole('button'));
    
    expect(onDropdownClick).toHaveBeenCalled();
  });
});

