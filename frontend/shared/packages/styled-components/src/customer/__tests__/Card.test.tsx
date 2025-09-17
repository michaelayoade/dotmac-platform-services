/**
 * CustomerCard component comprehensive tests
 * Testing customer-specific card functionality and user experience
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import React from 'react';

import {
  CustomerCard,
  CustomerCardContent,
  CustomerCardDescription,
  CustomerCardFooter,
  CustomerCardHeader,
  CustomerCardTitle,
} from '../Card';

describe('CustomerCard Component', () => {
  describe('Customer Card Experience', () => {
    it('renders customer-friendly card', () => {
      render(
        <CustomerCard data-testid='card'>
          <div>Welcome to your customer portal</div>
        </CustomerCard>
      );

      const card = screen.getByTestId('card');
      expect(card).toBeInTheDocument();
      expect(card).toHaveTextContent('Welcome to your customer portal');
    });

    it('applies customer branding classes', () => {
      render(
        <CustomerCard className='customer-portal-card' data-testid='card'>
          Customer content
        </CustomerCard>
      );

      const card = screen.getByTestId('card');
      expect(card).toHaveClass('customer-portal-card');
    });

    it('forwards ref for customer interactions', () => {
      const ref = React.createRef<HTMLDivElement>();

      render(
        <CustomerCard ref={ref} data-testid='card'>
          Customer information
        </CustomerCard>
      );

      expect(ref.current).toBeInstanceOf(HTMLDivElement);
      expect(ref.current).toBe(screen.getByTestId('card'));
    });

    it('renders as semantic customer elements', () => {
      render(
        <CustomerCard asChild>
          <section data-testid='customer-section'>Customer services</section>
        </CustomerCard>
      );

      const section = screen.getByTestId('customer-section');
      expect(section.tagName).toBe('SECTION');
      expect(section).toHaveTextContent('Customer services');
    });
  });

  describe('Customer Card Header', () => {
    it('renders customer service header', () => {
      render(
        <CustomerCard>
          <CustomerCardHeader data-testid='header'>
            <CustomerCardTitle>Account Overview</CustomerCardTitle>
            <CustomerCardDescription>Manage your services and billing</CustomerCardDescription>
          </CustomerCardHeader>
        </CustomerCard>
      );

      const header = screen.getByTestId('header');
      expect(header).toBeInTheDocument();
      expect(screen.getByText('Account Overview')).toBeInTheDocument();
      expect(screen.getByText('Manage your services and billing')).toBeInTheDocument();
    });

    it('applies customer header styling', () => {
      render(<CustomerCardHeader data-testid='header'>Customer header</CustomerCardHeader>);

      const header = screen.getByTestId('header');
      expect(header).toHaveClass('flex', 'flex-col', 'space-y-1.5', 'p-6');
    });

    it('renders as custom customer header element', () => {
      render(
        <CustomerCardHeader asChild>
          <header data-testid='custom-header'>Customer Portal Header</header>
        </CustomerCardHeader>
      );

      const header = screen.getByTestId('custom-header');
      expect(header.tagName).toBe('HEADER');
    });
  });

  describe('Customer Card Title', () => {
    it('renders customer service titles', () => {
      render(<CustomerCardTitle data-testid='title'>Your Services</CustomerCardTitle>);

      const title = screen.getByTestId('title');
      expect(title).toBeInTheDocument();
      expect(title).toHaveTextContent('Your Services');
    });

    it('applies customer title styling', () => {
      render(<CustomerCardTitle data-testid='title'>Customer Title</CustomerCardTitle>);

      const title = screen.getByTestId('title');
      expect(title).toHaveClass('text-2xl', 'font-semibold', 'leading-none', 'tracking-tight');
    });

    it('renders as accessible heading for customers', () => {
      render(<CustomerCardTitle>Service Status</CustomerCardTitle>);

      const title = screen.getByRole('heading');
      expect(title.tagName).toBe('H3');
      expect(title).toHaveTextContent('Service Status');
    });

    it('supports custom customer heading levels', () => {
      render(
        <CustomerCardTitle asChild>
          <h1 data-testid='main-title'>Customer Dashboard</h1>
        </CustomerCardTitle>
      );

      const title = screen.getByTestId('main-title');
      expect(title.tagName).toBe('H1');
    });
  });

  describe('Customer Card Description', () => {
    it('renders customer-friendly descriptions', () => {
      render(
        <CustomerCardDescription data-testid='description'>
          View and manage your internet service, billing, and support options
        </CustomerCardDescription>
      );

      const description = screen.getByTestId('description');
      expect(description).toBeInTheDocument();
      expect(description).toHaveTextContent(
        'View and manage your internet service, billing, and support options'
      );
    });

    it('applies customer description styling', () => {
      render(
        <CustomerCardDescription data-testid='description'>
          Customer description
        </CustomerCardDescription>
      );

      const description = screen.getByTestId('description');
      expect(description).toHaveClass('text-sm', 'text-customer-muted-foreground');
    });

    it('renders as accessible customer text', () => {
      render(<CustomerCardDescription>Service information</CustomerCardDescription>);

      const description = screen.getByText('Service information');
      expect(description.tagName).toBe('P');
    });

    it('supports custom customer description elements', () => {
      render(
        <CustomerCardDescription asChild>
          <div data-testid='custom-desc'>Enhanced customer experience</div>
        </CustomerCardDescription>
      );

      const description = screen.getByTestId('custom-desc');
      expect(description.tagName).toBe('DIV');
    });
  });

  describe('Customer Card Content', () => {
    it('renders customer portal content', () => {
      render(
        <CustomerCardContent data-testid='content'>
          <div>
            <p>Current Plan: Premium Internet</p>
            <p>Speed: 1 Gbps</p>
            <p>Status: Active</p>
          </div>
        </CustomerCardContent>
      );

      const content = screen.getByTestId('content');
      expect(content).toBeInTheDocument();
      expect(content).toHaveTextContent('Current Plan: Premium Internet');
      expect(content).toHaveTextContent('Speed: 1 Gbps');
      expect(content).toHaveTextContent('Status: Active');
    });

    it('applies customer content styling', () => {
      render(
        <CustomerCardContent data-testid='content'>Customer content area</CustomerCardContent>
      );

      const content = screen.getByTestId('content');
      expect(content).toHaveClass('p-6', 'pt-0');
    });

    it('renders as custom customer content element', () => {
      render(
        <CustomerCardContent asChild>
          <main data-testid='main-content'>Main customer portal content</main>
        </CustomerCardContent>
      );

      const content = screen.getByTestId('main-content');
      expect(content.tagName).toBe('MAIN');
    });
  });

  describe('Customer Card Footer', () => {
    it('renders customer action footer', () => {
      render(
        <CustomerCardFooter data-testid='footer'>
          <button type='button'>Upgrade Service</button>
          <button type='button'>Contact Support</button>
        </CustomerCardFooter>
      );

      const footer = screen.getByTestId('footer');
      expect(footer).toBeInTheDocument();
      expect(screen.getByText('Upgrade Service')).toBeInTheDocument();
      expect(screen.getByText('Contact Support')).toBeInTheDocument();
    });

    it('applies customer footer styling', () => {
      render(<CustomerCardFooter data-testid='footer'>Customer actions</CustomerCardFooter>);

      const footer = screen.getByTestId('footer');
      expect(footer).toHaveClass('flex', 'items-center', 'p-6', 'pt-0');
    });

    it('renders as custom customer footer element', () => {
      render(
        <CustomerCardFooter asChild>
          <footer data-testid='custom-footer'>Customer portal footer</footer>
        </CustomerCardFooter>
      );

      const footer = screen.getByTestId('custom-footer');
      expect(footer.tagName).toBe('FOOTER');
    });
  });

  describe('Customer Portal Use Cases', () => {
    it('renders complete customer dashboard card', () => {
      render(
        <CustomerCard data-testid='dashboard-card'>
          <CustomerCardHeader>
            <CustomerCardTitle>Internet Service</CustomerCardTitle>
            <CustomerCardDescription>
              Your current internet plan and usage information
            </CustomerCardDescription>
          </CustomerCardHeader>
          <CustomerCardContent>
            <div>
              <p>Plan: Gigabit Pro</p>
              <p>Speed: 1000 Mbps</p>
              <p>Data Used: 1.2 TB of unlimited</p>
              <p>Next Bill: $79.99 on March 15</p>
            </div>
          </CustomerCardContent>
          <CustomerCardFooter>
            <button type='button'>View Details</button>
            <button type='button'>Upgrade Plan</button>
          </CustomerCardFooter>
        </CustomerCard>
      );

      expect(screen.getByRole('heading', { name: 'Internet Service' })).toBeInTheDocument();
      expect(
        screen.getByText('Your current internet plan and usage information')
      ).toBeInTheDocument();
      expect(screen.getByText('Plan: Gigabit Pro')).toBeInTheDocument();
      expect(screen.getByText('View Details')).toBeInTheDocument();
      expect(screen.getByText('Upgrade Plan')).toBeInTheDocument();
    });

    it('renders customer billing card', () => {
      render(
        <CustomerCard>
          <CustomerCardHeader>
            <CustomerCardTitle>Billing & Payments</CustomerCardTitle>
            <CustomerCardDescription>
              Manage your account and payment methods
            </CustomerCardDescription>
          </CustomerCardHeader>
          <CustomerCardContent>
            <div>
              <p>Current Balance: $79.99</p>
              <p>Due Date: March 15, 2024</p>
              <p>Auto-Pay: Enabled</p>
            </div>
          </CustomerCardContent>
          <CustomerCardFooter>
            <button type='button'>Pay Now</button>
            <button type='button'>View Invoices</button>
          </CustomerCardFooter>
        </CustomerCard>
      );

      expect(screen.getByRole('heading', { name: 'Billing & Payments' })).toBeInTheDocument();
      expect(screen.getByText('Current Balance: $79.99')).toBeInTheDocument();
      expect(screen.getByText('Pay Now')).toBeInTheDocument();
    });

    it('renders customer support card', () => {
      render(
        <CustomerCard>
          <CustomerCardHeader>
            <CustomerCardTitle>Customer Support</CustomerCardTitle>
            <CustomerCardDescription>Get help with your services</CustomerCardDescription>
          </CustomerCardHeader>
          <CustomerCardContent>
            <div>
              <p>Available 24/7</p>
              <p>Average wait time: 2 minutes</p>
              <p>Live chat available</p>
            </div>
          </CustomerCardContent>
          <CustomerCardFooter>
            <button type='button'>Start Chat</button>
            <button type='button'>Call Support</button>
            <button type='button'>Email Us</button>
          </CustomerCardFooter>
        </CustomerCard>
      );

      expect(screen.getByRole('heading', { name: 'Customer Support' })).toBeInTheDocument();
      expect(screen.getByText('Available 24/7')).toBeInTheDocument();
      expect(screen.getByText('Start Chat')).toBeInTheDocument();
    });
  });

  describe('Customer Interactions', () => {
    it('handles customer card clicks', () => {
      const handleClick = jest.fn();

      render(
        <CustomerCard
          onClick={handleClick}
          className='cursor-pointer hover:shadow-lg'
          data-testid='clickable-card'
        >
          <CustomerCardContent>Click to view details</CustomerCardContent>
        </CustomerCard>
      );

      const card = screen.getByTestId('clickable-card');
      fireEvent.click(card);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('supports customer keyboard navigation', () => {
      const handleKeyDown = jest.fn();

      render(
        <CustomerCard tabIndex={0} onKeyDown={handleKeyDown} data-testid='keyboard-card'>
          <CustomerCardContent>Keyboard accessible</CustomerCardContent>
        </CustomerCard>
      );

      const card = screen.getByTestId('keyboard-card');
      card.focus();
      fireEvent.keyDown(card, { key: 'Enter' });

      expect(card).toHaveFocus();
      expect(handleKeyDown).toHaveBeenCalledTimes(1);
    });

    it('handles customer hover effects', () => {
      render(
        <CustomerCard
          className='transition-colors hover:border-customer-primary'
          data-testid='hover-card'
        >
          <CustomerCardContent>Hover for interaction</CustomerCardContent>
        </CustomerCard>
      );

      const card = screen.getByTestId('hover-card');
      expect(card).toHaveClass('hover:border-customer-primary', 'transition-colors');
    });
  });

  describe('Customer Accessibility', () => {
    it('meets customer accessibility standards', async () => {
      const { container } = render(
        <CustomerCard>
          <CustomerCardHeader>
            <CustomerCardTitle>Accessible Customer Card</CustomerCardTitle>
            <CustomerCardDescription>
              This card follows accessibility guidelines
            </CustomerCardDescription>
          </CustomerCardHeader>
          <CustomerCardContent>
            <p>Accessible content for all customers</p>
          </CustomerCardContent>
          <CustomerCardFooter>
            <button type='button'>Accessible Action</button>
          </CustomerCardFooter>
        </CustomerCard>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('supports customer ARIA landmarks', () => {
      render(
        <CustomerCard role='region' aria-labelledby='customer-card-title'>
          <CustomerCardHeader>
            <CustomerCardTitle id='customer-card-title'>Customer Portal</CustomerCardTitle>
          </CustomerCardHeader>
          <CustomerCardContent>Portal content with proper landmarks</CustomerCardContent>
        </CustomerCard>
      );

      const card = screen.getByRole('region');
      expect(card).toHaveAttribute('aria-labelledby', 'customer-card-title');
      expect(screen.getByRole('heading', { name: 'Customer Portal' })).toHaveAttribute(
        'id',
        'customer-card-title'
      );
    });

    it('provides customer screen reader support', () => {
      render(
        <CustomerCard aria-describedby='customer-description'>
          <CustomerCardHeader>
            <CustomerCardTitle>Service Information</CustomerCardTitle>
            <CustomerCardDescription id='customer-description'>
              Detailed information about your current services
            </CustomerCardDescription>
          </CustomerCardHeader>
          <CustomerCardContent>Service details</CustomerCardContent>
        </CustomerCard>
      );

      const card = screen.getByRole('generic');
      expect(card).toHaveAttribute('aria-describedby', 'customer-description');
    });
  });

  describe('Customer Experience Variations', () => {
    it('handles empty customer card gracefully', () => {
      render(<CustomerCard data-testid='empty-card' />);

      const card = screen.getByTestId('empty-card');
      expect(card).toBeInTheDocument();
      expect(card).toBeEmptyDOMElement();
    });

    it('displays customer status information', () => {
      render(
        <CustomerCard>
          <CustomerCardHeader>
            <CustomerCardTitle>Service Status: Active</CustomerCardTitle>
          </CustomerCardHeader>
          <CustomerCardContent>
            <div className='status-indicator green'>●</div>
            <span>All services operating normally</span>
          </CustomerCardContent>
        </CustomerCard>
      );

      expect(screen.getByRole('heading', { name: 'Service Status: Active' })).toBeInTheDocument();
      expect(screen.getByText('All services operating normally')).toBeInTheDocument();
    });

    it('handles customer data dynamically', () => {
      const { rerender } = render(
        <CustomerCard>
          <CustomerCardTitle>Current Plan: Basic</CustomerCardTitle>
        </CustomerCard>
      );

      expect(screen.getByRole('heading')).toHaveTextContent('Current Plan: Basic');

      rerender(
        <CustomerCard>
          <CustomerCardTitle>Current Plan: Premium</CustomerCardTitle>
        </CustomerCard>
      );

      expect(screen.getByRole('heading')).toHaveTextContent('Current Plan: Premium');
    });

    it('renders nested customer information', () => {
      render(
        <CustomerCard data-testid='outer-card'>
          <CustomerCardContent>
            <CustomerCard data-testid='inner-card'>
              <CustomerCardContent>
                <p>Nested service details</p>
              </CustomerCardContent>
            </CustomerCard>
          </CustomerCardContent>
        </CustomerCard>
      );

      expect(screen.getByTestId('outer-card')).toBeInTheDocument();
      expect(screen.getByTestId('inner-card')).toBeInTheDocument();
      expect(screen.getByText('Nested service details')).toBeInTheDocument();
    });
  });

  describe('Customer Performance', () => {
    it('renders customer portal efficiently', () => {
      const startTime = performance.now();

      render(
        <CustomerCard>
          <CustomerCardHeader>
            <CustomerCardTitle>High Performance Customer Portal</CustomerCardTitle>
            <CustomerCardDescription>Fast loading customer experience</CustomerCardDescription>
          </CustomerCardHeader>
          <CustomerCardContent>
            {Array.from({ length: 20 }, (_, i) => (
              <p key={`item-${i}`}>Customer service item {i}</p>
            ))}
          </CustomerCardContent>
          <CustomerCardFooter>
            {Array.from({ length: 5 }, (_, i) => (
              <button type='button' key={`item-${i}`}>
                Action {i}
              </button>
            ))}
          </CustomerCardFooter>
        </CustomerCard>
      );

      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(50);
      expect(
        screen.getByRole('heading', { name: 'High Performance Customer Portal' })
      ).toBeInTheDocument();
    });

    it('handles multiple customer cards efficiently', () => {
      const startTime = performance.now();

      render(
        <div>
          {Array.from({ length: 10 }, (_, i) => (
            <CustomerCard key={`item-${i}`}>
              <CustomerCardHeader>
                <CustomerCardTitle>Customer Service {i}</CustomerCardTitle>
              </CustomerCardHeader>
              <CustomerCardContent>
                <p>Service details for customer {i}</p>
              </CustomerCardContent>
            </CustomerCard>
          ))}
        </div>
      );

      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(100);
      expect(screen.getByRole('heading', { name: 'Customer Service 0' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Customer Service 9' })).toBeInTheDocument();
    });
  });

  describe('Customer Styling', () => {
    it('applies consistent customer spacing', () => {
      render(
        <CustomerCard>
          <CustomerCardHeader data-testid='header'>Header</CustomerCardHeader>
          <CustomerCardContent data-testid='content'>Content</CustomerCardContent>
          <CustomerCardFooter data-testid='footer'>Footer</CustomerCardFooter>
        </CustomerCard>
      );

      const header = screen.getByTestId('header');
      const content = screen.getByTestId('content');
      const footer = screen.getByTestId('footer');

      expect(header).toHaveClass('p-6');
      expect(content).toHaveClass('p-6', 'pt-0');
      expect(footer).toHaveClass('p-6', 'pt-0');
    });

    it('supports customer branding customization', () => {
      render(
        <CustomerCard className='border-customer-primary bg-customer-background'>
          <CustomerCardHeader className='bg-customer-header'>
            <CustomerCardTitle className='text-customer-primary'>Branded Title</CustomerCardTitle>
          </CustomerCardHeader>
          <CustomerCardContent className='text-customer-text'>
            Branded customer content
          </CustomerCardContent>
        </CustomerCard>
      );

      const card = screen.getByRole('generic');
      expect(card).toHaveClass('border-customer-primary', 'bg-customer-background');
    });
  });

  describe('Customer Edge Cases', () => {
    it('handles very long customer text', () => {
      const longText = 'Customer service information '.repeat(50);

      render(
        <CustomerCard>
          <CustomerCardContent data-testid='long-content'>{longText}</CustomerCardContent>
        </CustomerCard>
      );

      const content = screen.getByTestId('long-content');
      expect(content).toHaveTextContent(longText);
    });

    it('handles special customer characters', () => {
      const specialText = "Customer: O'Connor & Associates";

      render(
        <CustomerCard>
          <CustomerCardTitle>{specialText}</CustomerCardTitle>
        </CustomerCard>
      );

      expect(screen.getByRole('heading')).toHaveTextContent(specialText);
    });

    it('handles customer data updates smoothly', () => {
      const { rerender } = render(
        <CustomerCard>
          <CustomerCardContent>Balance: $79.99</CustomerCardContent>
        </CustomerCard>
      );

      expect(screen.getByText('Balance: $79.99')).toBeInTheDocument();

      rerender(
        <CustomerCard>
          <CustomerCardContent>Balance: $0.00</CustomerCardContent>
        </CustomerCard>
      );

      expect(screen.getByText('Balance: $0.00')).toBeInTheDocument();
    });
  });
});
