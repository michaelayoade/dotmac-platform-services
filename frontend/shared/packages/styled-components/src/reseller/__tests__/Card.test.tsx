/**
 * ResellerCard component comprehensive tests
 * Testing reseller-specific card functionality and business workflows
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import React from 'react';

import {
  ResellerCard,
  ResellerCardContent,
  ResellerCardDescription,
  ResellerCardFooter,
  ResellerCardHeader,
  ResellerCardTitle,
} from '../Card';

describe('ResellerCard Component', () => {
  describe('Reseller Business Interface', () => {
    it('renders reseller-optimized card', () => {
      render(
        <ResellerCard data-testid='card'>
          <div>Welcome to your reseller business portal</div>
        </ResellerCard>
      );

      const card = screen.getByTestId('card');
      expect(card).toBeInTheDocument();
      expect(card).toHaveTextContent('Welcome to your reseller business portal');
    });

    it('applies reseller business branding classes', () => {
      render(
        <ResellerCard className='reseller-business-card' data-testid='card'>
          Business content
        </ResellerCard>
      );

      const card = screen.getByTestId('card');
      expect(card).toHaveClass('reseller-business-card');
    });

    it('forwards ref for business integrations', () => {
      const ref = React.createRef<HTMLDivElement>();

      render(
        <ResellerCard ref={ref} data-testid='card'>
          Business information
        </ResellerCard>
      );

      expect(ref.current).toBeInstanceOf(HTMLDivElement);
      expect(ref.current).toBe(screen.getByTestId('card'));
    });

    it('renders as semantic business elements', () => {
      render(
        <ResellerCard asChild>
          <section data-testid='business-section'>Business operations</section>
        </ResellerCard>
      );

      const section = screen.getByTestId('business-section');
      expect(section.tagName).toBe('SECTION');
      expect(section).toHaveTextContent('Business operations');
    });
  });

  describe('Reseller Business Header', () => {
    it('renders business operation header', () => {
      render(
        <ResellerCard>
          <ResellerCardHeader data-testid='header'>
            <ResellerCardTitle>Business Dashboard</ResellerCardTitle>
            <ResellerCardDescription>
              Manage your customer portfolio and business operations
            </ResellerCardDescription>
          </ResellerCardHeader>
        </ResellerCard>
      );

      const header = screen.getByTestId('header');
      expect(header).toBeInTheDocument();
      expect(screen.getByText('Business Dashboard')).toBeInTheDocument();
      expect(
        screen.getByText('Manage your customer portfolio and business operations')
      ).toBeInTheDocument();
    });

    it('applies business header styling', () => {
      render(<ResellerCardHeader data-testid='header'>Business header</ResellerCardHeader>);

      const header = screen.getByTestId('header');
      expect(header).toHaveClass('flex', 'flex-col', 'space-y-1.5', 'p-6');
    });

    it('renders as custom business header element', () => {
      render(
        <ResellerCardHeader asChild>
          <header data-testid='custom-header'>Business Portal Header</header>
        </ResellerCardHeader>
      );

      const header = screen.getByTestId('custom-header');
      expect(header.tagName).toBe('HEADER');
    });
  });

  describe('Reseller Business Title', () => {
    it('renders business operation titles', () => {
      render(<ResellerCardTitle data-testid='title'>Customer Management</ResellerCardTitle>);

      const title = screen.getByTestId('title');
      expect(title).toBeInTheDocument();
      expect(title).toHaveTextContent('Customer Management');
    });

    it('applies business title styling', () => {
      render(<ResellerCardTitle data-testid='title'>Business Title</ResellerCardTitle>);

      const title = screen.getByTestId('title');
      expect(title).toHaveClass('text-2xl', 'font-semibold', 'leading-none', 'tracking-tight');
    });

    it('renders as accessible heading for business', () => {
      render(<ResellerCardTitle>Revenue Analytics</ResellerCardTitle>);

      const title = screen.getByRole('heading');
      expect(title.tagName).toBe('H3');
      expect(title).toHaveTextContent('Revenue Analytics');
    });

    it('supports custom business heading levels', () => {
      render(
        <ResellerCardTitle asChild>
          <h1 data-testid='main-title'>Business Portal</h1>
        </ResellerCardTitle>
      );

      const title = screen.getByTestId('main-title');
      expect(title.tagName).toBe('H1');
    });
  });

  describe('Reseller Business Description', () => {
    it('renders business-friendly descriptions', () => {
      render(
        <ResellerCardDescription data-testid='description'>
          Monitor your customer accounts, track revenue, and manage service provisioning
        </ResellerCardDescription>
      );

      const description = screen.getByTestId('description');
      expect(description).toBeInTheDocument();
      expect(description).toHaveTextContent(
        'Monitor your customer accounts, track revenue, and manage service provisioning'
      );
    });

    it('applies business description styling', () => {
      render(
        <ResellerCardDescription data-testid='description'>
          Business description
        </ResellerCardDescription>
      );

      const description = screen.getByTestId('description');
      expect(description).toHaveClass('text-sm', 'text-reseller-muted-foreground');
    });

    it('renders as accessible business text', () => {
      render(<ResellerCardDescription>Business operations information</ResellerCardDescription>);

      const description = screen.getByText('Business operations information');
      expect(description.tagName).toBe('P');
    });

    it('supports custom business description elements', () => {
      render(
        <ResellerCardDescription asChild>
          <div data-testid='custom-desc'>Enhanced business metrics</div>
        </ResellerCardDescription>
      );

      const description = screen.getByTestId('custom-desc');
      expect(description.tagName).toBe('DIV');
    });
  });

  describe('Reseller Business Content', () => {
    it('renders business portal content', () => {
      render(
        <ResellerCardContent data-testid='content'>
          <div>
            <p>Active Customers: 247</p>
            <p>Monthly Revenue: $124,580</p>
            <p>Commission Rate: 15%</p>
            <p>Status: Active Partner</p>
          </div>
        </ResellerCardContent>
      );

      const content = screen.getByTestId('content');
      expect(content).toBeInTheDocument();
      expect(content).toHaveTextContent('Active Customers: 247');
      expect(content).toHaveTextContent('Monthly Revenue: $124,580');
      expect(content).toHaveTextContent('Commission Rate: 15%');
      expect(content).toHaveTextContent('Status: Active Partner');
    });

    it('applies business content styling', () => {
      render(
        <ResellerCardContent data-testid='content'>Business content area</ResellerCardContent>
      );

      const content = screen.getByTestId('content');
      expect(content).toHaveClass('p-6', 'pt-0');
    });

    it('renders as custom business content element', () => {
      render(
        <ResellerCardContent asChild>
          <main data-testid='main-content'>Main business portal content</main>
        </ResellerCardContent>
      );

      const content = screen.getByTestId('main-content');
      expect(content.tagName).toBe('MAIN');
    });
  });

  describe('Reseller Business Footer', () => {
    it('renders business action footer', () => {
      render(
        <ResellerCardFooter data-testid='footer'>
          <button type='button'>Add Customer</button>
          <button type='button'>Generate Report</button>
          <button type='button'>Billing History</button>
        </ResellerCardFooter>
      );

      const footer = screen.getByTestId('footer');
      expect(footer).toBeInTheDocument();
      expect(screen.getByText('Add Customer')).toBeInTheDocument();
      expect(screen.getByText('Generate Report')).toBeInTheDocument();
      expect(screen.getByText('Billing History')).toBeInTheDocument();
    });

    it('applies business footer styling', () => {
      render(<ResellerCardFooter data-testid='footer'>Business actions</ResellerCardFooter>);

      const footer = screen.getByTestId('footer');
      expect(footer).toHaveClass('flex', 'items-center', 'p-6', 'pt-0');
    });

    it('renders as custom business footer element', () => {
      render(
        <ResellerCardFooter asChild>
          <footer data-testid='custom-footer'>Business portal footer</footer>
        </ResellerCardFooter>
      );

      const footer = screen.getByTestId('custom-footer');
      expect(footer.tagName).toBe('FOOTER');
    });
  });

  describe('Business Portal Use Cases', () => {
    it('renders complete business dashboard card', () => {
      render(
        <ResellerCard data-testid='dashboard-card'>
          <ResellerCardHeader>
            <ResellerCardTitle>Customer Portfolio</ResellerCardTitle>
            <ResellerCardDescription>
              Monitor your customers and track business performance
            </ResellerCardDescription>
          </ResellerCardHeader>
          <ResellerCardContent>
            <div>
              <p>Total Customers: 342</p>
              <p>Active Services: 1,247</p>
              <p>Monthly Revenue: $287,450</p>
              <p>Commission Earned: $43,118</p>
            </div>
          </ResellerCardContent>
          <ResellerCardFooter>
            <button type='button'>View Details</button>
            <button type='button'>Add Customer</button>
            <button type='button'>Generate Report</button>
          </ResellerCardFooter>
        </ResellerCard>
      );

      expect(screen.getByRole('heading', { name: 'Customer Portfolio' })).toBeInTheDocument();
      expect(
        screen.getByText('Monitor your customers and track business performance')
      ).toBeInTheDocument();
      expect(screen.getByText('Total Customers: 342')).toBeInTheDocument();
      expect(screen.getByText('View Details')).toBeInTheDocument();
      expect(screen.getByText('Add Customer')).toBeInTheDocument();
    });

    it('renders business revenue card', () => {
      render(
        <ResellerCard>
          <ResellerCardHeader>
            <ResellerCardTitle>Revenue Analytics</ResellerCardTitle>
            <ResellerCardDescription>
              Track your earnings and commission structure
            </ResellerCardDescription>
          </ResellerCardHeader>
          <ResellerCardContent>
            <div>
              <p>This Month: $43,118</p>
              <p>Last Month: $38,750</p>
              <p>Growth: +11.3%</p>
              <p>Commission Rate: 15%</p>
            </div>
          </ResellerCardContent>
          <ResellerCardFooter>
            <button type='button'>View Statement</button>
            <button type='button'>Payment History</button>
          </ResellerCardFooter>
        </ResellerCard>
      );

      expect(screen.getByRole('heading', { name: 'Revenue Analytics' })).toBeInTheDocument();
      expect(screen.getByText('This Month: $43,118')).toBeInTheDocument();
      expect(screen.getByText('View Statement')).toBeInTheDocument();
    });

    it('renders business tools card', () => {
      render(
        <ResellerCard>
          <ResellerCardHeader>
            <ResellerCardTitle>Business Tools</ResellerCardTitle>
            <ResellerCardDescription>
              Access your partner resources and tools
            </ResellerCardDescription>
          </ResellerCardHeader>
          <ResellerCardContent>
            <div>
              <p>Customer Onboarding</p>
              <p>Service Provisioning</p>
              <p>Billing Management</p>
              <p>Support Portal</p>
            </div>
          </ResellerCardContent>
          <ResellerCardFooter>
            <button type='button'>Open Tools</button>
            <button type='button'>Training</button>
            <button type='button'>Support</button>
          </ResellerCardFooter>
        </ResellerCard>
      );

      expect(screen.getByRole('heading', { name: 'Business Tools' })).toBeInTheDocument();
      expect(screen.getByText('Customer Onboarding')).toBeInTheDocument();
      expect(screen.getByText('Open Tools')).toBeInTheDocument();
    });
  });

  describe('Business Interactions', () => {
    it('handles business card clicks', () => {
      const handleClick = jest.fn();

      render(
        <ResellerCard
          onClick={handleClick}
          className='cursor-pointer hover:shadow-lg'
          data-testid='clickable-card'
        >
          <ResellerCardContent>Click to view business details</ResellerCardContent>
        </ResellerCard>
      );

      const card = screen.getByTestId('clickable-card');
      fireEvent.click(card);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('supports business keyboard navigation', () => {
      const handleKeyDown = jest.fn();

      render(
        <ResellerCard tabIndex={0} onKeyDown={handleKeyDown} data-testid='keyboard-card'>
          <ResellerCardContent>Keyboard accessible business card</ResellerCardContent>
        </ResellerCard>
      );

      const card = screen.getByTestId('keyboard-card');
      card.focus();
      fireEvent.keyDown(card, { key: 'Enter' });

      expect(card).toHaveFocus();
      expect(handleKeyDown).toHaveBeenCalledTimes(1);
    });

    it('handles business hover effects', () => {
      render(
        <ResellerCard
          className='transition-colors hover:border-reseller-primary'
          data-testid='hover-card'
        >
          <ResellerCardContent>Hover for business interaction</ResellerCardContent>
        </ResellerCard>
      );

      const card = screen.getByTestId('hover-card');
      expect(card).toHaveClass('hover:border-reseller-primary', 'transition-colors');
    });
  });

  describe('Business Accessibility', () => {
    it('meets business accessibility standards', async () => {
      const { container } = render(
        <ResellerCard>
          <ResellerCardHeader>
            <ResellerCardTitle>Accessible Business Card</ResellerCardTitle>
            <ResellerCardDescription>
              This card follows business accessibility guidelines
            </ResellerCardDescription>
          </ResellerCardHeader>
          <ResellerCardContent>
            <p>Accessible content for all business users</p>
          </ResellerCardContent>
          <ResellerCardFooter>
            <button type='button'>Accessible Action</button>
          </ResellerCardFooter>
        </ResellerCard>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('supports business ARIA landmarks', () => {
      render(
        <ResellerCard role='region' aria-labelledby='business-card-title'>
          <ResellerCardHeader>
            <ResellerCardTitle id='business-card-title'>Business Portal</ResellerCardTitle>
          </ResellerCardHeader>
          <ResellerCardContent>Portal content with proper business landmarks</ResellerCardContent>
        </ResellerCard>
      );

      const card = screen.getByRole('region');
      expect(card).toHaveAttribute('aria-labelledby', 'business-card-title');
      expect(screen.getByRole('heading', { name: 'Business Portal' })).toHaveAttribute(
        'id',
        'business-card-title'
      );
    });

    it('provides business screen reader support', () => {
      render(
        <ResellerCard aria-describedby='business-description'>
          <ResellerCardHeader>
            <ResellerCardTitle>Business Information</ResellerCardTitle>
            <ResellerCardDescription id='business-description'>
              Detailed information about your business operations
            </ResellerCardDescription>
          </ResellerCardHeader>
          <ResellerCardContent>Business details</ResellerCardContent>
        </ResellerCard>
      );

      const card = screen.getByRole('generic');
      expect(card).toHaveAttribute('aria-describedby', 'business-description');
    });
  });

  describe('Business Variations', () => {
    it('handles empty business card gracefully', () => {
      render(<ResellerCard data-testid='empty-card' />);

      const card = screen.getByTestId('empty-card');
      expect(card).toBeInTheDocument();
      expect(card).toBeEmptyDOMElement();
    });

    it('displays business status information', () => {
      render(
        <ResellerCard>
          <ResellerCardHeader>
            <ResellerCardTitle>Business Status: Active Partner</ResellerCardTitle>
          </ResellerCardHeader>
          <ResellerCardContent>
            <div className='status-indicator green'>●</div>
            <span>All business operations running smoothly</span>
          </ResellerCardContent>
        </ResellerCard>
      );

      expect(
        screen.getByRole('heading', { name: 'Business Status: Active Partner' })
      ).toBeInTheDocument();
      expect(screen.getByText('All business operations running smoothly')).toBeInTheDocument();
    });

    it('handles business data dynamically', () => {
      const { rerender } = render(
        <ResellerCard>
          <ResellerCardTitle>Customers: 125</ResellerCardTitle>
        </ResellerCard>
      );

      expect(screen.getByRole('heading')).toHaveTextContent('Customers: 125');

      rerender(
        <ResellerCard>
          <ResellerCardTitle>Customers: 247</ResellerCardTitle>
        </ResellerCard>
      );

      expect(screen.getByRole('heading')).toHaveTextContent('Customers: 247');
    });

    it('renders nested business information', () => {
      render(
        <ResellerCard data-testid='outer-card'>
          <ResellerCardContent>
            <ResellerCard data-testid='inner-card'>
              <ResellerCardContent>
                <p>Nested business metrics</p>
              </ResellerCardContent>
            </ResellerCard>
          </ResellerCardContent>
        </ResellerCard>
      );

      expect(screen.getByTestId('outer-card')).toBeInTheDocument();
      expect(screen.getByTestId('inner-card')).toBeInTheDocument();
      expect(screen.getByText('Nested business metrics')).toBeInTheDocument();
    });
  });

  describe('Business Performance', () => {
    it('renders business portal efficiently', () => {
      const startTime = performance.now();

      render(
        <ResellerCard>
          <ResellerCardHeader>
            <ResellerCardTitle>High Performance Business Portal</ResellerCardTitle>
            <ResellerCardDescription>Fast loading business experience</ResellerCardDescription>
          </ResellerCardHeader>
          <ResellerCardContent>
            {Array.from({ length: 50 }, (_, i) => (
              <p key={`item-${i}`}>
                Business metric {i}: $1,{i}00
              </p>
            ))}
          </ResellerCardContent>
          <ResellerCardFooter>
            {Array.from({ length: 8 }, (_, i) => (
              <button type='button' key={`item-${i}`}>
                Business Action {i}
              </button>
            ))}
          </ResellerCardFooter>
        </ResellerCard>
      );

      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(100);
      expect(
        screen.getByRole('heading', { name: 'High Performance Business Portal' })
      ).toBeInTheDocument();
    });

    it('handles multiple business cards efficiently', () => {
      const startTime = performance.now();

      render(
        <div>
          {Array.from({ length: 20 }, (_, i) => (
            <ResellerCard key={`item-${i}`}>
              <ResellerCardHeader>
                <ResellerCardTitle>Business Unit {i}</ResellerCardTitle>
              </ResellerCardHeader>
              <ResellerCardContent>
                <p>Revenue: ${i * 1000}</p>
                <p>Customers: {i * 10}</p>
              </ResellerCardContent>
            </ResellerCard>
          ))}
        </div>
      );

      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(200);
      expect(screen.getByRole('heading', { name: 'Business Unit 0' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Business Unit 19' })).toBeInTheDocument();
    });
  });

  describe('Business Styling', () => {
    it('applies consistent business spacing', () => {
      render(
        <ResellerCard>
          <ResellerCardHeader data-testid='header'>Header</ResellerCardHeader>
          <ResellerCardContent data-testid='content'>Content</ResellerCardContent>
          <ResellerCardFooter data-testid='footer'>Footer</ResellerCardFooter>
        </ResellerCard>
      );

      const header = screen.getByTestId('header');
      const content = screen.getByTestId('content');
      const footer = screen.getByTestId('footer');

      expect(header).toHaveClass('p-6');
      expect(content).toHaveClass('p-6', 'pt-0');
      expect(footer).toHaveClass('p-6', 'pt-0');
    });

    it('supports business branding customization', () => {
      render(
        <ResellerCard className='border-reseller-primary bg-reseller-background'>
          <ResellerCardHeader className='bg-reseller-header'>
            <ResellerCardTitle className='text-reseller-primary'>
              Business Branded Title
            </ResellerCardTitle>
          </ResellerCardHeader>
          <ResellerCardContent className='text-reseller-text'>
            Branded business content
          </ResellerCardContent>
        </ResellerCard>
      );

      const card = screen.getByRole('generic');
      expect(card).toHaveClass('border-reseller-primary', 'bg-reseller-background');
    });
  });

  describe('Business Edge Cases', () => {
    it('handles very long business text', () => {
      const longText = 'Business operations and customer management '.repeat(20);

      render(
        <ResellerCard>
          <ResellerCardContent data-testid='long-content'>{longText}</ResellerCardContent>
        </ResellerCard>
      );

      const content = screen.getByTestId('long-content');
      expect(content).toHaveTextContent(longText);
    });

    it('handles special business characters', () => {
      const specialText = "Business: O'Connor & Associates, LLC";

      render(
        <ResellerCard>
          <ResellerCardTitle>{specialText}</ResellerCardTitle>
        </ResellerCard>
      );

      expect(screen.getByRole('heading')).toHaveTextContent(specialText);
    });

    it('handles business data updates smoothly', () => {
      const { rerender } = render(
        <ResellerCard>
          <ResellerCardContent>Revenue: $124,580</ResellerCardContent>
        </ResellerCard>
      );

      expect(screen.getByText('Revenue: $124,580')).toBeInTheDocument();

      rerender(
        <ResellerCard>
          <ResellerCardContent>Revenue: $156,890</ResellerCardContent>
        </ResellerCard>
      );

      expect(screen.getByText('Revenue: $156,890')).toBeInTheDocument();
    });

    it('handles business metric formatting', () => {
      render(
        <ResellerCard>
          <ResellerCardContent>
            <div>Customers: 1,247</div>
            <div>Revenue: $1,234,567.89</div>
            <div>Growth: +15.7%</div>
            <div>Commission: 15.5%</div>
          </ResellerCardContent>
        </ResellerCard>
      );

      expect(screen.getByText('Customers: 1,247')).toBeInTheDocument();
      expect(screen.getByText('Revenue: $1,234,567.89')).toBeInTheDocument();
      expect(screen.getByText('Growth: +15.7%')).toBeInTheDocument();
      expect(screen.getByText('Commission: 15.5%')).toBeInTheDocument();
    });
  });

  describe('Business Integration', () => {
    it('integrates with business state management', () => {
      const TestBusinessCard = () => {
        const [customerCount, setCustomerCount] = React.useState(125);
        const [revenue, setRevenue] = React.useState(45000);

        return (
          <ResellerCard>
            <ResellerCardHeader>
              <ResellerCardTitle>Business Metrics</ResellerCardTitle>
            </ResellerCardHeader>
            <ResellerCardContent>
              <p>Customers: {customerCount}</p>
              <p>Revenue: ${revenue.toLocaleString()}</p>
            </ResellerCardContent>
            <ResellerCardFooter>
              <button type='button' onClick={() => setCustomerCount((c) => c + 1)}>
                Add Customer
              </button>
              <button type='button' onClick={() => setRevenue((r) => r + 1000)}>
                Increase Revenue
              </button>
            </ResellerCardFooter>
          </ResellerCard>
        );
      };

      render(<TestBusinessCard />);

      expect(screen.getByText('Customers: 125')).toBeInTheDocument();
      expect(screen.getByText('Revenue: $45,000')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Add Customer'));
      expect(screen.getByText('Customers: 126')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Increase Revenue'));
      expect(screen.getByText('Revenue: $46,000')).toBeInTheDocument();
    });
  });
});
