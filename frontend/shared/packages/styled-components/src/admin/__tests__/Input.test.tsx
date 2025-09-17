/**
 * AdminInput component comprehensive tests
 * Testing admin-specific input functionality and variants
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import React from 'react';

import { AdminInput } from '../Input';

describe('AdminInput Component', () => {
  describe('Basic Rendering', () => {
    it('renders as input by default', () => {
      render(<AdminInput data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toBeInTheDocument();
      expect(input.tagName).toBe('INPUT');
      expect(input).toHaveAttribute('type', 'text');
    });

    it('renders as child component when asChild is true', () => {
      render(
        <AdminInput asChild data-testid='wrapper'>
          <textarea placeholder='Custom textarea' />
        </AdminInput>
      );

      const textarea = screen.getByPlaceholderText('Custom textarea');
      expect(textarea.tagName).toBe('TEXTAREA');
    });

    it('applies custom className', () => {
      render(<AdminInput className='custom-input' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('custom-input');
    });
  });

  describe('Input Types', () => {
    const inputTypes = [
      'text',
      'email',
      'password',
      'number',
      'tel',
      'url',
      'search',
      'date',
      'time',
    ];

    inputTypes.forEach((type) => {
      it(`renders ${type} input type`, () => {
        render(<AdminInput type={type} data-testid='input' />);

        const input = screen.getByTestId('input');
        expect(input).toHaveAttribute('type', type);
      });
    });
  });

  describe('Variants', () => {
    it('renders default variant', () => {
      render(<AdminInput variant='default' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-admin-input');
    });

    it('renders outline variant', () => {
      render(<AdminInput variant='outline' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-admin-border');
    });

    it('renders filled variant', () => {
      render(<AdminInput variant='filled' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('bg-admin-muted');
    });

    it('renders ghost variant', () => {
      render(<AdminInput variant='ghost' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-transparent');
    });
  });

  describe('Sizes', () => {
    it('renders default size', () => {
      render(<AdminInput size='default' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('h-10', 'px-3', 'py-2');
    });

    it('renders small size', () => {
      render(<AdminInput size='sm' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('h-9', 'px-3');
    });

    it('renders large size', () => {
      render(<AdminInput size='lg' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('h-11', 'px-4');
    });
  });

  describe('States', () => {
    it('renders default state', () => {
      render(<AdminInput state='default' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-admin-input');
      expect(input).toHaveAttribute('aria-invalid', 'false');
    });

    it('renders error state', () => {
      render(<AdminInput state='error' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-admin-destructive');
      expect(input).toHaveAttribute('aria-invalid', 'true');
    });

    it('renders success state', () => {
      render(<AdminInput state='success' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-admin-success');
    });

    it('renders warning state', () => {
      render(<AdminInput state='warning' data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-admin-warning');
    });

    it('handles disabled state', () => {
      render(<AdminInput disabled data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toBeDisabled();
      expect(input).toHaveClass('disabled:cursor-not-allowed');
    });

    it('handles readonly state', () => {
      render(<AdminInput readOnly data-testid='input' />);

      const input = screen.getByTestId('input');
      expect(input).toHaveAttribute('readonly');
    });
  });

  describe('Icons', () => {
    it('renders with left icon', () => {
      const LeftIcon = () => <span data-testid='left-icon'>🔍</span>;

      render(<AdminInput leftIcon={<LeftIcon />} placeholder='Search...' data-testid='input' />);

      expect(screen.getByTestId('left-icon')).toBeInTheDocument();
      expect(screen.getByTestId('input')).toBeInTheDocument();
    });

    it('renders with right icon', () => {
      const RightIcon = () => <span data-testid='right-icon'>👁</span>;

      render(<AdminInput rightIcon={<RightIcon />} type='password' data-testid='input' />);

      expect(screen.getByTestId('right-icon')).toBeInTheDocument();
      expect(screen.getByTestId('input')).toBeInTheDocument();
    });

    it('renders with both icons', () => {
      const LeftIcon = () => <span data-testid='left-icon'>🔍</span>;
      const RightIcon = () => <span data-testid='right-icon'>✓</span>;

      render(<AdminInput leftIcon={<LeftIcon />} rightIcon={<RightIcon />} data-testid='input' />);

      expect(screen.getByTestId('left-icon')).toBeInTheDocument();
      expect(screen.getByTestId('right-icon')).toBeInTheDocument();
      expect(screen.getByTestId('input')).toBeInTheDocument();
    });

    it('makes icons non-interactive', () => {
      const LeftIcon = () => <span data-testid='left-icon'>🔍</span>;

      render(<AdminInput leftIcon={<LeftIcon />} data-testid='input' />);

      const icon = screen.getByTestId('left-icon');
      expect(icon.closest('[role="presentation"]')).toBeInTheDocument();
    });
  });

  describe('Label and Description', () => {
    it('renders with label', () => {
      render(<AdminInput label='Email Address' data-testid='input' />);

      expect(screen.getByText('Email Address')).toBeInTheDocument();
      expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
    });

    it('renders with required label', () => {
      render(<AdminInput label='Required Field' required data-testid='input' />);

      const label = screen.getByText('Required Field');
      expect(label).toBeInTheDocument();
      expect(label.textContent).toContain('*');
    });

    it('renders with description', () => {
      render(
        <AdminInput
          label='Password'
          description='Must be at least 8 characters'
          data-testid='input'
        />
      );

      expect(screen.getByText('Must be at least 8 characters')).toBeInTheDocument();
    });

    it('renders with error message', () => {
      render(
        <AdminInput
          label='Email'
          error='Please enter a valid email'
          state='error'
          data-testid='input'
        />
      );

      expect(screen.getByText('Please enter a valid email')).toBeInTheDocument();
      const input = screen.getByTestId('input');
      expect(input).toHaveAttribute('aria-invalid', 'true');
    });

    it('associates input with description via aria-describedby', () => {
      render(
        <AdminInput label='Username' description='Choose a unique username' data-testid='input' />
      );

      const input = screen.getByTestId('input');
      const description = screen.getByText('Choose a unique username');

      expect(input).toHaveAttribute('aria-describedby');
      expect(description).toHaveAttribute('id');
    });
  });

  describe('Interactions', () => {
    it('handles value changes', () => {
      const handleChange = jest.fn();

      render(<AdminInput onChange={handleChange} data-testid='input' />);

      const input = screen.getByTestId('input');
      fireEvent.change(input, { target: { value: 'test value' } });

      expect(handleChange).toHaveBeenCalledTimes(1);
      expect(input).toHaveValue('test value');
    });

    it('handles controlled value', () => {
      const { rerender } = render(
        <AdminInput
          value='initial'
          onChange={() => {
            // Event handler implementation pending
          }}
          data-testid='input'
        />
      );

      let input = screen.getByTestId('input');
      expect(input).toHaveValue('initial');

      rerender(
        <AdminInput
          value='updated'
          onChange={() => {
            // Event handler implementation pending
          }}
          data-testid='input'
        />
      );

      input = screen.getByTestId('input');
      expect(input).toHaveValue('updated');
    });

    it('handles focus and blur events', () => {
      const handleFocus = jest.fn();
      const handleBlur = jest.fn();

      render(<AdminInput onFocus={handleFocus} onBlur={handleBlur} data-testid='input' />);

      const input = screen.getByTestId('input');

      fireEvent.focus(input);
      expect(handleFocus).toHaveBeenCalledTimes(1);

      fireEvent.blur(input);
      expect(handleBlur).toHaveBeenCalledTimes(1);
    });

    it('handles keyboard events', () => {
      const handleKeyDown = jest.fn();
      const handleKeyPress = jest.fn();

      render(
        <AdminInput onKeyDown={handleKeyDown} onKeyPress={handleKeyPress} data-testid='input' />
      );

      const input = screen.getByTestId('input');

      fireEvent.keyDown(input, { key: 'Enter' });
      expect(handleKeyDown).toHaveBeenCalledTimes(1);

      fireEvent.keyPress(input, { key: 'a' });
      expect(handleKeyPress).toHaveBeenCalledTimes(1);
    });

    it('does not trigger events when disabled', () => {
      const handleChange = jest.fn();
      const handleFocus = jest.fn();

      render(
        <AdminInput disabled onChange={handleChange} onFocus={handleFocus} data-testid='input' />
      );

      const input = screen.getByTestId('input');

      fireEvent.change(input, { target: { value: 'test' } });
      fireEvent.focus(input);

      expect(handleChange).not.toHaveBeenCalled();
      expect(handleFocus).not.toHaveBeenCalled();
    });
  });

  describe('Ref Forwarding', () => {
    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLInputElement>();

      render(<AdminInput ref={ref} data-testid='input' />);

      expect(ref.current).toBeInstanceOf(HTMLInputElement);
      expect(ref.current).toBe(screen.getByTestId('input'));
    });

    it('allows programmatic focus', () => {
      const ref = React.createRef<HTMLInputElement>();

      render(<AdminInput ref={ref} data-testid='input' />);

      ref.current?.focus();
      expect(ref.current).toHaveFocus();
    });
  });

  describe('Accessibility', () => {
    it('should be accessible', async () => {
      const { container } = render(
        <AdminInput label='Accessible Input' description='This is accessible' />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should be accessible with error state', async () => {
      const { container } = render(
        <AdminInput label='Error Input' error='This field has an error' state='error' />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('provides proper ARIA attributes', () => {
      render(
        <AdminInput
          label='Test Input'
          description='Test description'
          error='Test error'
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

    it('supports custom ARIA attributes', () => {
      render(
        <AdminInput
          aria-label='Custom label'
          aria-describedby='custom-description'
          data-testid='input'
        />
      );

      const input = screen.getByTestId('input');
      expect(input).toHaveAttribute('aria-label', 'Custom label');
      expect(input).toHaveAttribute('aria-describedby', 'custom-description');
    });
  });

  describe('Edge Cases', () => {
    it('handles empty props gracefully', () => {
      render(<AdminInput />);

      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });

    it('handles null and undefined values', () => {
      const { rerender } = render(
        <AdminInput
          value={null as unknown}
          onChange={() => {
            // Event handler implementation pending
          }}
          data-testid='input'
        />
      );

      let input = screen.getByTestId('input');
      expect(input).toHaveValue('');

      rerender(
        <AdminInput
          value={undefined}
          onChange={() => {
            // Event handler implementation pending
          }}
          data-testid='input'
        />
      );

      input = screen.getByTestId('input');
      expect(input).toHaveValue('');
    });

    it('handles very long values', () => {
      const longValue = 'a'.repeat(1000);

      render(
        <AdminInput
          value={longValue}
          onChange={() => {
            // Event handler implementation pending
          }}
          data-testid='input'
        />
      );

      const input = screen.getByTestId('input');
      expect(input).toHaveValue(longValue);
    });

    it('handles special characters in values', () => {
      const specialValue = '!@#$%^&*()_+-=[]{
    // Implementation pending
  }|;:,.<>?';

      render(
        <AdminInput
          value=specialValue
          onChange=() => 
          data-testid='input'
        />
      );

      const input = screen.getByTestId('input');
      expect(input).toHaveValue(specialValue);
    });
  });

  describe('Validation', () => {
    it('supports HTML5 validation attributes', () => {
      render(
        <AdminInput
          type='email'
          required
          minLength={5}
          maxLength={50}
          pattern='[a-z]+@[a-z]+\.[a-z]+'
          data-testid='input'
        />
      );

      const input = screen.getByTestId('input');
      expect(input).toHaveAttribute('required');
      expect(input).toHaveAttribute('minlength', '5');
      expect(input).toHaveAttribute('maxlength', '50');
      expect(input).toHaveAttribute('pattern', '[a-z]+@[a-z]+.[a-z]+');
    });

    it('shows validation state in UI', () => {
      render(
        <AdminInput
          label='Email'
          type='email'
          value='invalid-email'
          state='error'
          error='Please enter a valid email address'
          data-testid='input'
        />
      );

      const input = screen.getByTestId('input');
      expect(input).toHaveClass('border-admin-destructive');
      expect(input).toHaveAttribute('aria-invalid', 'true');
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('renders efficiently with many props', () => {
      const startTime = performance.now();

      render(
        <AdminInput
          label='Performance Test'
          description='Testing performance'
          variant='outline'
          size='lg'
          state='success'
          leftIcon={<span>🔍</span>}
          rightIcon={<span>✓</span>}
          className='performance-test'
          placeholder='Enter text...'
          value='test value'
          onChange={() => {
            // Event handler implementation pending
          }}
          onFocus={() => {
            // Event handler implementation pending
          }}
          onBlur={() => {
            // Event handler implementation pending
          }}
          required
          data-testid='perf-input'
        />
      );

      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(10);
      expect(screen.getByTestId('perf-input')).toBeInTheDocument();
    });

    it('handles rapid value changes efficiently', () => {
      const handleChange = jest.fn();

      render(<AdminInput onChange={handleChange} data-testid='input' />);

      const input = screen.getByTestId('input');

      // Simulate rapid typing
      const startTime = performance.now();
      for (let i = 0; i < 100; i++) {
        fireEvent.change(input, { target: { value: `text${i}` } });
      }
      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(100);
      expect(handleChange).toHaveBeenCalledTimes(100);
    });
  });
});
