/**
 * AdminCard component tests
 * Testing admin-specific card functionality and admin styling
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import React from 'react';

import {
  AdminCard,
  AdminCardContent,
  AdminCardDescription,
  AdminCardFooter,
  AdminCardHeader,
  AdminCardTitle,
} from '../Card';

// Mock the primitive components since they don't exist yet
jest.mock('@dotmac/primitives', () => ({
  card: React.forwardRef(({ children, className, ...props }: unknown, ref: unknown) => (
    <div ref={ref} className={className} {...props}>
      {children}
    </div>
  )),
  CardHeader: React.forwardRef(({ children, className, ...props }: unknown, ref: unknown) => (
    <div ref={ref} className={className} {...props}>
      {children}
    </div>
  )),
  CardContent: React.forwardRef(({ children, className, ...props }: unknown, ref: unknown) => (
    <div ref={ref} className={className} {...props}>
      {children}
    </div>
  )),
  CardFooter: React.forwardRef(({ children, className, ...props }: unknown, ref: unknown) => (
    <div ref={ref} className={className} {...props}>
      {children}
    </div>
  )),
}));

describe('AdminCard Component', () => {
  describe('AdminCard', () => {
    it('renders basic card', () => {
      render(
        <AdminCard data-testid='card'>
          <div>Basic card content</div>
        </AdminCard>
      );

      const card = screen.getByTestId('card');
      expect(card).toBeInTheDocument();
      expect(card).toHaveTextContent('Basic card content');
    });

    it('applies default styling classes', () => {
      render(<AdminCard data-testid='card'>Card content</AdminCard>);

      const card = screen.getByTestId('card');
      expect(card).toHaveClass(
        'rounded-lg',
        'border',
        'border-admin-border',
        'bg-admin-card',
        'text-admin-card-foreground',
        'shadow-sm'
      );
    });

    it('applies custom className', () => {
      render(
        <AdminCard className='custom-class' data-testid='card'>
          Card content
        </AdminCard>
      );

      const card = screen.getByTestId('card');
      expect(card).toHaveClass('custom-class');
    });

    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>();

      render(
        <AdminCard ref={ref} data-testid='card'>
          Card content
        </AdminCard>
      );

      expect(ref.current).toBeInstanceOf(HTMLDivElement);
      expect(ref.current).toBe(screen.getByTestId('card'));
    });

    it('handles variant prop', () => {
      render(
        <AdminCard variant='danger' data-testid='card'>
          Danger card
        </AdminCard>
      );

      const card = screen.getByTestId('card');
      expect(card).toHaveClass('border-admin-destructive/50', 'bg-admin-destructive/5');
    });

    it('handles interactive prop', () => {
      render(
        <AdminCard interactive data-testid='card'>
          Interactive card
        </AdminCard>
      );

      const card = screen.getByTestId('card');
      expect(card).toHaveClass('cursor-pointer', 'hover:bg-admin-accent/5', 'transition-colors');
    });

    it('handles compact prop', () => {
      render(
        <AdminCard compact data-testid='card'>
          Compact card
        </AdminCard>
      );

      const card = screen.getByTestId('card');
      expect(card).toHaveClass('p-3');
    });

    it('handles various HTML attributes', () => {
      render(
        <AdminCard
          data-testid='card'
          role='button'
          aria-label='Test card'
          onClick={() => {
            // Event handler implementation pending
          }}
        >
          Card content
        </AdminCard>
      );

      const card = screen.getByTestId('card');
      expect(card).toHaveAttribute('role', 'button');
      expect(card).toHaveAttribute('aria-label', 'Test card');
    });
  });

  describe('AdminCardHeader', () => {
    it('renders card header', () => {
      render(
        <AdminCardHeader data-testid='header'>
          <div>Header content</div>
        </AdminCardHeader>
      );

      const header = screen.getByTestId('header');
      expect(header).toBeInTheDocument();
      expect(header).toHaveTextContent('Header content');
    });

    it('applies header styling classes', () => {
      render(<AdminCardHeader data-testid='header'>Admin header</AdminCardHeader>);

      const header = screen.getByTestId('header');
      expect(header).toHaveClass(
        'flex',
        'flex-row',
        'items-center',
        'justify-between',
        'space-y-0',
        'p-4'
      );
    });

    it('renders with actions', () => {
      render(
        <AdminCardHeader
          actions={
            <button type='button' data-testid='action-btn'>
              Action
            </button>
          }
          data-testid='header'
        >
          Header with actions
        </AdminCardHeader>
      );

      const header = screen.getByTestId('header');
      const actionBtn = screen.getByTestId('action-btn');
      expect(header).toBeInTheDocument();
      expect(actionBtn).toBeInTheDocument();
      expect(actionBtn).toHaveTextContent('Action');
    });

    it('handles compact prop', () => {
      render(
        <AdminCardHeader compact data-testid='header'>
          Compact header
        </AdminCardHeader>
      );

      const header = screen.getByTestId('header');
      expect(header).toHaveClass('p-3');
    });
  });

  describe('AdminCardTitle', () => {
    it('renders card title', () => {
      render(<AdminCardTitle data-testid='title'>Card Title</AdminCardTitle>);

      const title = screen.getByTestId('title');
      expect(title).toBeInTheDocument();
      expect(title).toHaveTextContent('Card Title');
    });

    it('applies title styling classes', () => {
      render(<AdminCardTitle data-testid='title'>Title</AdminCardTitle>);

      const title = screen.getByTestId('title');
      expect(title).toHaveClass(
        'font-semibold',
        'tracking-tight',
        'text-admin-foreground',
        'text-base'
      );
    });

    it('renders as heading by default', () => {
      render(<AdminCardTitle>Title</AdminCardTitle>);

      const title = screen.getByRole('heading');
      expect(title.tagName).toBe('H3');
    });

    it('handles size prop', () => {
      render(
        <AdminCardTitle size='lg' data-testid='title'>
          Large Title
        </AdminCardTitle>
      );

      const title = screen.getByTestId('title');
      expect(title).toHaveClass('text-lg');
    });
  });

  describe('AdminCardDescription', () => {
    it('renders card description', () => {
      render(
        <AdminCardDescription data-testid='description'>Card description text</AdminCardDescription>
      );

      const description = screen.getByTestId('description');
      expect(description).toBeInTheDocument();
      expect(description).toHaveTextContent('Card description text');
    });

    it('applies description styling classes', () => {
      render(
        <AdminCardDescription data-testid='description'>Card description</AdminCardDescription>
      );

      const description = screen.getByTestId('description');
      expect(description).toHaveClass('text-xs', 'text-admin-muted-foreground');
    });

    it('renders as paragraph by default', () => {
      render(<AdminCardDescription>Description</AdminCardDescription>);

      const description = screen.getByText('Description');
      expect(description.tagName).toBe('P');
    });
  });

  describe('AdminCardContent', () => {
    it('renders card content', () => {
      render(
        <AdminCardContent data-testid='content'>
          <div>Content goes here</div>
        </AdminCardContent>
      );

      const content = screen.getByTestId('content');
      expect(content).toBeInTheDocument();
      expect(content).toHaveTextContent('Content goes here');
    });

    it('applies content styling classes', () => {
      render(<AdminCardContent data-testid='content'>Card content</AdminCardContent>);

      const content = screen.getByTestId('content');
      expect(content).toHaveClass('p-4', 'pt-0');
    });

    it('handles compact prop', () => {
      render(
        <AdminCardContent compact data-testid='content'>
          Compact content
        </AdminCardContent>
      );

      const content = screen.getByTestId('content');
      expect(content).toHaveClass('p-3', 'pt-0');
    });
  });

  describe('AdminCardFooter', () => {
    it('renders card footer', () => {
      render(
        <AdminCardFooter data-testid='footer'>
          <button type='button'>Footer button</button>
        </AdminCardFooter>
      );

      const footer = screen.getByTestId('footer');
      expect(footer).toBeInTheDocument();
      expect(footer).toHaveTextContent('Footer button');
    });

    it('applies footer styling classes', () => {
      render(<AdminCardFooter data-testid='footer'>Card footer</AdminCardFooter>);

      const footer = screen.getByTestId('footer');
      expect(footer).toHaveClass(
        'flex',
        'items-center',
        'border-t',
        'border-admin-border/50',
        'bg-admin-muted/20',
        'p-4',
        'pt-3'
      );
    });

    it('handles compact prop', () => {
      render(
        <AdminCardFooter compact data-testid='footer'>
          Compact footer
        </AdminCardFooter>
      );

      const footer = screen.getByTestId('footer');
      expect(footer).toHaveClass('p-3', 'pt-2');
    });
  });

  describe('Card Composition', () => {
    it('renders complete card with all components', () => {
      render(
        <AdminCard data-testid='complete-card'>
          <AdminCardHeader>
            <AdminCardTitle>Complete Card</AdminCardTitle>
            <AdminCardDescription>This is a complete card example</AdminCardDescription>
          </AdminCardHeader>
          <AdminCardContent>
            <p>This is the main content of the card.</p>
          </AdminCardContent>
          <AdminCardFooter>
            <button type='button'>Action Button</button>
          </AdminCardFooter>
        </AdminCard>
      );

      expect(screen.getByTestId('complete-card')).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Complete Card' })).toBeInTheDocument();
      expect(screen.getByText('This is a complete card example')).toBeInTheDocument();
      expect(screen.getByText('This is the main content of the card.')).toBeInTheDocument();
      expect(screen.getByText('Action Button')).toBeInTheDocument();
    });

    it('renders card with only header and content', () => {
      render(
        <AdminCard>
          <AdminCardHeader>
            <AdminCardTitle>Simple Card</AdminCardTitle>
          </AdminCardHeader>
          <AdminCardContent>
            <p>Simple card content</p>
          </AdminCardContent>
        </AdminCard>
      );

      expect(screen.getByRole('heading', { name: 'Simple Card' })).toBeInTheDocument();
      expect(screen.getByText('Simple card content')).toBeInTheDocument();
    });

    it('renders card with custom structure', () => {
      render(
        <AdminCard variant='elevated' interactive>
          <AdminCardHeader compact actions={<span>👤</span>}>
            <AdminCardTitle size='sm'>Custom Card</AdminCardTitle>
          </AdminCardHeader>
          <AdminCardContent compact>
            <div>Custom content layout</div>
          </AdminCardContent>
        </AdminCard>
      );

      expect(screen.getByText('👤')).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Custom Card' })).toBeInTheDocument();
      expect(screen.getByText('Custom content layout')).toBeInTheDocument();
    });
  });

  describe('Interactive Cards', () => {
    it('handles clickable card', () => {
      const handleClick = jest.fn();

      render(
        <AdminCard interactive onClick={handleClick} data-testid='clickable-card'>
          <AdminCardContent>Clickable card</AdminCardContent>
        </AdminCard>
      );

      const card = screen.getByTestId('clickable-card');
      fireEvent.click(card);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('handles keyboard navigation', () => {
      const handleKeyDown = jest.fn();

      render(
        <AdminCard interactive tabIndex={0} onKeyDown={handleKeyDown} data-testid='keyboard-card'>
          <AdminCardContent>Keyboard navigable card</AdminCardContent>
        </AdminCard>
      );

      const card = screen.getByTestId('keyboard-card');
      card.focus();
      fireEvent.keyDown(card, { key: 'Enter' });

      expect(card).toHaveFocus();
      expect(handleKeyDown).toHaveBeenCalledTimes(1);
    });

    it('handles hover effects', () => {
      render(
        <AdminCard interactive data-testid='hover-card'>
          <AdminCardContent>Hoverable card</AdminCardContent>
        </AdminCard>
      );

      const card = screen.getByTestId('hover-card');
      expect(card).toHaveClass('hover:bg-admin-accent/5');
    });
  });

  describe('Accessibility', () => {
    it('should be accessible', async () => {
      const { container } = render(
        <AdminCard>
          <AdminCardHeader>
            <AdminCardTitle>Accessible Card</AdminCardTitle>
            <AdminCardDescription>This card is fully accessible</AdminCardDescription>
          </AdminCardHeader>
          <AdminCardContent>
            <p>Accessible content for all users</p>
          </AdminCardContent>
          <AdminCardFooter>
            <button type='button'>Accessible Action</button>
          </AdminCardFooter>
        </AdminCard>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('supports ARIA landmarks', () => {
      render(
        <AdminCard role='region' aria-labelledby='card-title'>
          <AdminCardHeader>
            <AdminCardTitle id='card-title'>Admin Dashboard</AdminCardTitle>
          </AdminCardHeader>
          <AdminCardContent>Dashboard content with proper landmarks</AdminCardContent>
        </AdminCard>
      );

      const card = screen.getByRole('region');
      expect(card).toHaveAttribute('aria-labelledby', 'card-title');
      expect(screen.getByRole('heading', { name: 'Admin Dashboard' })).toHaveAttribute(
        'id',
        'card-title'
      );
    });

    it('supports screen reader descriptions', () => {
      render(
        <AdminCard role='region' aria-describedby='card-description'>
          <AdminCardHeader>
            <AdminCardTitle>System Status</AdminCardTitle>
            <AdminCardDescription id='card-description'>
              Current system health and metrics
            </AdminCardDescription>
          </AdminCardHeader>
          <AdminCardContent>Status information</AdminCardContent>
        </AdminCard>
      );

      const card = screen.getByRole('region');
      expect(card).toHaveAttribute('aria-describedby', 'card-description');
    });
  });

  describe('Content Variations', () => {
    it('handles empty card', () => {
      render(<AdminCard data-testid='empty-card' />);

      const card = screen.getByTestId('empty-card');
      expect(card).toBeInTheDocument();
      expect(card).toBeEmptyDOMElement();
    });

    it('handles card with only title', () => {
      render(
        <AdminCard>
          <AdminCardHeader>
            <AdminCardTitle>Minimal Card</AdminCardTitle>
          </AdminCardHeader>
        </AdminCard>
      );

      expect(screen.getByRole('heading', { name: 'Minimal Card' })).toBeInTheDocument();
    });

    it('handles card with rich content', () => {
      render(
        <AdminCard>
          <AdminCardHeader>
            <AdminCardTitle>Rich Content Card</AdminCardTitle>
            <AdminCardDescription>Card with various content types</AdminCardDescription>
          </AdminCardHeader>
          <AdminCardContent>
            <ul>
              <li>Item 1</li>
              <li>Item 2</li>
              <li>Item 3</li>
            </ul>
            <p>Additional paragraph content</p>
            <button type='button'>Embedded button</button>
          </AdminCardContent>
        </AdminCard>
      );

      expect(screen.getByText('Item 1')).toBeInTheDocument();
      expect(screen.getByText('Additional paragraph content')).toBeInTheDocument();
      expect(screen.getByText('Embedded button')).toBeInTheDocument();
    });

    it('handles nested cards', () => {
      render(
        <AdminCard data-testid='outer-card'>
          <AdminCardContent>
            <AdminCard data-testid='inner-card'>
              <AdminCardContent>
                <p>Nested card content</p>
              </AdminCardContent>
            </AdminCard>
          </AdminCardContent>
        </AdminCard>
      );

      expect(screen.getByTestId('outer-card')).toBeInTheDocument();
      expect(screen.getByTestId('inner-card')).toBeInTheDocument();
      expect(screen.getByText('Nested card content')).toBeInTheDocument();
    });
  });

  describe('Styling and Layout', () => {
    it('applies consistent spacing', () => {
      render(
        <AdminCard>
          <AdminCardHeader data-testid='header'>Header</AdminCardHeader>
          <AdminCardContent data-testid='content'>Content</AdminCardContent>
          <AdminCardFooter data-testid='footer'>Footer</AdminCardFooter>
        </AdminCard>
      );

      const header = screen.getByTestId('header');
      const content = screen.getByTestId('content');
      const footer = screen.getByTestId('footer');

      expect(header).toHaveClass('p-4');
      expect(content).toHaveClass('p-4', 'pt-0');
      expect(footer).toHaveClass('p-4', 'pt-3');
    });

    it('handles custom styling combinations', () => {
      render(
        <AdminCard
          variant='elevated'
          interactive
          compact
          className='custom-admin-card'
          data-testid='styled-card'
        >
          <AdminCardHeader compact className='custom-header'>
            <AdminCardTitle size='lg' className='custom-title'>
              Custom Styled Card
            </AdminCardTitle>
          </AdminCardHeader>
          <AdminCardContent compact className='custom-content'>
            Custom content with styling
          </AdminCardContent>
        </AdminCard>
      );

      const card = screen.getByTestId('styled-card');
      expect(card).toHaveClass('custom-admin-card', 'p-3', 'shadow-md', 'cursor-pointer');
    });
  });

  describe('Edge Cases', () => {
    it('handles very long content', () => {
      const longContent = 'Very long content '.repeat(50);

      render(
        <AdminCard>
          <AdminCardContent data-testid='long-content'>{longContent}</AdminCardContent>
        </AdminCard>
      );

      const content = screen.getByTestId('long-content');
      expect(content.textContent).toBe(longContent);
    });

    it('handles special characters in content', () => {
      const specialContent = 'Content with special chars: <>&"\'`{}[]()';

      render(
        <AdminCard>
          <AdminCardTitle>{specialContent}</AdminCardTitle>
        </AdminCard>
      );

      expect(screen.getByRole('heading')).toHaveTextContent(specialContent);
    });

    it('handles dynamic content updates', () => {
      const { rerender } = render(
        <AdminCard>
          <AdminCardTitle>Original Title</AdminCardTitle>
        </AdminCard>
      );

      expect(screen.getByRole('heading')).toHaveTextContent('Original Title');

      rerender(
        <AdminCard>
          <AdminCardTitle>Updated Title</AdminCardTitle>
        </AdminCard>
      );

      expect(screen.getByRole('heading')).toHaveTextContent('Updated Title');
    });
  });

  describe('Performance', () => {
    it('renders efficiently with complex content', () => {
      const startTime = performance.now();

      render(
        <AdminCard>
          <AdminCardHeader>
            <AdminCardTitle>Performance Test Card</AdminCardTitle>
            <AdminCardDescription>Testing rendering performance</AdminCardDescription>
          </AdminCardHeader>
          <AdminCardContent>
            {Array.from({ length: 100 }, (_, i) => (
              <p key={`item-${i}`}>Performance test item {i}</p>
            ))}
          </AdminCardContent>
          <AdminCardFooter>
            {Array.from({ length: 10 }, (_, i) => (
              <button type='button' key={`item-${i}`}>
                Action {i}
              </button>
            ))}
          </AdminCardFooter>
        </AdminCard>
      );

      const endTime = performance.now();

      // Should render within reasonable time
      expect(endTime - startTime).toBeLessThan(100);
      expect(screen.getByRole('heading', { name: 'Performance Test Card' })).toBeInTheDocument();
    });
  });
});
