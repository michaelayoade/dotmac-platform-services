/**
 * CustomerInput component comprehensive tests
 * Testing customer-specific input functionality and user experience
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import React from 'react';

import { CustomerInput } from '../Input';

describe('CustomerInput Component', () => {
  describe('Basic Customer Experience', () => {
    it('renders customer-friendly input', () => {
      render(<CustomerInput placeholder='Enter your information' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('placeholder', 'Enter your information');
    });

    it('renders as child component for customer forms', () => {
      render(
        <CustomerInput asChild data-testid='wrapper'>
          <textarea placeholder='Tell us about your needs' />
        </CustomerInput>
      );

      const textarea = screen.getByPlaceholderText('Tell us about your needs');
      expect(textarea.tagName).toBe('TEXTAREA');
    });

    it('applies customer branding classes', () => {
      render(<CustomerInput className='customer-input' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('customer-input');
    });
  });

  describe('Customer Input Types', () => {
    const customerInputTypes = ['text', 'email', 'password', 'tel', 'url'];

    customerInputTypes.forEach((type) => {
      it(`supports ${type} input for customer data`, () => {
        render(<CustomerInput type={type} data-testid='input' />);

        const input = screen.getByTestId('input');
        expect(input).toHaveAttribute('type', type);
      });
    });

    it('handles customer account number input', () => {
      render(
        <CustomerInput
          type='text'
          placeholder='Account Number'
          pattern='[0-9]{8,12}'
          data-testid='account-input'
        />
      );

      const input = screen.getByTestId('account-input');
      expect(input).toHaveAttribute('pattern', '[0-9]{8,12}');
    });
  });

  describe('Customer-Specific Variants', () => {
    it('renders customer default variant', () => {
      render(<CustomerInput variant='default' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-customer-input');
    });

    it('renders customer outline variant', () => {
      render(<CustomerInput variant='outline' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-customer-border');
    });

    it('renders customer filled variant for better UX', () => {
      render(<CustomerInput variant='filled' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('bg-customer-muted');
    });

    it('renders customer ghost variant for minimal design', () => {
      render(<CustomerInput variant='ghost' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-transparent');
    });
  });

  describe('Customer-Friendly Sizes', () => {
    it('renders comfortable default size for customers', () => {
      render(<CustomerInput size='default' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('h-10', 'px-3', 'py-2');
    });

    it('renders compact size for mobile customers', () => {
      render(<CustomerInput size='sm' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('h-9', 'px-3');
    });

    it('renders large size for important customer inputs', () => {
      render(<CustomerInput size='lg' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('h-11', 'px-4');
    });
  });

  describe('Customer Experience States', () => {
    it('provides clear default state for customers', () => {
      render(<CustomerInput state='default' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-customer-input');
      expect(input).toHaveAttribute('aria-invalid', 'false');
    });

    it('shows customer-friendly error state', () => {
      render(<CustomerInput state='error' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-customer-destructive');
      expect(input).toHaveAttribute('aria-invalid', 'true');
    });

    it('displays success state for customer validation', () => {
      render(<CustomerInput state='success' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-customer-success');
    });

    it('shows warning state for customer guidance', () => {
      render(<CustomerInput state='warning' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-customer-warning');
    });

    it('handles disabled state with clear customer feedback', () => {
      render(<CustomerInput disabled data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toBeDisabled();
      expect(input).toHaveClass('disabled:cursor-not-allowed');
    });
  });

  describe('Customer Support Icons', () => {
    it('shows search icon for customer queries', () => {
      const SearchIcon = () => <span data-testid='search-icon'>🔍</span>;

      render(
        <CustomerInput
          leftIcon={<SearchIcon />}
          placeholder='Search services...'
          data-testid='input'
        />
      );

      expect(screen.getByTestId('search-icon')).toBeInTheDocument();
    });

    it('shows help icon for customer assistance', () => {
      const HelpIcon = () => <span data-testid='help-icon'>❓</span>;

      render(
        <CustomerInput rightIcon={<HelpIcon />} placeholder='Need help?' data-testid='input' />
      );

      expect(screen.getByTestId('help-icon')).toBeInTheDocument();
    });

    it('shows both icons for comprehensive customer support', () => {
      const SearchIcon = () => <span data-testid='search-icon'>🔍</span>;
      const ClearIcon = () => <span data-testid='clear-icon'>✖</span>;

      render(
        <CustomerInput leftIcon={<SearchIcon />} rightIcon={<ClearIcon />} data-testid='input' />
      );

      expect(screen.getByTestId('search-icon')).toBeInTheDocument();
      expect(screen.getByTestId('clear-icon')).toBeInTheDocument();
    });
  });

  describe('Customer Form Fields', () => {
    it('renders customer profile field with label', () => {
      render(
        <CustomerInput label='Full Name' placeholder='Enter your full name' data-testid='input' />
      );

      expect(screen.getByText('Full Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Full Name')).toBeInTheDocument();
    });

    it('shows required field indicators for customers', () => {
      render(<CustomerInput label='Email Address' required data-testid='input' />);

      const label = screen.getByText('Email Address');
      expect(label.textContent).toContain('*');
    });

    it('provides helpful descriptions for customers', () => {
      render(
        <CustomerInput
          label='Account Number'
          description='Find this on your monthly bill'
          data-testid='input'
        />
      );

      expect(screen.getByText('Find this on your monthly bill')).toBeInTheDocument();
    });

    it('shows customer-friendly error messages', () => {
      render(
        <CustomerInput
          label='Phone Number'
          error='Please enter a valid phone number'
          state='error'
          data-testid='input'
        />
      );

      expect(screen.getByText('Please enter a valid phone number')).toBeInTheDocument();
    });
  });

  describe('Customer Interactions', () => {
    it('handles customer input changes smoothly', () => {
      const handleChange = jest.fn();

      render(
        <CustomerInput onChange={handleChange} placeholder='Type here...' data-testid='input' />
      );

      const input = screen.getByTestId('input');
      fireEvent.change(input, { target: { value: 'customer input' } });

      expect(handleChange).toHaveBeenCalledTimes(1);
      expect(input).toHaveValue('customer input');
    });

    it('handles controlled customer data', () => {
      const { rerender } = render(
        <CustomerInput
          value='initial value'
          onChange={() => {
            // Event handler implementation pending
          }}
          data-testid='input'
        />
      );

      let input = screen.getByTestId('input');
      expect(input).toHaveValue('initial value');

      rerender(
        <CustomerInput
          value='updated value'
          onChange={() => {
            // Event handler implementation pending
          }}
          data-testid='input'
        />
      );

      input = screen.getByTestId('input');
      expect(input).toHaveValue('updated value');
    });

    it('provides feedback on customer focus and blur', () => {
      const handleFocus = jest.fn();
      const handleBlur = jest.fn();

      render(<CustomerInput onFocus={handleFocus} onBlur={handleBlur} data-testid='input' />);

      const input = screen.getByTestId('input');

      fireEvent.focus(input);
      expect(handleFocus).toHaveBeenCalledTimes(1);

      fireEvent.blur(input);
      expect(handleBlur).toHaveBeenCalledTimes(1);
    });

    it('supports customer keyboard navigation', () => {
      const handleKeyDown = jest.fn();

      render(<CustomerInput onKeyDown={handleKeyDown} data-testid='input' />);

      const input = screen.getByTestId('input');
      fireEvent.keyDown(input, { key: 'Tab' });

      expect(handleKeyDown).toHaveBeenCalledTimes(1);
    });
  });

  describe('Customer Portal Integration', () => {
    it('forwards ref for customer portal features', () => {
      const ref = React.createRef<HTMLInputElement>();

      render(<CustomerInput ref={ref} placeholder='Portal input' />);

      expect(ref.current).toBeInstanceOf(HTMLInputElement);
      expect(ref.current?.placeholder).toBe('Portal input');
    });

    it('enables programmatic focus for customer UX', () => {
      const ref = React.createRef<HTMLInputElement>();

      render(<CustomerInput ref={ref} data-testid='input' />);

      ref.current?.focus();
      expect(ref.current).toHaveFocus();
    });
  });

  describe('Customer Accessibility', () => {
    it('meets customer accessibility standards', async () => {
      const { container } = render(
        <CustomerInput
          label='Accessible Customer Input'
          description='This input is fully accessible'
        />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('maintains accessibility with customer errors', async () => {
      const { container } = render(
        <CustomerInput label='Customer Data' error='Please correct this field' state='error' />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('provides proper ARIA support for customers', () => {
      render(
        <CustomerInput
          label='Customer Information'
          description='Enter your details'
          error='Invalid input'
          state='error'
          required
          data-testid='input'
        />
      );

      const input = screen.getByTestId('input');
      expect(input).toHaveAttribute('aria-invalid', 'true');
      expect(input).toHaveAttribute('aria-required', 'true');
      expect(input).toHaveAttribute('aria-describedby');
    });

    it('supports custom customer ARIA attributes', () => {
      render(
        <CustomerInput
          aria-label='Customer service phone'
          aria-describedby='phone-help'
          data-testid='input'
        />
      );

      const input = screen.getByTestId('input');
      expect(input).toHaveAttribute('aria-label', 'Customer service phone');
      expect(input).toHaveAttribute('aria-describedby', 'phone-help');
    });
  });

  describe('Customer Data Validation', () => {
    it('supports customer email validation', () => {
      render(
        <CustomerInput
          type='email'
          required
          pattern='[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
          data-testid='email-input'
        />
      );

      const input = screen.getByTestId('email-input');
      expect(input).toHaveAttribute('type', 'email');
      expect(input).toHaveAttribute('required');
      expect(input).toHaveAttribute('pattern');
    });

    it('shows customer validation feedback in UI', () => {
      render(
        <CustomerInput
          label='Customer Email'
          type='email'
          value='invalid-email'
          state='error'
          error='Please enter a valid email address'
          data-testid='input'
        />
      );

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-customer-destructive');
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
    });

    it('validates customer phone numbers', () => {
      render(
        <CustomerInput
          type='tel'
          pattern='[0-9]{3}-[0-9]{3}-[0-9]{4}'
          placeholder='123-456-7890'
          data-testid='phone-input'
        />
      );

      const input = screen.getByTestId('phone-input');
      expect(input).toHaveAttribute('type', 'tel');
      expect(input).toHaveAttribute('pattern', '[0-9]{3}-[0-9]{3}-[0-9]{4}');
    });
  });

  describe('Customer Use Cases', () => {
    it('handles customer contact form', () => {
      render(
        <div>
          <CustomerInput label='Name' placeholder='Your full name' />
          <CustomerInput label='Email' type='email' placeholder='your.email@example.com' />
          <CustomerInput label='Phone' type='tel' placeholder='(555) 123-4567' />
          <CustomerInput label='Account Number' placeholder='12345678' />
        </div>
      );

      expect(screen.getByLabelText('Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Email')).toBeInTheDocument();
      expect(screen.getByLabelText('Phone')).toBeInTheDocument();
      expect(screen.getByLabelText('Account Number')).toBeInTheDocument();
    });

    it('handles customer billing information', () => {
      render(
        <div>
          <CustomerInput label='Billing Address' placeholder='123 Main St' />
          <CustomerInput label='City' placeholder='Your city' />
          <CustomerInput label='ZIP Code' placeholder='12345' pattern='[0-9]{5}' />
        </div>
      );

      expect(screen.getByLabelText('Billing Address')).toBeInTheDocument();
      expect(screen.getByLabelText('City')).toBeInTheDocument();
      expect(screen.getByLabelText('ZIP Code')).toBeInTheDocument();
    });

    it('handles customer service requests', () => {
      const HelpIcon = () => <span data-testid='help'>❓</span>;

      render(
        <CustomerInput
          label='How can we help?'
          leftIcon={<HelpIcon />}
          placeholder='Describe your issue...'
        />
      );

      expect(screen.getByTestId('help')).toBeInTheDocument();
      expect(screen.getByLabelText('How can we help?')).toBeInTheDocument();
    });
  });

  describe('Customer Experience Edge Cases', () => {
    it('handles empty customer input gracefully', () => {
      render(<CustomerInput />);

      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });

    it('handles null customer values safely', () => {
      render(
        <CustomerInput
          value={null as unknown}
          onChange={() => {
            // Event handler implementation pending
          }}
          data-testid='input'
        />
      );

      const input = screen.getByTestId('input');
      expect(input).toHaveValue('');
    });

    it('handles special characters in customer data', () => {
      const specialValue = "O'Connor & Associates";

      render(
        <CustomerInput
          value={specialValue}
          onChange={() => {
            // Event handler implementation pending
          }}
          data-testid='input'
        />
      );

      const input = screen.getByTestId('input');
      expect(input).toHaveValue(specialValue);
    });

    it('handles long customer text efficiently', () => {
      const longText = 'Customer'.repeat(100);

      render(
        <CustomerInput
          value={longText}
          onChange={() => {
            // Event handler implementation pending
          }}
          data-testid='input'
        />
      );

      const input = screen.getByTestId('input');
      expect(input).toHaveValue(longText);
    });
  });

  describe('Customer Performance', () => {
    it('renders efficiently for customer portal', () => {
      const startTime = performance.now();

      render(
        <CustomerInput
          label='Customer Portal Input'
          description='Fast and responsive'
          variant='outline'
          size='lg'
          leftIcon={<span>🔍</span>}
          placeholder='Search customer data...'
          data-testid='perf-input'
        />
      );

      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(10);
      expect(screen.getByTestId('perf-input')).toBeInTheDocument();
    });

    it('handles rapid customer typing efficiently', () => {
      const handleChange = jest.fn();

      render(<CustomerInput onChange={handleChange} data-testid='input' />);

      const input = screen.getByTestId('input');

      // Simulate fast customer typing
      const startTime = performance.now();
      for (let i = 0; i < 50; i++) {
        fireEvent.change(input, { target: { value: `customer${i}` } });
      }
      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(100);
      expect(handleChange).toHaveBeenCalledTimes(50);
    });
  });
});
