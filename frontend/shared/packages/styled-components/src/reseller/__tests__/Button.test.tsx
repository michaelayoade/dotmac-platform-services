/**
 * ResellerButton component comprehensive tests
 * Testing reseller-specific button functionality and business workflows
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import React from 'react';

import { ResellerButton } from '../Button';

describe('ResellerButton Component', () => {
  describe('Reseller Business Interface', () => {
    it('renders reseller-optimized button', () => {
      render(<ResellerButton>Manage Customers</ResellerButton>);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Manage Customers');
    });

    it('renders as child component for reseller workflows', () => {
      render(
        <ResellerButton asChild>
          <a href='/reseller/dashboard'>Reseller Dashboard</a>
        </ResellerButton>
      );

      const link = screen.getByRole('link');
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', '/reseller/dashboard');
    });

    it('applies reseller branding classes', () => {
      render(<ResellerButton className='reseller-action'>Business Action</ResellerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('reseller-action');
    });
  });

  describe('Reseller-Specific Variants', () => {
    it('renders primary variant with reseller branding', () => {
      render(<ResellerButton variant='default'>Create Customer</ResellerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-reseller-primary');
    });

    it('renders secondary variant for reseller tools', () => {
      render(<ResellerButton variant='secondary'>Bulk Actions</ResellerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-reseller-secondary');
    });

    it('renders outline variant for reseller navigation', () => {
      render(<ResellerButton variant='outline'>View Reports</ResellerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('border-reseller-primary');
    });

    it('renders ghost variant for reseller utilities', () => {
      render(<ResellerButton variant='ghost'>Quick Edit</ResellerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('hover:bg-reseller-accent');
    });

    it('renders destructive variant for critical reseller actions', () => {
      render(<ResellerButton variant='destructive'>Suspend Account</ResellerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-reseller-destructive');
    });

    it('renders link variant with reseller styling', () => {
      render(<ResellerButton variant='link'>View Details</ResellerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('text-reseller-primary');
    });
  });

  describe('Reseller Business Sizes', () => {
    it('renders comfortable default size for business users', () => {
      render(<ResellerButton size='default'>Standard Action</ResellerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-10', 'px-4', 'py-2');
    });

    it('renders compact size for dense reseller interfaces', () => {
      render(<ResellerButton size='sm'>Quick Action</ResellerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-9', 'px-3');
    });

    it('renders prominent size for key business actions', () => {
      render(<ResellerButton size='lg'>Create Account</ResellerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-11', 'px-8');
    });

    it('renders icon size for reseller tools', () => {
      render(<ResellerButton size='icon'>⚙</ResellerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-10', 'w-10');
    });
  });

  describe('Reseller Business Features', () => {
    it('handles business process loading states', () => {
      render(<ResellerButton loading>Processing Customer Data</ResellerButton>);

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });

    it('shows business-friendly loading messages', () => {
      render(
        <ResellerButton loading loadingText='Creating customer account...'>
          Create Customer
        </ResellerButton>
      );

      expect(screen.getByText('Creating customer account...')).toBeInTheDocument();
      expect(screen.queryByText('Create Customer')).not.toBeInTheDocument();
    });

    it('renders with business operation icons', () => {
      const BusinessIcon = () => <span data-testid='business-icon'>💼</span>;

      render(<ResellerButton leftIcon={<BusinessIcon />}>Manage Portfolio</ResellerButton>);

      expect(screen.getByTestId('business-icon')).toBeInTheDocument();
      expect(screen.getByText('Manage Portfolio')).toBeInTheDocument();
    });

    it('handles disabled state for restricted business actions', () => {
      render(<ResellerButton disabled>Restricted Action</ResellerButton>);

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
      expect(button).toHaveClass('disabled:opacity-50');
    });
  });

  describe('Reseller Business Interactions', () => {
    it('handles reseller business actions', () => {
      const handleClick = jest.fn();

      render(<ResellerButton onClick={handleClick}>Execute Business Action</ResellerButton>);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('prevents actions during business processes', () => {
      const handleClick = jest.fn();

      render(
        <ResellerButton onClick={handleClick} loading>
          Processing
        </ResellerButton>
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(handleClick).not.toHaveBeenCalled();
    });

    it('supports business keyboard workflows', () => {
      const handleKeyDown = jest.fn();

      render(<ResellerButton onKeyDown={handleKeyDown}>Business Shortcut</ResellerButton>);

      const button = screen.getByRole('button');
      fireEvent.keyDown(button, { key: 'Enter' });

      expect(handleKeyDown).toHaveBeenCalledTimes(1);
    });

    it('handles reseller form submissions', () => {
      const handleSubmit = jest.fn((e) => e.preventDefault());

      render(
        <form onSubmit={handleSubmit}>
          <ResellerButton type='submit'>Submit Business Form</ResellerButton>
        </form>
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(handleSubmit).toHaveBeenCalledTimes(1);
    });
  });

  describe('Reseller Portal Integration', () => {
    it('forwards ref for reseller portal features', () => {
      const ref = React.createRef<HTMLButtonElement>();

      render(<ResellerButton ref={ref}>Portal Button</ResellerButton>);

      expect(ref.current).toBeInstanceOf(HTMLButtonElement);
      expect(ref.current?.textContent).toBe('Portal Button');
    });

    it('works with reseller navigation systems', () => {
      const ref = React.createRef<HTMLAnchorElement>();

      render(
        <ResellerButton asChild ref={ref}>
          <a href='/reseller/customers'>Customer Management</a>
        </ResellerButton>
      );

      expect(ref.current).toBeInstanceOf(HTMLAnchorElement);
      expect(ref.current?.href).toContain('/reseller/customers');
    });
  });

  describe('Reseller Accessibility', () => {
    it('meets business accessibility standards', async () => {
      const { container } = render(<ResellerButton>Business Accessible Button</ResellerButton>);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('provides clear business state feedback', async () => {
      const { container } = render(
        <ResellerButton disabled>Disabled Business Action</ResellerButton>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('announces business process states', async () => {
      const { container } = render(<ResellerButton loading>Loading Business Data</ResellerButton>);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('supports business-specific ARIA labels', () => {
      render(
        <ResellerButton aria-label='Create new customer account' aria-describedby='business-help'>
          New Customer
        </ResellerButton>
      );

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', 'Create new customer account');
      expect(button).toHaveAttribute('aria-describedby', 'business-help');
    });
  });

  describe('Reseller Business Use Cases', () => {
    it('handles customer management workflows', () => {
      render(
        <div>
          <ResellerButton variant='default'>Add Customer</ResellerButton>
          <ResellerButton variant='secondary'>Bulk Import</ResellerButton>
          <ResellerButton variant='outline'>Export List</ResellerButton>
          <ResellerButton variant='destructive'>Suspend Account</ResellerButton>
        </div>
      );

      expect(screen.getByText('Add Customer')).toBeInTheDocument();
      expect(screen.getByText('Bulk Import')).toBeInTheDocument();
      expect(screen.getByText('Export List')).toBeInTheDocument();
      expect(screen.getByText('Suspend Account')).toBeInTheDocument();
    });

    it('handles billing and financial operations', () => {
      const MoneyIcon = () => <span data-testid='money'>💰</span>;

      render(
        <div>
          <ResellerButton leftIcon={<MoneyIcon />}>Process Payments</ResellerButton>
          <ResellerButton variant='outline'>Generate Invoices</ResellerButton>
          <ResellerButton variant='secondary'>View Commissions</ResellerButton>
        </div>
      );

      expect(screen.getByTestId('money')).toBeInTheDocument();
      expect(screen.getByText('Process Payments')).toBeInTheDocument();
      expect(screen.getByText('Generate Invoices')).toBeInTheDocument();
      expect(screen.getByText('View Commissions')).toBeInTheDocument();
    });

    it('handles service provisioning', () => {
      render(
        <div>
          <ResellerButton variant='default'>Provision Service</ResellerButton>
          <ResellerButton variant='secondary'>Modify Plan</ResellerButton>
          <ResellerButton variant='outline'>Schedule Installation</ResellerButton>
          <ResellerButton variant='destructive'>Disconnect Service</ResellerButton>
        </div>
      );

      expect(screen.getByText('Provision Service')).toBeInTheDocument();
      expect(screen.getByText('Modify Plan')).toBeInTheDocument();
      expect(screen.getByText('Schedule Installation')).toBeInTheDocument();
      expect(screen.getByText('Disconnect Service')).toBeInTheDocument();
    });

    it('handles reporting and analytics', () => {
      const ChartIcon = () => <span data-testid='chart'>📊</span>;

      render(
        <div>
          <ResellerButton leftIcon={<ChartIcon />}>View Reports</ResellerButton>
          <ResellerButton variant='outline'>Export Data</ResellerButton>
          <ResellerButton variant='ghost'>Quick Stats</ResellerButton>
        </div>
      );

      expect(screen.getByTestId('chart')).toBeInTheDocument();
      expect(screen.getByText('View Reports')).toBeInTheDocument();
      expect(screen.getByText('Export Data')).toBeInTheDocument();
      expect(screen.getByText('Quick Stats')).toBeInTheDocument();
    });
  });

  describe('Reseller Edge Cases', () => {
    it('handles empty business actions gracefully', () => {
      render(<ResellerButton />);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('handles null business content', () => {
      render(<ResellerButton>{null}</ResellerButton>);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('displays business numbers correctly', () => {
      render(<ResellerButton>Customer ID: {67890}</ResellerButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveTextContent('Customer ID: 67890');
    });

    it('handles mixed business content', () => {
      render(
        <ResellerButton>
          Account <span>Status: Active</span> <span>($1,234 MRR)</span>
        </ResellerButton>
      );

      const button = screen.getByRole('button');
      expect(button).toHaveTextContent('Account Status: Active ($1,234 MRR)');
    });
  });

  describe('Reseller Performance', () => {
    it('renders efficiently for business portals', () => {
      const startTime = performance.now();

      render(
        <ResellerButton
          variant='default'
          size='lg'
          disabled={false}
          loading={false}
          leftIcon={<span>💼</span>}
          rightIcon={<span>→</span>}
          className='reseller-portal-btn'
          onClick={() => {
            // Event handler implementation pending
          }}
          aria-label='Business portal action'
        >
          Business Portal Action
        </ResellerButton>
      );

      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(10);
      expect(screen.getByLabelText('Business portal action')).toBeInTheDocument();
    });

    it('handles rapid business interactions efficiently', () => {
      const handleClick = jest.fn();

      render(<ResellerButton onClick={handleClick}>Fast Business Action</ResellerButton>);

      const button = screen.getByRole('button');

      // Simulate rapid business clicks
      for (let i = 0; i < 10; i++) {
        fireEvent.click(button);
      }

      expect(handleClick).toHaveBeenCalledTimes(10);
    });
  });

  describe('Reseller Variant Combinations', () => {
    const resellerVariants = [
      'default',
      'destructive',
      'outline',
      'secondary',
      'ghost',
      'link',
    ] as const;
    const resellerSizes = ['default', 'sm', 'lg', 'icon'] as const;

    resellerVariants.forEach((variant) => {
      it(`renders reseller ${variant} variant correctly`, () => {
        render(<ResellerButton variant={variant}>Reseller {variant}</ResellerButton>);

        const button = screen.getByRole('button');
        expect(button).toBeInTheDocument();
        expect(button).toHaveTextContent(`Reseller ${variant}`);
      });
    });

    resellerSizes.forEach((size) => {
      it(`renders reseller ${size} size correctly`, () => {
        render(<ResellerButton size={size}>Reseller {size}</ResellerButton>);

        const button = screen.getByRole('button');
        expect(button).toBeInTheDocument();
      });
    });

    it('handles all reseller variant and size combinations', () => {
      resellerVariants.forEach((variant) => {
        resellerSizes.forEach((size) => {
          const { unmount } = render(
            <ResellerButton variant={variant} size={size}>
              {variant} {size}
            </ResellerButton>
          );

          const button = screen.getByRole('button');
          expect(button).toBeInTheDocument();

          unmount();
        });
      });
    });
  });

  describe('Reseller Business Workflows', () => {
    it('handles multi-step business processes', () => {
      const ProcessButton = ({ step }: { step: number }) => (
        <ResellerButton variant={step === 1 ? 'default' : 'outline'} disabled={step > 1}>
          Step {step}: {step === 1 ? 'Collect Info' : step === 2 ? 'Validate' : 'Provision'}
        </ResellerButton>
      );

      render(
        <div>
          <ProcessButton step={1} />
          <ProcessButton step={2} />
          <ProcessButton step={3} />
        </div>
      );

      expect(screen.getByText('Step 1: Collect Info')).toBeInTheDocument();
      expect(screen.getByText('Step 2: Validate')).toBeDisabled();
      expect(screen.getByText('Step 3: Provision')).toBeDisabled();
    });

    it('handles business status indicators', () => {
      render(
        <div>
          <ResellerButton variant='default'>● Active (123)</ResellerButton>
          <ResellerButton variant='secondary'>⏸ Suspended (45)</ResellerButton>
          <ResellerButton variant='outline'>⏹ Pending (12)</ResellerButton>
        </div>
      );

      expect(screen.getByText('●  Active (123)')).toBeInTheDocument();
      expect(screen.getByText('⏸  Suspended (45)')).toBeInTheDocument();
      expect(screen.getByText('⏹  Pending (12)')).toBeInTheDocument();
    });
  });
});
