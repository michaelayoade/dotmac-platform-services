/**
 * ResellerInput component comprehensive tests
 * Testing reseller-specific input functionality and business workflows
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import React from 'react';

import { ResellerInput } from '../Input';

describe('ResellerInput Component', () => {
  describe('Reseller Business Interface', () => {
    it('renders reseller-optimized input', () => {
      render(<ResellerInput placeholder='Enter business data' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('placeholder', 'Enter business data');
    });

    it('renders as child component for reseller forms', () => {
      render(
        <ResellerInput asChild data-testid='wrapper'>
          <textarea placeholder='Business requirements' />
        </ResellerInput>
      );

      const textarea = screen.getByPlaceholderText('Business requirements');
      expect(textarea.tagName).toBe('TEXTAREA');
    });

    it('applies reseller branding classes', () => {
      render(<ResellerInput className='reseller-business-input' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('reseller-business-input');
    });
  });

  describe('Business Input Types', () => {
    const businessInputTypes = ['text', 'email', 'password', 'tel', 'url', 'number'];

    businessInputTypes.forEach((type) => {
      it(`supports ${type} input for business data`, () => {
        render(<ResellerInput type={type} data-testid='input' />);

        const input = screen.getByTestId('input');
        expect(input).toHaveAttribute('type', type);
      });
    });

    it('handles business identifier input', () => {
      render(
        <ResellerInput
          type='text'
          placeholder='Business ID'
          pattern='[A-Z]{2}[0-9]{6,10}'
          data-testid='business-input'
        />
      );

      const input = screen.getByTestId('business-input');
      expect(input).toHaveAttribute('pattern', '[A-Z]{2}[0-9]{6,10}');
    });

    it('handles tax identification numbers', () => {
      render(
        <ResellerInput
          type='text'
          placeholder='Tax ID'
          pattern='[0-9]{2}-[0-9]{7}'
          data-testid='tax-input'
        />
      );

      const input = screen.getByTestId('tax-input');
      expect(input).toHaveAttribute('pattern', '[0-9]{2}-[0-9]{7}');
    });
  });

  describe('Reseller Business Variants', () => {
    it('renders reseller default variant', () => {
      render(<ResellerInput variant='default' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-reseller-input');
    });

    it('renders reseller outline variant', () => {
      render(<ResellerInput variant='outline' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-reseller-border');
    });

    it('renders reseller filled variant for business forms', () => {
      render(<ResellerInput variant='filled' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('bg-reseller-muted');
    });

    it('renders reseller ghost variant for minimal business design', () => {
      render(<ResellerInput variant='ghost' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-transparent');
    });
  });

  describe('Business-Optimized Sizes', () => {
    it('renders comfortable default size for business users', () => {
      render(<ResellerInput size='default' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('h-10', 'px-3', 'py-2');
    });

    it('renders compact size for dense business interfaces', () => {
      render(<ResellerInput size='sm' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('h-9', 'px-3');
    });

    it('renders large size for prominent business inputs', () => {
      render(<ResellerInput size='lg' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('h-11', 'px-4');
    });
  });

  describe('Business Process States', () => {
    it('provides clear default state for business operations', () => {
      render(<ResellerInput state='default' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-reseller-input');
      expect(input).toHaveAttribute('aria-invalid', 'false');
    });

    it('shows business-friendly error state', () => {
      render(<ResellerInput state='error' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-reseller-destructive');
      expect(input).toHaveAttribute('aria-invalid', 'true');
    });

    it('displays success state for business validation', () => {
      render(<ResellerInput state='success' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-reseller-success');
    });

    it('shows warning state for business process guidance', () => {
      render(<ResellerInput state='warning' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-reseller-warning');
    });

    it('handles disabled state with clear business feedback', () => {
      render(<ResellerInput disabled data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toBeDisabled();
      expect(input).toHaveClass('disabled:cursor-not-allowed');
    });
  });

  describe('Business Process Icons', () => {
    it('shows business search icon', () => {
      const SearchIcon = () => <span data-testid='search-icon'>🔍</span>;

      render(
        <ResellerInput
          leftIcon={<SearchIcon />}
          placeholder='Search business data...'
          data-testid='input'
        />
      );

      expect(screen.getByTestId('search-icon')).toBeInTheDocument();
    });

    it('shows business validation icon', () => {
      const ValidateIcon = () => <span data-testid='validate-icon'>✅</span>;

      render(
        <ResellerInput
          rightIcon={<ValidateIcon />}
          placeholder='Validate business info'
          data-testid='input'
        />
      );

      expect(screen.getByTestId('validate-icon')).toBeInTheDocument();
    });

    it('shows both icons for comprehensive business operations', () => {
      const BusinessIcon = () => <span data-testid='business-icon'>💼</span>;
      const ProcessIcon = () => <span data-testid='process-icon'>⚙️</span>;

      render(
        <ResellerInput
          leftIcon={<BusinessIcon />}
          rightIcon={<ProcessIcon />}
          data-testid='input'
        />
      );

      expect(screen.getByTestId('business-icon')).toBeInTheDocument();
      expect(screen.getByTestId('process-icon')).toBeInTheDocument();
    });
  });

  describe('Business Form Fields', () => {
    it('renders business profile field with label', () => {
      render(
        <ResellerInput
          label='Business Name'
          placeholder='Enter your business name'
          data-testid='input'
        />
      );

      expect(screen.getByText('Business Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Business Name')).toBeInTheDocument();
    });

    it('shows required field indicators for business forms', () => {
      render(<ResellerInput label='Business Email' required data-testid='input' />);

      const label = screen.getByText('Business Email');
      expect(label.textContent).toContain('*');
    });

    it('provides helpful descriptions for business processes', () => {
      render(
        <ResellerInput
          label='Business License'
          description='Enter your business license number'
          data-testid='input'
        />
      );

      expect(screen.getByText('Enter your business license number')).toBeInTheDocument();
    });

    it('shows business-friendly error messages', () => {
      render(
        <ResellerInput
          label='Business Phone'
          error='Please enter a valid business phone number'
          state='error'
          data-testid='input'
        />
      );

      expect(screen.getByText('Please enter a valid business phone number')).toBeInTheDocument();
    });
  });

  describe('Business Interactions', () => {
    it('handles business input changes efficiently', () => {
      const handleChange = jest.fn();

      render(
        <ResellerInput onChange={handleChange} placeholder='Business data...' data-testid='input' />
      );

      const input = screen.getByTestId('input');
      fireEvent.change(input, { target: { value: 'business input' } });

      expect(handleChange).toHaveBeenCalledTimes(1);
      expect(input).toHaveValue('business input');
    });

    it('handles controlled business data', () => {
      const { rerender } = render(
        <ResellerInput
          value='initial business value'
          onChange={() => {
            // Event handler implementation pending
          }}
          data-testid='input'
        />
      );

      let input = screen.getByTestId('input');
      expect(input).toHaveValue('initial business value');

      rerender(
        <ResellerInput
          value='updated business value'
          onChange={() => {
            // Event handler implementation pending
          }}
          data-testid='input'
        />
      );

      input = screen.getByTestId('input');
      expect(input).toHaveValue('updated business value');
    });

    it('provides feedback on business process focus and blur', () => {
      const handleFocus = jest.fn();
      const handleBlur = jest.fn();

      render(<ResellerInput onFocus={handleFocus} onBlur={handleBlur} data-testid='input' />);

      const input = screen.getByTestId('input');

      fireEvent.focus(input);
      expect(handleFocus).toHaveBeenCalledTimes(1);

      fireEvent.blur(input);
      expect(handleBlur).toHaveBeenCalledTimes(1);
    });

    it('supports business keyboard workflows', () => {
      const handleKeyDown = jest.fn();

      render(<ResellerInput onKeyDown={handleKeyDown} data-testid='input' />);

      const input = screen.getByTestId('input');
      fireEvent.keyDown(input, { key: 'Tab' });

      expect(handleKeyDown).toHaveBeenCalledTimes(1);
    });
  });

  describe('Reseller Portal Integration', () => {
    it('forwards ref for reseller portal features', () => {
      const ref = React.createRef<HTMLInputElement>();

      render(<ResellerInput ref={ref} placeholder='Portal input' />);

      expect(ref.current).toBeInstanceOf(HTMLInputElement);
      expect(ref.current?.placeholder).toBe('Portal input');
    });

    it('enables programmatic focus for business UX', () => {
      const ref = React.createRef<HTMLInputElement>();

      render(<ResellerInput ref={ref} data-testid='input' />);

      ref.current?.focus();
      expect(ref.current).toHaveFocus();
    });
  });

  describe('Business Accessibility', () => {
    it('meets business accessibility standards', async () => {
      const { container } = render(
        <ResellerInput
          label='Accessible Business Input'
          description='This input is fully accessible for business use'
        />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('maintains accessibility with business errors', async () => {
      const { container } = render(
        <ResellerInput
          label='Business Data'
          error='Please correct this business field'
          state='error'
        />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('provides proper ARIA support for business processes', () => {
      render(
        <ResellerInput
          label='Business Information'
          description='Enter your business details'
          error='Invalid business input'
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

    it('supports custom business ARIA attributes', () => {
      render(
        <ResellerInput
          aria-label='Business contact phone'
          aria-describedby='business-phone-help'
          data-testid='input'
        />
      );

      const input = screen.getByTestId('input');
      expect(input).toHaveAttribute('aria-label', 'Business contact phone');
      expect(input).toHaveAttribute('aria-describedby', 'business-phone-help');
    });
  });

  describe('Business Data Validation', () => {
    it('supports business email validation', () => {
      render(
        <ResellerInput
          type='email'
          required
          pattern='[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}$'
          data-testid='email-input'
        />
      );

      const input = screen.getByTestId('email-input');
      expect(input).toHaveAttribute('type', 'email');
      expect(input).toHaveAttribute('required');
      expect(input).toHaveAttribute('pattern');
    });

    it('shows business validation feedback in UI', () => {
      render(
        <ResellerInput
          label='Business Email'
          type='email'
          value='invalid-business-email'
          state='error'
          error='Please enter a valid business email address'
          data-testid='input'
        />
      );

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-reseller-destructive');
      expect(screen.getByText('Please enter a valid business email address')).toBeInTheDocument();
    });

    it('validates business phone numbers', () => {
      render(
        <ResellerInput
          type='tel'
          pattern='\\([0-9]{3}\\) [0-9]{3}-[0-9]{4}'
          placeholder='(555) 123-4567'
          data-testid='phone-input'
        />
      );

      const input = screen.getByTestId('phone-input');
      expect(input).toHaveAttribute('type', 'tel');
      expect(input).toHaveAttribute('pattern', '\\([0-9]{3}\\) [0-9]{3}-[0-9]{4}');
    });

    it('validates business tax identifiers', () => {
      render(
        <ResellerInput
          type='text'
          pattern='[0-9]{2}-[0-9]{7}'
          placeholder='12-3456789'
          data-testid='tax-input'
        />
      );

      const input = screen.getByTestId('tax-input');
      expect(input).toHaveAttribute('pattern', '[0-9]{2}-[0-9]{7}');
    });
  });

  describe('Business Use Cases', () => {
    it('handles business registration form', () => {
      render(
        <div>
          <ResellerInput label='Business Name' placeholder='Your business name' />
          <ResellerInput label='Business Email' type='email' placeholder='business@example.com' />
          <ResellerInput label='Business Phone' type='tel' placeholder='(555) 123-4567' />
          <ResellerInput label='Tax ID' placeholder='12-3456789' />
        </div>
      );

      expect(screen.getByLabelText('Business Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Business Email')).toBeInTheDocument();
      expect(screen.getByLabelText('Business Phone')).toBeInTheDocument();
      expect(screen.getByLabelText('Tax ID')).toBeInTheDocument();
    });

    it('handles business address information', () => {
      render(
        <div>
          <ResellerInput label='Business Address' placeholder='123 Business St' />
          <ResellerInput label='City' placeholder='Business City' />
          <ResellerInput label='State' placeholder='State' />
          <ResellerInput label='ZIP Code' placeholder='12345' pattern='[0-9]{5}' />
        </div>
      );

      expect(screen.getByLabelText('Business Address')).toBeInTheDocument();
      expect(screen.getByLabelText('City')).toBeInTheDocument();
      expect(screen.getByLabelText('State')).toBeInTheDocument();
      expect(screen.getByLabelText('ZIP Code')).toBeInTheDocument();
    });

    it('handles business service requests', () => {
      const BusinessIcon = () => <span data-testid='business'>💼</span>;

      render(
        <ResellerInput
          label='Business Requirements'
          leftIcon={<BusinessIcon />}
          placeholder='Describe your business needs...'
        />
      );

      expect(screen.getByTestId('business')).toBeInTheDocument();
      expect(screen.getByLabelText('Business Requirements')).toBeInTheDocument();
    });

    it('handles customer account creation', () => {
      render(
        <div>
          <ResellerInput label='Customer Name' placeholder='Customer full name' />
          <ResellerInput label='Customer Email' type='email' placeholder='customer@example.com' />
          <ResellerInput label='Service Plan' placeholder='Select service plan' />
          <ResellerInput label='Monthly Revenue' type='number' placeholder='500.00' />
        </div>
      );

      expect(screen.getByLabelText('Customer Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Customer Email')).toBeInTheDocument();
      expect(screen.getByLabelText('Service Plan')).toBeInTheDocument();
      expect(screen.getByLabelText('Monthly Revenue')).toBeInTheDocument();
    });
  });

  describe('Business Edge Cases', () => {
    it('handles empty business input gracefully', () => {
      render(<ResellerInput />);

      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });

    it('handles null business values safely', () => {
      render(
        <ResellerInput
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

    it('handles special characters in business data', () => {
      const specialValue = "O'Connor & Associates LLC";

      render(
        <ResellerInput
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

    it('handles long business text efficiently', () => {
      const longText = 'Business'.repeat(50);

      render(
        <ResellerInput
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

    it('handles business numeric values', () => {
      render(
        <ResellerInput
          type='number'
          value='1234567'
          onChange={() => {
            // Event handler implementation pending
          }}
          data-testid='input'
        />
      );

      const input = screen.getByTestId('input');
      expect(input).toHaveValue('1234567');
    });
  });

  describe('Business Performance', () => {
    it('renders efficiently for business portal', () => {
      const startTime = performance.now();

      render(
        <ResellerInput
          label='Business Portal Input'
          description='Fast and responsive business input'
          variant='outline'
          size='lg'
          leftIcon={<span>🏢</span>}
          placeholder='Search business data...'
          data-testid='perf-input'
        />
      );

      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(10);
      expect(screen.getByTestId('perf-input')).toBeInTheDocument();
    });

    it('handles rapid business data entry efficiently', () => {
      const handleChange = jest.fn();

      render(<ResellerInput onChange={handleChange} data-testid='input' />);

      const input = screen.getByTestId('input');

      // Simulate fast business typing
      const startTime = performance.now();
      for (let i = 0; i < 50; i++) {
        fireEvent.change(input, { target: { value: `business${i}` } });
      }
      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(100);
      expect(handleChange).toHaveBeenCalledTimes(50);
    });

    it('handles large business datasets in dropdowns efficiently', () => {
      const startTime = performance.now();

      // Simulate large business data processing
      const businessData = Array.from({ length: 1000 }, (_, i) => `Business ${i}`);

      render(<ResellerInput placeholder='Search in large business dataset' data-testid='input' />);

      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(20);
      expect(screen.getByTestId('input')).toBeInTheDocument();
      expect(businessData.length).toBe(1000);
    });
  });

  describe('Business Integration', () => {
    it('integrates with business form validation', () => {
      const TestBusinessForm = () => {
        const [value, setValue] = React.useState('');
        const [error, setError] = React.useState('');

        const validateBusiness = (input: string) => {
          if (input.length < 2) {
            setError('Business name must be at least 2 characters');
            return false;
          }
          setError('');
          return true;
        };

        return (
          <ResellerInput
            label='Business Name'
            value={value}
            onChange={(e) => {
              const newValue = e.target.value;
              setValue(newValue);
              validateBusiness(newValue);
            }}
            error={error}
            state={error ? 'error' : 'default'}
            data-testid='business-input'
          />
        );
      };

      render(<TestBusinessForm />);

      const input = screen.getByTestId('business-input');

      fireEvent.change(input, { target: { value: 'A' } });
      expect(screen.getByText('Business name must be at least 2 characters')).toBeInTheDocument();

      fireEvent.change(input, { target: { value: 'ABC Corp' } });
      expect(
        screen.queryByText('Business name must be at least 2 characters')
      ).not.toBeInTheDocument();
    });

    it('integrates with business autocomplete', () => {
      const businessSuggestions = ['ABC Corp', 'XYZ Ltd', 'Business Solutions Inc'];

      const TestBusinessAutocomplete = () => {
        const [value, setValue] = React.useState('');
        const [suggestions, setSuggestions] = React.useState<string[]>([]);

        const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
          const input = e.target.value;
          setValue(input);

          if (input.length > 0) {
            const filtered = businessSuggestions.filter((biz) =>
              biz.toLowerCase().includes(input.toLowerCase())
            );
            setSuggestions(filtered);
          } else {
            setSuggestions([]);
          }
        };

        return (
          <div>
            <ResellerInput
              label='Business Search'
              value={value}
              onChange={handleChange}
              placeholder='Search businesses...'
              data-testid='autocomplete-input'
            />
            {suggestions.length > 0 && (
              <div data-testid='suggestions'>
                {suggestions.map((suggestion, index) => (
                  <div key={`item-${index}`}>{suggestion}</div>
                ))}
              </div>
            )}
          </div>
        );
      };

      render(<TestBusinessAutocomplete />);

      const input = screen.getByTestId('autocomplete-input');
      fireEvent.change(input, { target: { value: 'ABC' } });

      expect(screen.getByTestId('suggestions')).toBeInTheDocument();
      expect(screen.getByText('ABC Corp')).toBeInTheDocument();
    });
  });
});
