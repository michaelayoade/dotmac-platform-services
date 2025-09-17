/**
 * CustomerButton component comprehensive tests
 * Testing customer-specific button functionality and variants
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import React from 'react';

import { CustomerButton } from '../Button';

describe('CustomerButton Component', () => {
  describe('Basic Rendering', () => {
    it('renders as button by default', () => {
      render(<CustomerButton>Click me</CustomerButton>);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Click me');
    });

    it('renders as child component when asChild is true', () => {
      render(
        <CustomerButton asChild>
          <a href='/customer'>Customer Link</a>
        </CustomerButton>
      );

      const link = screen.getByRole('link');
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', '/customer');
    });

    it('applies custom className', () => {
      render(<CustomerButton className='customer-btn'>Button</CustomerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('customer-btn');
    });
  });

  describe('Customer-Specific Variants', () => {
    it('renders primary variant with customer branding', () => {
      render(<CustomerButton variant='default'>Primary Action</CustomerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-customer-primary');
    });

    it('renders secondary variant with customer styling', () => {
      render(<CustomerButton variant='secondary'>Secondary</CustomerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-customer-secondary');
    });

    it('renders outline variant with customer border', () => {
      render(<CustomerButton variant='outline'>Outline</CustomerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('border-customer-primary');
    });

    it('renders ghost variant with customer hover', () => {
      render(<CustomerButton variant='ghost'>Ghost</CustomerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('hover:bg-customer-accent');
    });

    it('renders destructive variant', () => {
      render(<CustomerButton variant='destructive'>Delete</CustomerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-customer-destructive');
    });

    it('renders link variant with customer link styling', () => {
      render(<CustomerButton variant='link'>Link Style</CustomerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('text-customer-primary');
    });
  });

  describe('Customer-Optimized Sizes', () => {
    it('renders customer-friendly default size', () => {
      render(<CustomerButton size='default'>Default</CustomerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-10', 'px-4', 'py-2');
    });

    it('renders compact size for mobile customers', () => {
      render(<CustomerButton size='sm'>Compact</CustomerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-9', 'px-3');
    });

    it('renders prominent size for key actions', () => {
      render(<CustomerButton size='lg'>Prominent</CustomerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-11', 'px-8');
    });

    it('renders icon size for customer tools', () => {
      render(<CustomerButton size='icon'>⚙</CustomerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-10', 'w-10');
    });
  });

  describe('Customer Experience Features', () => {
    it('handles loading state with customer feedback', () => {
      render(<CustomerButton loading>Processing</CustomerButton>);

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });

    it('shows customer-friendly loading text', () => {
      render(
        <CustomerButton loading loadingText='Please wait...'>
          Submit
        </CustomerButton>
      );

      expect(screen.getByText('Please wait...')).toBeInTheDocument();
      expect(screen.queryByText('Submit')).not.toBeInTheDocument();
    });

    it('renders with customer service icons', () => {
      const ServiceIcon = () => <span data-testid='service-icon'>📞</span>;

      render(<CustomerButton leftIcon={<ServiceIcon />}>Contact Support</CustomerButton>);

      expect(screen.getByTestId('service-icon')).toBeInTheDocument();
      expect(screen.getByText('Contact Support')).toBeInTheDocument();
    });

    it('handles disabled state with clear feedback', () => {
      render(<CustomerButton disabled>Unavailable</CustomerButton>);

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
      expect(button).toHaveClass('disabled:opacity-50');
    });
  });

  describe('Customer Interactions', () => {
    it('handles customer actions with feedback', () => {
      const handleClick = jest.fn();

      render(<CustomerButton onClick={handleClick}>Customer Action</CustomerButton>);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('prevents action when loading for customer safety', () => {
      const handleClick = jest.fn();

      render(
        <CustomerButton onClick={handleClick} loading>
          Loading
        </CustomerButton>
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(handleClick).not.toHaveBeenCalled();
    });

    it('supports keyboard navigation for accessibility', () => {
      const handleKeyDown = jest.fn();

      render(<CustomerButton onKeyDown={handleKeyDown}>Accessible</CustomerButton>);

      const button = screen.getByRole('button');
      fireEvent.keyDown(button, { key: 'Enter' });

      expect(handleKeyDown).toHaveBeenCalledTimes(1);
    });

    it('handles form submission for customer forms', () => {
      const handleSubmit = jest.fn((e) => e.preventDefault());

      render(
        <form onSubmit={handleSubmit}>
          <CustomerButton type='submit'>Submit Request</CustomerButton>
        </form>
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(handleSubmit).toHaveBeenCalledTimes(1);
    });
  });

  describe('Customer Portal Integration', () => {
    it('forwards ref for customer portal features', () => {
      const ref = React.createRef<HTMLButtonElement>();

      render(<CustomerButton ref={ref}>Portal Button</CustomerButton>);

      expect(ref.current).toBeInstanceOf(HTMLButtonElement);
      expect(ref.current?.textContent).toBe('Portal Button');
    });

    it('works with customer portal navigation', () => {
      const ref = React.createRef<HTMLAnchorElement>();

      render(
        <CustomerButton asChild ref={ref}>
          <a href='/customer/dashboard'>Dashboard</a>
        </CustomerButton>
      );

      expect(ref.current).toBeInstanceOf(HTMLAnchorElement);
      expect(ref.current?.href).toContain('/customer/dashboard');
    });
  });

  describe('Customer Accessibility', () => {
    it('meets customer accessibility standards', async () => {
      const { container } = render(<CustomerButton>Accessible Button</CustomerButton>);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('provides clear disabled state for customers', async () => {
      const { container } = render(<CustomerButton disabled>Disabled Action</CustomerButton>);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('announces loading state to screen readers', async () => {
      const { container } = render(<CustomerButton loading>Loading Action</CustomerButton>);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('supports customer-specific ARIA labels', () => {
      render(
        <CustomerButton aria-label='Contact customer service' aria-describedby='help-text'>
          Help
        </CustomerButton>
      );

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', 'Contact customer service');
      expect(button).toHaveAttribute('aria-describedby', 'help-text');
    });
  });

  describe('Customer Use Cases', () => {
    it('handles account management actions', () => {
      render(
        <div>
          <CustomerButton variant='default'>Update Profile</CustomerButton>
          <CustomerButton variant='secondary'>Change Password</CustomerButton>
          <CustomerButton variant='outline'>View Billing</CustomerButton>
        </div>
      );

      expect(screen.getByText('Update Profile')).toBeInTheDocument();
      expect(screen.getByText('Change Password')).toBeInTheDocument();
      expect(screen.getByText('View Billing')).toBeInTheDocument();
    });

    it('handles service requests', () => {
      const SupportIcon = () => <span data-testid='support'>🎧</span>;

      render(
        <CustomerButton leftIcon={<SupportIcon />} variant='default'>
          Request Support
        </CustomerButton>
      );

      expect(screen.getByTestId('support')).toBeInTheDocument();
      expect(screen.getByText('Request Support')).toBeInTheDocument();
    });

    it('handles billing actions', () => {
      render(
        <div>
          <CustomerButton variant='default'>Pay Bill</CustomerButton>
          <CustomerButton variant='outline'>Download Invoice</CustomerButton>
          <CustomerButton variant='ghost'>View History</CustomerButton>
        </div>
      );

      expect(screen.getByText('Pay Bill')).toBeInTheDocument();
      expect(screen.getByText('Download Invoice')).toBeInTheDocument();
      expect(screen.getByText('View History')).toBeInTheDocument();
    });

    it('handles service management', () => {
      render(
        <div>
          <CustomerButton variant='default'>Upgrade Service</CustomerButton>
          <CustomerButton variant='secondary'>Modify Plan</CustomerButton>
          <CustomerButton variant='destructive'>Cancel Service</CustomerButton>
        </div>
      );

      expect(screen.getByText('Upgrade Service')).toBeInTheDocument();
      expect(screen.getByText('Modify Plan')).toBeInTheDocument();
      expect(screen.getByText('Cancel Service')).toBeInTheDocument();
    });
  });

  describe('Customer Experience Edge Cases', () => {
    it('handles empty customer actions gracefully', () => {
      render(<CustomerButton />);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('handles customer content variations', () => {
      render(<CustomerButton>{null}</CustomerButton>);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('displays customer numbers correctly', () => {
      render(<CustomerButton>Account: {12345}</CustomerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveTextContent('Account: 12345');
    });

    it('handles mixed customer content', () => {
      render(
        <CustomerButton>
          Service <span>Status: Active</span>
        </CustomerButton>
      );

      const button = screen.getByRole('button');
      expect(button).toHaveTextContent('Service Status: Active');
    });
  });

  describe('Customer Performance', () => {
    it('renders efficiently for customer portal', () => {
      const startTime = performance.now();

      render(
        <CustomerButton
          variant='default'
          size='lg'
          disabled={false}
          loading={false}
          leftIcon={<span>💼</span>}
          rightIcon={<span>→</span>}
          className='customer-portal-btn'
          onClick={() => {
            // Event handler implementation pending
          }}
          aria-label='Customer portal action'
        >
          Customer Portal Action
        </CustomerButton>
      );

      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(10);
      expect(screen.getByLabelText('Customer portal action')).toBeInTheDocument();
    });

    it('handles rapid customer interactions', () => {
      const handleClick = jest.fn();

      render(<CustomerButton onClick={handleClick}>Fast Action</CustomerButton>);

      const button = screen.getByRole('button');

      // Simulate rapid clicks
      for (let i = 0; i < 10; i++) {
        fireEvent.click(button);
      }

      expect(handleClick).toHaveBeenCalledTimes(10);
    });
  });

  describe('Customer Variant Combinations', () => {
    const customerVariants = [
      'default',
      'destructive',
      'outline',
      'secondary',
      'ghost',
      'link',
    ] as const;
    const customerSizes = ['default', 'sm', 'lg', 'icon'] as const;

    customerVariants.forEach((variant) => {
      it(`renders customer ${variant} variant correctly`, () => {
        render(<CustomerButton variant={variant}>Customer {variant}</CustomerButton>);

        const button = screen.getByRole('button');
        expect(button).toBeInTheDocument();
        expect(button).toHaveTextContent(`Customer ${variant}`);
      });
    });

    customerSizes.forEach((size) => {
      it(`renders customer ${size} size correctly`, () => {
        render(<CustomerButton size={size}>Customer {size}</CustomerButton>);

        const button = screen.getByRole('button');
        expect(button).toBeInTheDocument();
      });
    });

    it('handles all customer variant and size combinations', () => {
      customerVariants.forEach((variant) => {
        customerSizes.forEach((size) => {
          const { unmount } = render(
            <CustomerButton variant={variant} size={size}>
              {variant} {size}
            </CustomerButton>
          );

          const button = screen.getByRole('button');
          expect(button).toBeInTheDocument();

          unmount();
        });
      });
    });
  });
});
