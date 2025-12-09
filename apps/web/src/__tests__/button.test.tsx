/**
 * shadcn Button Component Tests
 * 
 * Verifies that the Button component renders correctly with our theme.
 */

import { render, screen } from '@testing-library/react';
import { Button } from '@/components/ui/button';

describe('Button Component', () => {
  test('renders default button', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button')).toHaveTextContent('Click me');
  });

  test('renders all button variants', () => {
    const { rerender } = render(<Button variant="default">Default</Button>);
    expect(screen.getByRole('button')).toBeInTheDocument();

    rerender(<Button variant="destructive">Destructive</Button>);
    expect(screen.getByRole('button')).toHaveTextContent('Destructive');

    rerender(<Button variant="outline">Outline</Button>);
    expect(screen.getByRole('button')).toHaveTextContent('Outline');

    rerender(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByRole('button')).toHaveTextContent('Secondary');

    rerender(<Button variant="ghost">Ghost</Button>);
    expect(screen.getByRole('button')).toHaveTextContent('Ghost');

    rerender(<Button variant="link">Link</Button>);
    expect(screen.getByRole('button')).toHaveTextContent('Link');
  });

  test('renders all button sizes', () => {
    const { rerender } = render(<Button size="default">Default</Button>);
    expect(screen.getByRole('button')).toBeInTheDocument();

    rerender(<Button size="sm">Small</Button>);
    expect(screen.getByRole('button')).toHaveTextContent('Small');

    rerender(<Button size="lg">Large</Button>);
    expect(screen.getByRole('button')).toHaveTextContent('Large');

    rerender(<Button size="icon">Icon</Button>);
    expect(screen.getByRole('button')).toHaveTextContent('Icon');
  });

  test('applies custom className', () => {
    render(<Button className="custom-class">Custom</Button>);
    expect(screen.getByRole('button')).toHaveClass('custom-class');
  });

  test('renders as child component when asChild is true', () => {
    render(
      <Button asChild>
        <a href="/test">Link Button</a>
      </Button>
    );
    expect(screen.getByRole('link')).toHaveTextContent('Link Button');
  });

  test('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});

