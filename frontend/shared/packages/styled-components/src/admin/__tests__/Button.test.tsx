/**
 * AdminButton component comprehensive tests
 * Testing admin-specific button functionality and variants
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import React from 'react';

import { AdminButton } from '../Button';

describe('AdminButton Component', () => {
  describe('Basic Rendering', () => {
    it('renders as button by default', () => {
      render(<AdminButton>Click me</AdminButton>);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Click me');
    });

    it('renders as child component when asChild is true', () => {
      render(
        <AdminButton asChild>
          <a href='/test'>Link button</a>
        </AdminButton>
      );

      const link = screen.getByRole('link');
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', '/test');
      expect(link).toHaveTextContent('Link button');
    });

    it('applies custom className', () => {
      render(<AdminButton className='custom-btn'>Button</AdminButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('custom-btn');
    });
  });

  describe('Variants', () => {
    it('renders default variant', () => {
      render(<AdminButton variant='default'>Default</AdminButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-admin-primary');
    });

    it('renders destructive variant', () => {
      render(<AdminButton variant='destructive'>Delete</AdminButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-admin-destructive');
    });

    it('renders outline variant', () => {
      render(<AdminButton variant='outline'>Outline</AdminButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('border-admin-border');
    });

    it('renders secondary variant', () => {
      render(<AdminButton variant='secondary'>Secondary</AdminButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-admin-secondary');
    });

    it('renders ghost variant', () => {
      render(<AdminButton variant='ghost'>Ghost</AdminButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('hover:bg-admin-accent');
    });

    it('renders link variant', () => {
      render(<AdminButton variant='link'>Link</AdminButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('text-admin-primary');
    });
  });

  describe('Sizes', () => {
    it('renders default size', () => {
      render(<AdminButton size='default'>Default</AdminButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-8', 'px-3', 'py-1.5');
    });

    it('renders small size', () => {
      render(<AdminButton size='sm'>Small</AdminButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-7', 'px-2');
    });

    it('renders large size', () => {
      render(<AdminButton size='lg'>Large</AdminButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-9', 'px-6');
    });

    it('renders icon size', () => {
      render(<AdminButton size='icon'>⚙</AdminButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-8', 'w-8');
    });
  });

  describe('Icons', () => {
    it('renders with left icon', () => {
      const LeftIcon = () => <span data-testid='left-icon'>←</span>;

      render(<AdminButton leftIcon={<LeftIcon />}>With Left Icon</AdminButton>);

      expect(screen.getByTestId('left-icon')).toBeInTheDocument();
      expect(screen.getByText('With Left Icon')).toBeInTheDocument();
    });

    it('renders with right icon', () => {
      const RightIcon = () => <span data-testid='right-icon'>→</span>;

      render(<AdminButton rightIcon={<RightIcon />}>With Right Icon</AdminButton>);

      expect(screen.getByTestId('right-icon')).toBeInTheDocument();
      expect(screen.getByText('With Right Icon')).toBeInTheDocument();
    });

    it('renders with both icons', () => {
      const LeftIcon = () => <span data-testid='left-icon'>←</span>;
      const RightIcon = () => <span data-testid='right-icon'>→</span>;

      render(
        <AdminButton leftIcon={<LeftIcon />} rightIcon={<RightIcon />}>
          Both Icons
        </AdminButton>
      );

      expect(screen.getByTestId('left-icon')).toBeInTheDocument();
      expect(screen.getByTestId('right-icon')).toBeInTheDocument();
      expect(screen.getByText('Both Icons')).toBeInTheDocument();
    });

    it('renders icon only button', () => {
      const Icon = () => <span data-testid='icon'>⚙</span>;

      render(
        <AdminButton size='icon' aria-label='Settings'>
          <Icon />
        </AdminButton>
      );

      expect(screen.getByTestId('icon')).toBeInTheDocument();
      expect(screen.getByLabelText('Settings')).toBeInTheDocument();
    });
  });

  describe('States', () => {
    it('handles disabled state', () => {
      render(<AdminButton disabled>Disabled</AdminButton>);

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
      expect(button).toHaveClass('disabled:pointer-events-none');
    });

    it('handles loading state', () => {
      render(<AdminButton loading>Loading</AdminButton>);

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });

    it('shows loading spinner when loading', () => {
      render(<AdminButton loading>Submit</AdminButton>);

      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
      expect(screen.getByText('Submit')).toBeInTheDocument();
    });

    it('hides icons when loading', () => {
      const LeftIcon = () => <span data-testid='left-icon'>←</span>;

      render(
        <AdminButton loading leftIcon={<LeftIcon />}>
          Loading Button
        </AdminButton>
      );

      expect(screen.queryByTestId('left-icon')).not.toBeInTheDocument();
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('handles click events', () => {
      const handleClick = jest.fn();

      render(<AdminButton onClick={handleClick}>Click me</AdminButton>);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('does not fire click when disabled', () => {
      const handleClick = jest.fn();

      render(
        <AdminButton onClick={handleClick} disabled>
          Disabled
        </AdminButton>
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(handleClick).not.toHaveBeenCalled();
    });

    it('does not fire click when loading', () => {
      const handleClick = jest.fn();

      render(
        <AdminButton onClick={handleClick} loading>
          Loading
        </AdminButton>
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(handleClick).not.toHaveBeenCalled();
    });

    it('handles keyboard events', () => {
      const handleKeyDown = jest.fn();

      render(<AdminButton onKeyDown={handleKeyDown}>Button</AdminButton>);

      const button = screen.getByRole('button');
      fireEvent.keyDown(button, { key: 'Enter' });

      expect(handleKeyDown).toHaveBeenCalledTimes(1);
    });

    it('handles form submission', () => {
      const handleSubmit = jest.fn((e) => e.preventDefault());

      render(
        <form onSubmit={handleSubmit}>
          <AdminButton type='submit'>Submit</AdminButton>
        </form>
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(handleSubmit).toHaveBeenCalledTimes(1);
    });
  });

  describe('Ref Forwarding', () => {
    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLButtonElement>();

      render(<AdminButton ref={ref}>Button</AdminButton>);

      expect(ref.current).toBeInstanceOf(HTMLButtonElement);
      expect(ref.current?.textContent).toBe('Button');
    });

    it('forwards ref to child component', () => {
      const ref = React.createRef<HTMLAnchorElement>();

      render(
        <AdminButton asChild>
          <a ref={ref} href='/test'>
            Link
          </a>
        </AdminButton>
      );

      expect(ref.current).toBeInstanceOf(HTMLAnchorElement);
      expect(ref.current?.getAttribute('href')).toBe('/test');
    });
  });

  describe('Accessibility', () => {
    it('should be accessible', async () => {
      const { container } = render(<AdminButton>Accessible Button</AdminButton>);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should be accessible when disabled', async () => {
      const { container } = render(<AdminButton disabled>Disabled Button</AdminButton>);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should be accessible when loading', async () => {
      const { container } = render(<AdminButton loading>Loading Button</AdminButton>);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('provides proper ARIA attributes for loading state', () => {
      render(<AdminButton loading>Loading</AdminButton>);

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
      expect(screen.getByTestId('loading-spinner')).toHaveAttribute('aria-label', 'Loading');
    });

    it('supports custom ARIA attributes', () => {
      render(
        <AdminButton aria-label='Custom label' aria-describedby='description'>
          Button
        </AdminButton>
      );

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', 'Custom label');
      expect(button).toHaveAttribute('aria-describedby', 'description');
    });
  });

  describe('Edge Cases', () => {
    it('handles empty children', () => {
      render(<AdminButton />);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('handles null children', () => {
      render(<AdminButton>{null}</AdminButton>);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('handles numeric children', () => {
      render(<AdminButton>{42}</AdminButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveTextContent('42');
    });

    it('handles mixed content', () => {
      render(
        <AdminButton>
          Text <span>and span</span>
        </AdminButton>
      );

      const button = screen.getByRole('button');
      expect(button).toHaveTextContent('Text and span');
    });
  });

  describe('Variant Combinations', () => {
    const variants = ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'] as const;
    const sizes = ['default', 'sm', 'lg', 'icon'] as const;

    variants.forEach((variant) => {
      it(`renders ${variant} variant correctly`, () => {
        render(<AdminButton variant={variant}>{variant}</AdminButton>);

        const button = screen.getByRole('button');
        expect(button).toBeInTheDocument();
      });
    });

    sizes.forEach((size) => {
      it(`renders ${size} size correctly`, () => {
        render(<AdminButton size={size}>{size}</AdminButton>);

        const button = screen.getByRole('button');
        expect(button).toBeInTheDocument();
      });
    });

    it('handles all variant and size combinations', () => {
      variants.forEach((variant) => {
        sizes.forEach((size) => {
          const { unmount } = render(
            <AdminButton variant={variant} size={size}>
              {variant} {size}
            </AdminButton>
          );

          const button = screen.getByRole('button');
          expect(button).toBeInTheDocument();

          unmount();
        });
      });
    });
  });

  describe('Performance', () => {
    it('renders efficiently with many props', () => {
      const startTime = performance.now();

      render(
        <AdminButton
          variant='default'
          size='lg'
          disabled={false}
          loading={false}
          leftIcon={<span>←</span>}
          rightIcon={<span>→</span>}
          className='many-props'
          onClick={() => {
            // Event handler implementation pending
          }}
          onKeyDown={() => {
            // Event handler implementation pending
          }}
          aria-label='Performance test'
          data-testid='perf-button'
        >
          Performance Test Button
        </AdminButton>
      );

      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(10);
      expect(screen.getByTestId('perf-button')).toBeInTheDocument();
    });
  });
});
