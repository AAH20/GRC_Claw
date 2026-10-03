import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '../../frontend/components/Button';
import { Modal } from '../../frontend/components/Modal';
import { LoadingSpinner } from '../../frontend/components/LoadingSpinner';
import { ErrorBoundary } from '../../frontend/components/ErrorBoundary';

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick handler', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('shows loading state', () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});

describe('Modal', () => {
  it('renders when open', () => {
    render(
      <Modal isOpen={true} onClose={jest.fn()}>
        <div>Modal content</div>
      </Modal>
    );
    expect(screen.getByText('Modal content')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(
      <Modal isOpen={false} onClose={jest.fn()}>
        <div>Modal content</div>
      </Modal>
    );
    expect(screen.queryByText('Modal content')).not.toBeInTheDocument();
  });
});

describe('LoadingSpinner', () => {
  it('renders spinner', () => {
    render(<LoadingSpinner />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});

describe('ErrorBoundary', () => {
  it('renders children when no error', () => {
    render(
      <ErrorBoundary>
        <div>Child content</div>
      </ErrorBoundary>
    );
    expect(screen.getByText('Child content')).toBeInTheDocument();
  });

  it('renders error message on error', () => {
    const ThrowError = () => {
      throw new Error('Test error');
    };
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );
    expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
  });
});
