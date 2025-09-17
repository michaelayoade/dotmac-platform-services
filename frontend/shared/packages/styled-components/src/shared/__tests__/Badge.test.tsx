/**
 * Badge component comprehensive tests
 * Testing badge variants, sizes, states, portal adaptation and composition patterns
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import React from 'react';

import { Badge } from '../Badge';

describe('Badge Component', () => {
  describe('Basic Rendering', () => {
    it('renders with default props', () => {
      render(<Badge data-testid='badge'>Default Badge</Badge>);

      const badge = screen.getByTestId('badge');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveTextContent('Default Badge');
      expect(badge).toHaveClass('inline-flex', 'items-center', 'rounded-full');
    });

    it('applies default variant and size classes', () => {
      render(<Badge data-testid='badge'>Badge</Badge>);

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveClass(
        'bg-primary',
        'text-primary-foreground',
        'px-2.5',
        'py-0.5',
        'text-xs'
      );
    });

    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>();

      render(
        <Badge ref={ref} data-testid='badge'>
          Badge
        </Badge>
      );

      expect(ref.current).toBeInstanceOf(HTMLDivElement);
      expect(ref.current).toBe(screen.getByTestId('badge'));
    });

    it('applies custom className', () => {
      render(
        <Badge className='custom-badge' data-testid='badge'>
          Custom
        </Badge>
      );

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('custom-badge');
      // Should also have default classes
      expect(badge).toHaveClass('inline-flex', 'items-center');
    });

    it('passes through HTML attributes', () => {
      render(
        <Badge
          data-testid='badge'
          role='alert'
          aria-live='polite'
          aria-label='Test badge'
          onClick={() => {
            // Event handler implementation pending
          }}
        >
          Badge
        </Badge>
      );

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveAttribute('role', 'status');
      expect(badge).toHaveAttribute('aria-label', 'Test badge');
    });
  });

  describe('Variant Props', () => {
    it('applies variant classes correctly', () => {
      const { rerender } = render(
        <Badge variant='default' data-testid='badge'>
          Default
        </Badge>
      );

      let badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('bg-primary', 'text-primary-foreground');

      rerender(
        <Badge variant='secondary' data-testid='badge'>
          Secondary
        </Badge>
      );
      badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('bg-secondary', 'text-secondary-foreground');

      rerender(
        <Badge variant='destructive' data-testid='badge'>
          Destructive
        </Badge>
      );
      badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('bg-destructive', 'text-destructive-foreground');

      rerender(
        <Badge variant='outline' data-testid='badge'>
          Outline
        </Badge>
      );
      badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('text-foreground');

      rerender(
        <Badge variant='success' data-testid='badge'>
          Success
        </Badge>
      );
      badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('bg-success', 'text-success-foreground');

      rerender(
        <Badge variant='warning' data-testid='badge'>
          Warning
        </Badge>
      );
      badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('bg-warning', 'text-warning-foreground');

      rerender(
        <Badge variant='info' data-testid='badge'>
          Info
        </Badge>
      );
      badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('bg-info', 'text-info-foreground');
    });

    it('handles hover states for variants', () => {
      const { rerender } = render(
        <Badge variant='default' data-testid='badge'>
          Default
        </Badge>
      );

      let badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('hover:bg-primary/80');

      rerender(
        <Badge variant='secondary' data-testid='badge'>
          Secondary
        </Badge>
      );
      badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('hover:bg-secondary/80');

      rerender(
        <Badge variant='destructive' data-testid='badge'>
          Destructive
        </Badge>
      );
      badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('hover:bg-destructive/80');
    });
  });

  describe('Size Props', () => {
    it('applies size classes correctly', () => {
      const { rerender } = render(
        <Badge size='sm' data-testid='badge'>
          Small
        </Badge>
      );

      let badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('text-xs', 'px-2', 'py-0.5');

      rerender(
        <Badge size='default' data-testid='badge'>
          Default
        </Badge>
      );
      badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('text-xs', 'px-2.5', 'py-0.5');

      rerender(
        <Badge size='lg' data-testid='badge'>
          Large
        </Badge>
      );
      badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('text-sm', 'px-3', 'py-1');
    });
  });

  describe('Icon Functionality', () => {
    it('renders with icon', () => {
      const TestIcon = () => <span data-testid='test-icon'>★</span>;

      render(
        <Badge icon={<TestIcon />} data-testid='badge'>
          With Icon
        </Badge>
      );

      expect(screen.getByTestId('test-icon')).toBeInTheDocument();
      expect(screen.getByText('With Icon')).toBeInTheDocument();

      const badge = screen.getByTestId('badge');
      const iconSpan = badge.querySelector('.mr-1.h-3.w-3.flex-shrink-0');
      expect(iconSpan).toBeInTheDocument();
    });

    it('does not render icon wrapper when no icon provided', () => {
      render(<Badge data-testid='badge'>No Icon</Badge>);

      const badge = screen.getByTestId('badge');
      const iconSpan = badge.querySelector('.mr-1.h-3.w-3.flex-shrink-0');
      expect(iconSpan).not.toBeInTheDocument();
    });

    it('renders icon-only badge', () => {
      const TestIcon = () => <span data-testid='star-icon'>★</span>;

      render(<Badge icon={<TestIcon />} data-testid='badge' aria-label='Starred' />);

      expect(screen.getByTestId('star-icon')).toBeInTheDocument();
      expect(screen.getByLabelText('Starred')).toBeInTheDocument();
    });

    it('handles complex icon content', () => {
      const ComplexIcon = () => (
        <svg aria-label='icon' data-testid='complex-icon' viewBox='0 0 24 24'>
          <title>Icon</title>
          <circle cx='12' cy='12' r='10' />
        </svg>
      );

      render(
        <Badge icon={<ComplexIcon />} data-testid='badge'>
          Complex Icon
        </Badge>
      );

      expect(screen.getByTestId('complex-icon')).toBeInTheDocument();
    });
  });

  describe('Pulse Animation', () => {
    it('applies pulse animation when pulse prop is true', () => {
      render(
        <Badge pulse data-testid='badge'>
          Pulsing Badge
        </Badge>
      );

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('animate-pulse');
    });

    it('does not apply pulse animation by default', () => {
      render(<Badge data-testid='badge'>Normal Badge</Badge>);

      const badge = screen.getByTestId('badge');
      expect(badge).not.toHaveClass('animate-pulse');
    });

    it('combines pulse with other styling', () => {
      render(
        <Badge pulse variant='success' size='lg' data-testid='badge'>
          Success Pulsing
        </Badge>
      );

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('animate-pulse', 'bg-success', 'text-sm');
    });
  });

  describe('Portal Detection and Adaptation', () => {
    beforeEach(() => {
      // Clear any existing portal classes
      document.body.className = '';
    });

    it('applies admin portal styling when body has admin-portal class', () => {
      document.body.classList.add('admin-portal');

      render(<Badge data-testid='badge'>Admin Badge</Badge>);

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('admin-badge');
    });

    it('applies customer portal styling when body has customer-portal class', () => {
      document.body.classList.add('customer-portal');

      render(<Badge data-testid='badge'>Customer Badge</Badge>);

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('customer-badge');
    });

    it('applies reseller portal styling when body has reseller-portal class', () => {
      document.body.classList.add('reseller-portal');

      render(<Badge data-testid='badge'>Reseller Badge</Badge>);

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('reseller-badge');
    });

    it('explicit portal prop overrides auto-detection', () => {
      document.body.classList.add('admin-portal');

      render(
        <Badge portal='customer' data-testid='badge'>
          Override Badge
        </Badge>
      );

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('customer-badge');
      expect(badge).not.toHaveClass('admin-badge');
    });

    it('does not apply portal classes when no portal detected', () => {
      render(<Badge data-testid='badge'>Neutral Badge</Badge>);

      const badge = screen.getByTestId('badge');
      expect(badge).not.toHaveClass('admin-badge');
      expect(badge).not.toHaveClass('customer-badge');
      expect(badge).not.toHaveClass('reseller-badge');
    });

    it('updates portal detection on portal prop change', () => {
      const { rerender } = render(
        <Badge portal='admin' data-testid='badge'>
          Badge
        </Badge>
      );

      let badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('admin-badge');

      rerender(
        <Badge portal='customer' data-testid='badge'>
          Badge
        </Badge>
      );
      badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('customer-badge');
      expect(badge).not.toHaveClass('admin-badge');
    });
  });

  describe('Interactive Badges', () => {
    it('handles click events when clickable', () => {
      const handleClick = jest.fn();

      render(
        <Badge onClick={handleClick} data-testid='badge' className='cursor-pointer'>
          Clickable Badge
        </Badge>
      );

      const badge = screen.getByTestId('badge');
      fireEvent.click(badge);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('supports keyboard navigation', () => {
      const handleKeyDown = jest.fn();

      render(
        <Badge onKeyDown={handleKeyDown} tabIndex={0} data-testid='badge'>
          Keyboard Badge
        </Badge>
      );

      const badge = screen.getByTestId('badge');
      badge.focus();
      fireEvent.keyDown(badge, { key: 'Enter' });

      expect(badge).toHaveFocus();
      expect(handleKeyDown).toHaveBeenCalledTimes(1);
    });

    it('supports focus ring styling', () => {
      render(<Badge data-testid='badge'>Focusable Badge</Badge>);

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('focus:ring-2', 'focus:ring-ring', 'focus:ring-offset-2');
    });
  });

  describe('Status Indicators', () => {
    it('works as status indicator', () => {
      render(
        <div>
          <span>Connection Status: </span>
          <Badge variant='success' data-testid='status-badge'>
            Connected
          </Badge>
        </div>
      );

      const badge = screen.getByTestId('status-badge');
      expect(badge).toHaveTextContent('Connected');
      expect(badge).toHaveClass('bg-success');
    });

    it('works as count indicator', () => {
      render(
        <div>
          <span>Notifications </span>
          <Badge variant='destructive' data-testid='count-badge'>
            5
          </Badge>
        </div>
      );

      const badge = screen.getByTestId('count-badge');
      expect(badge).toHaveTextContent('5');
      expect(badge).toHaveClass('bg-destructive');
    });

    it('works as live indicator with pulse', () => {
      render(
        <Badge variant='success' pulse data-testid='live-badge'>
          Live
        </Badge>
      );

      const badge = screen.getByTestId('live-badge');
      expect(badge).toHaveClass('bg-success', 'animate-pulse');
      expect(badge).toHaveTextContent('Live');
    });
  });

  describe('Content Handling', () => {
    it('handles empty content', () => {
      render(<Badge data-testid='badge' />);

      const badge = screen.getByTestId('badge');
      expect(badge).toBeInTheDocument();
      expect(badge).toBeEmptyDOMElement();
    });

    it('handles numeric content', () => {
      render(<Badge data-testid='badge'>{42}</Badge>);

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveTextContent('42');
    });

    it('handles boolean content', () => {
      render(<Badge data-testid='badge'>{true ? 'Active' : 'Inactive'}</Badge>);

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveTextContent('Active');
    });

    it('handles complex content', () => {
      render(
        <Badge data-testid='badge'>
          <div className='flex items-center gap-1'>
            <span>●</span>
            <span>Live</span>
          </div>
        </Badge>
      );

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveTextContent('●Live');
    });

    it('renders with icon and complex content', () => {
      const Icon = () => <span data-testid='icon'>★</span>;

      render(
        <Badge icon={<Icon />} data-testid='badge'>
          <div>
            <span>Featured</span>
            <span className='ml-1 text-xs'>NEW</span>
          </div>
        </Badge>
      );

      expect(screen.getByTestId('icon')).toBeInTheDocument();
      expect(screen.getByText('Featured')).toBeInTheDocument();
      expect(screen.getByText('NEW')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should be accessible', async () => {
      const { container } = render(<Badge>Accessible Badge</Badge>);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('supports aria-label for screen readers', () => {
      render(
        <Badge aria-label='5 unread notifications' data-testid='badge'>
          5
        </Badge>
      );

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveAttribute('aria-label', '5 unread notifications');
    });

    it('supports role attribute for semantic meaning', () => {
      render(
        <Badge role='alert' aria-live='polite' data-testid='badge'>
          Online
        </Badge>
      );

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveAttribute('role', 'status');
    });

    it('is announced by screen readers when used as status', () => {
      render(
        <Badge role='alert' aria-live='polite' aria-live='polite' data-testid='badge'>
          Processing...
        </Badge>
      );

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveAttribute('aria-live', 'polite');
      expect(badge).toHaveAttribute('role', 'status');
    });

    it('supports high contrast mode', () => {
      render(
        <Badge variant='outline' data-testid='badge'>
          High Contrast
        </Badge>
      );

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('border', 'text-foreground');
    });
  });

  describe('Variant and Size Combinations', () => {
    const variants = [
      'default',
      'secondary',
      'destructive',
      'outline',
      'success',
      'warning',
      'info',
    ] as const;
    const sizes = ['sm', 'default', 'lg'] as const;

    variants.forEach((variant) => {
      it(`renders ${variant} variant correctly`, () => {
        render(
          <Badge variant={variant} data-testid={`badge-${variant}`}>
            {variant} badge
          </Badge>
        );

        expect(screen.getByTestId(`badge-${variant}`)).toBeInTheDocument();
        expect(screen.getByText(`${variant} badge`)).toBeInTheDocument();
      });
    });

    sizes.forEach((size) => {
      it(`renders ${size} size correctly`, () => {
        render(
          <Badge size={size} data-testid={`badge-${size}`}>
            {size} badge
          </Badge>
        );

        expect(screen.getByTestId(`badge-${size}`)).toBeInTheDocument();
        expect(screen.getByText(`${size} badge`)).toBeInTheDocument();
      });
    });

    it('handles all variant and size combinations', () => {
      variants.forEach((variant) => {
        sizes.forEach((size) => {
          const { unmount } = render(
            <Badge variant={variant} size={size} data-testid={`badge-${variant}-${size}`}>
              {variant} {size}
            </Badge>
          );

          const badge = screen.getByTestId(`badge-${variant}-${size}`);
          expect(badge).toBeInTheDocument();
          expect(badge).toHaveTextContent(`${variant} ${size}`);

          unmount();
        });
      });
    });

    it('combines variants with special features', () => {
      render(
        <Badge
          variant='success'
          size='lg'
          pulse
          icon={<span data-testid='icon'>✓</span>}
          portal='admin'
          data-testid='feature-badge'
        >
          Success
        </Badge>
      );

      const badge = screen.getByTestId('feature-badge');
      expect(badge).toHaveClass('bg-success', 'text-sm', 'animate-pulse', 'admin-badge');
      expect(screen.getByTestId('icon')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles very long text content', () => {
      const longText = 'Very long badge content that might wrap or overflow';

      render(<Badge data-testid='badge'>{longText}</Badge>);

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveTextContent(longText);
    });

    it('handles special characters in content', () => {
      const specialContent = 'Content with special chars: <>&"\'`{}[]()';

      render(<Badge data-testid='badge'>{specialContent}</Badge>);

      const badge = screen.getByTestId('badge');
      expect(badge).toHaveTextContent(specialContent);
    });

    it('handles null and undefined children gracefully', () => {
      const { rerender } = render(<Badge data-testid='badge'>{null}</Badge>);

      let badge = screen.getByTestId('badge');
      expect(badge).toBeInTheDocument();

      rerender(<Badge data-testid='badge'>{undefined}</Badge>);
      badge = screen.getByTestId('badge');
      expect(badge).toBeInTheDocument();
    });

    it('handles dynamic content updates', () => {
      const { rerender } = render(<Badge data-testid='badge'>Initial Content</Badge>);

      expect(screen.getByText('Initial Content')).toBeInTheDocument();

      rerender(<Badge data-testid='badge'>Updated Content</Badge>);
      expect(screen.getByText('Updated Content')).toBeInTheDocument();
      expect(screen.queryByText('Initial Content')).not.toBeInTheDocument();
    });

    it('handles rapid portal changes', () => {
      const { rerender } = render(
        <Badge portal='admin' data-testid='badge'>
          Badge
        </Badge>
      );

      let badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('admin-badge');

      rerender(
        <Badge portal='customer' data-testid='badge'>
          Badge
        </Badge>
      );
      badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('customer-badge');

      rerender(
        <Badge portal='reseller' data-testid='badge'>
          Badge
        </Badge>
      );
      badge = screen.getByTestId('badge');
      expect(badge).toHaveClass('reseller-badge');

      rerender(<Badge data-testid='badge'>Badge</Badge>);
      badge = screen.getByTestId('badge');
      expect(badge).not.toHaveClass('admin-badge', 'customer-badge', 'reseller-badge');
    });
  });

  describe('Performance', () => {
    it('renders efficiently with complex props', () => {
      const startTime = performance.now();

      render(
        <div>
          {Array.from({ length: 100 }, (_, i) => (
            <Badge
              key={`item-${i}`}
              variant={i % 2 === 0 ? 'default' : 'secondary'}
              size={i % 3 === 0 ? 'sm' : 'default'}
              pulse={i % 5 === 0}
              icon={i % 4 === 0 ? <span>★</span> : undefined}
            >
              Badge {i}
            </Badge>
          ))}
        </div>
      );

      const endTime = performance.now();

      // Should render within reasonable time
      expect(endTime - startTime).toBeLessThan(200);

      expect(screen.getAllByText(/Badge \d+/)).toHaveLength(100);
    });
  });

  describe('Composition Patterns', () => {
    it('works in lists and grids', () => {
      render(
        <div data-testid='badge-list'>
          <Badge variant='default'>Item 1</Badge>
          <Badge variant='secondary'>Item 2</Badge>
          <Badge variant='success'>Item 3</Badge>
        </div>
      );

      const list = screen.getByTestId('badge-list');
      expect(list.children).toHaveLength(3);
      expect(screen.getByText('Item 1')).toBeInTheDocument();
      expect(screen.getByText('Item 2')).toBeInTheDocument();
      expect(screen.getByText('Item 3')).toBeInTheDocument();
    });

    it('composes with other components', () => {
      render(
        <div className='flex items-center gap-2'>
          <span>Status:</span>
          <Badge variant='success' pulse>
            Online
          </Badge>
          <span>Count:</span>
          <Badge variant='destructive'>5</Badge>
        </div>
      );

      expect(screen.getByText('Status:')).toBeInTheDocument();
      expect(screen.getByText('Online')).toBeInTheDocument();
      expect(screen.getByText('Count:')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
    });
  });
});
