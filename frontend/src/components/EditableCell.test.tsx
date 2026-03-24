import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { EditableCell } from './EditableCell';

describe('EditableCell', () => {
  it('renders display text when not editing', () => {
    render(<EditableCell value="ABC-123" onSave={vi.fn()} />);
    expect(screen.getByText('ABC-123')).toBeInTheDocument();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
  });

  it('clicking cell switches to input with value pre-filled', () => {
    render(<EditableCell value="ABC-123" onSave={vi.fn()} />);
    fireEvent.click(screen.getByText('ABC-123'));
    const input = screen.getByRole('textbox');
    expect(input).toBeInTheDocument();
    expect(input).toHaveValue('ABC-123');
  });

  it('Not found value renders with muted italic styling', () => {
    const { container } = render(<EditableCell value="Not found" onSave={vi.fn()} />);
    const span = container.querySelector('span');
    expect(span).toHaveClass('italic');
    expect(span).toHaveClass('text-muted-foreground');
  });

  it('clicking Not found cell opens empty input', () => {
    render(<EditableCell value="Not found" onSave={vi.fn()} />);
    fireEvent.click(screen.getByText('Not found'));
    expect(screen.getByRole('textbox')).toHaveValue('');
  });

  it('blur calls onSave when value changed', () => {
    const onSave = vi.fn();
    render(<EditableCell value="old" onSave={onSave} />);
    fireEvent.click(screen.getByText('old'));
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'new' } });
    fireEvent.blur(input);
    expect(onSave).toHaveBeenCalledWith('new');
  });

  it('blur does NOT call onSave when draft empty and original was Not found', () => {
    const onSave = vi.fn();
    render(<EditableCell value="Not found" onSave={onSave} />);
    fireEvent.click(screen.getByText('Not found'));
    fireEvent.blur(screen.getByRole('textbox'));
    expect(onSave).not.toHaveBeenCalled();
  });

  it('Enter key calls onSave when value changed', () => {
    const onSave = vi.fn();
    render(<EditableCell value="old" onSave={onSave} />);
    fireEvent.click(screen.getByText('old'));
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'new' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(onSave).toHaveBeenCalledWith('new');
  });

  it('Escape reverts to original value without calling onSave', () => {
    const onSave = vi.fn();
    render(<EditableCell value="original" onSave={onSave} />);
    fireEvent.click(screen.getByText('original'));
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'changed' } });
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(onSave).not.toHaveBeenCalled();
    expect(screen.getByText('original')).toBeInTheDocument();
  });
});
