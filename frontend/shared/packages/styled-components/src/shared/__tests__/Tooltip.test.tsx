/**
 * Tooltip component tests
 * Testing tooltip positioning, triggers, and accessibility
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { axe } from 'jest-axe';
import React from 'react';

import { Tooltip } from '../Tooltip';

describe('Tooltip Component', () => {
  describe('Basic Rendering', () => {
    it('renders tooltip trigger', () => {
      render(
        <Tooltip content='Tooltip text'>
          <button type='button'>Hover me</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button', { name: /hover me/i });
      expect(trigger).toBeInTheDocument();
    });

    it('does not show tooltip content initially', () => {
      render(
        <Tooltip content='Tooltip text'>
          <button type='button'>Hover me</button>
        </Tooltip>
      );

      expect(screen.queryByText('Tooltip text')).not.toBeInTheDocument();
    });

    it('accepts custom className for trigger', () => {
      render(
        <Tooltip content='Tooltip text' className='custom-tooltip'>
          <button type='button'>Hover me</button>
        </Tooltip>
      );

      // Tooltip wrapper should have custom class
      const trigger = screen.getByRole('button').parentElement;
      expect(trigger).toHaveClass('custom-tooltip');
    });
  });

  describe('Hover Interactions', () => {
    it('shows tooltip on mouse enter', async () => {
      render(
        <Tooltip content='Tooltip text'>
          <button type='button'>Hover me</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');
      fireEvent.mouseEnter(trigger);

      await waitFor(() => {
        expect(screen.getByText('Tooltip text')).toBeInTheDocument();
      });
    });

    it('hides tooltip on mouse leave', async () => {
      render(
        <Tooltip content='Tooltip text'>
          <button type='button'>Hover me</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');

      fireEvent.mouseEnter(trigger);
      await waitFor(() => {
        expect(screen.getByText('Tooltip text')).toBeInTheDocument();
      });

      fireEvent.mouseLeave(trigger);
      await waitFor(() => {
        expect(screen.queryByText('Tooltip text')).not.toBeInTheDocument();
      });
    });

    it('respects hover delay', async () => {
      render(
        <Tooltip content='Tooltip text' delay={200}>
          <button type='button'>Hover me</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');
      fireEvent.mouseEnter(trigger);

      // Should not appear immediately
      expect(screen.queryByText('Tooltip text')).not.toBeInTheDocument();

      // Should appear after delay
      await waitFor(
        () => {
          expect(screen.getByText('Tooltip text')).toBeInTheDocument();
        },
        { timeout: 300 }
      );
    });
  });

  describe('Focus Interactions', () => {
    it('shows tooltip on focus', async () => {
      render(
        <Tooltip content='Tooltip text'>
          <button type='button'>Focus me</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');
      fireEvent.focus(trigger);

      await waitFor(() => {
        expect(screen.getByText('Tooltip text')).toBeInTheDocument();
      });
    });

    it('hides tooltip on blur', async () => {
      render(
        <Tooltip content='Tooltip text'>
          <button type='button'>Focus me</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');

      fireEvent.focus(trigger);
      await waitFor(() => {
        expect(screen.getByText('Tooltip text')).toBeInTheDocument();
      });

      fireEvent.blur(trigger);
      await waitFor(() => {
        expect(screen.queryByText('Tooltip text')).not.toBeInTheDocument();
      });
    });
  });

  describe('Click Interactions', () => {
    it('shows tooltip on click when trigger is click', async () => {
      render(
        <Tooltip content='Tooltip text' trigger='click'>
          <button type='button'>Click me</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');
      fireEvent.click(trigger);

      await waitFor(() => {
        expect(screen.getByText('Tooltip text')).toBeInTheDocument();
      });
    });

    it('toggles tooltip on repeated clicks', async () => {
      render(
        <Tooltip content='Tooltip text' trigger='click'>
          <button type='button'>Click me</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');

      // First click - show
      fireEvent.click(trigger);
      await waitFor(() => {
        expect(screen.getByText('Tooltip text')).toBeInTheDocument();
      });

      // Second click - hide
      fireEvent.click(trigger);
      await waitFor(() => {
        expect(screen.queryByText('Tooltip text')).not.toBeInTheDocument();
      });
    });

    it('hides tooltip when clicking outside', async () => {
      render(
        <div>
          <Tooltip content='Tooltip text' trigger='click'>
            <button type='button'>Click me</button>
          </Tooltip>
          <div data-testid='outside'>Outside element</div>
        </div>
      );

      const trigger = screen.getByRole('button');
      const outside = screen.getByTestId('outside');

      fireEvent.click(trigger);
      await waitFor(() => {
        expect(screen.getByText('Tooltip text')).toBeInTheDocument();
      });

      fireEvent.click(outside);
      await waitFor(() => {
        expect(screen.queryByText('Tooltip text')).not.toBeInTheDocument();
      });
    });
  });

  describe('Content Types', () => {
    it('renders text content', async () => {
      render(
        <Tooltip content='Simple text tooltip'>
          <button type='button'>Hover me</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');
      fireEvent.mouseEnter(trigger);

      await waitFor(() => {
        expect(screen.getByText('Simple text tooltip')).toBeInTheDocument();
      });
    });

    it('renders JSX content', async () => {
      render(
        <Tooltip
          content={
            <div>
              JSX <strong>tooltip</strong> content
            </div>
          }
        >
          <button type='button'>Hover me</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');
      fireEvent.mouseEnter(trigger);

      await waitFor(() => {
        expect(screen.getByText('JSX')).toBeInTheDocument();
        expect(screen.getByText('tooltip')).toBeInTheDocument();
        expect(screen.getByText('content')).toBeInTheDocument();
      });
    });

    it('handles empty content gracefully', () => {
      render(
        <Tooltip content=''>
          <button type='button'>Hover me</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');
      fireEvent.mouseEnter(trigger);

      // Should not show tooltip for empty content
      expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
    });

    it('handles null content gracefully', () => {
      render(
        <Tooltip content={null}>
          <button type='button'>Hover me</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');
      fireEvent.mouseEnter(trigger);

      // Should not show tooltip for null content
      expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
    });
  });

  describe('Positioning', () => {
    it('supports different placements', async () => {
      const { rerender } = render(
        <Tooltip content='Tooltip text' placement='top'>
          <button type='button'>Hover me</button>
        </Tooltip>
      );

      let trigger = screen.getByRole('button');
      fireEvent.mouseEnter(trigger);

      await waitFor(() => {
        const tooltip = screen.getByText('Tooltip text');
        expect(tooltip).toBeInTheDocument();
        // Check if tooltip has top placement class
        expect(tooltip.closest('[data-placement]')).toHaveAttribute('data-placement', 'top');
      });

      fireEvent.mouseLeave(trigger);
      await waitFor(() => {
        expect(screen.queryByText('Tooltip text')).not.toBeInTheDocument();
      });

      rerender(
        <Tooltip content='Tooltip text' placement='bottom'>
          <button type='button'>Hover me</button>
        </Tooltip>
      );

      trigger = screen.getByRole('button');
      fireEvent.mouseEnter(trigger);

      await waitFor(() => {
        const tooltip = screen.getByText('Tooltip text');
        expect(tooltip.closest('[data-placement]')).toHaveAttribute('data-placement', 'bottom');
      });
    });
  });

  describe('Controlled State', () => {
    it('supports controlled visibility', async () => {
      const ControlledTooltip = () => {
        const [open, setOpen] = React.useState(false);

        return (
          <div>
            <Tooltip content='Controlled tooltip' open={open}>
              <button type='button'>Trigger</button>
            </Tooltip>
            <button type='button' onClick={() => setOpen(!open)}>
              Toggle
            </button>
          </div>
        );
      };

      render(<ControlledTooltip />);

      // Initially hidden
      expect(screen.queryByText('Controlled tooltip')).not.toBeInTheDocument();

      // Show via external control
      fireEvent.click(screen.getByText('Toggle'));
      await waitFor(() => {
        expect(screen.getByText('Controlled tooltip')).toBeInTheDocument();
      });

      // Hide via external control
      fireEvent.click(screen.getByText('Toggle'));
      await waitFor(() => {
        expect(screen.queryByText('Controlled tooltip')).not.toBeInTheDocument();
      });
    });

    it('calls onOpenChange callback', async () => {
      const onOpenChange = jest.fn();

      render(
        <Tooltip content='Tooltip text' onOpenChange={onOpenChange}>
          <button type='button'>Hover me</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');

      fireEvent.mouseEnter(trigger);
      await waitFor(() => {
        expect(onOpenChange).toHaveBeenCalledWith(true);
      });

      fireEvent.mouseLeave(trigger);
      await waitFor(() => {
        expect(onOpenChange).toHaveBeenCalledWith(false);
      });
    });
  });

  describe('Accessibility', () => {
    it('should be accessible', async () => {
      const { container } = render(
        <Tooltip content='Accessible tooltip'>
          <button type='button'>Accessible button</button>
        </Tooltip>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should be accessible when tooltip is visible', async () => {
      const { container } = render(
        <Tooltip content='Visible tooltip'>
          <button type='button'>Hover me</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');
      fireEvent.mouseEnter(trigger);

      await waitFor(() => {
        expect(screen.getByText('Visible tooltip')).toBeInTheDocument();
      });

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('provides proper ARIA attributes', async () => {
      render(
        <Tooltip content='ARIA tooltip'>
          <button type='button'>Button</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');
      fireEvent.mouseEnter(trigger);

      await waitFor(() => {
        const tooltip = screen.getByText('ARIA tooltip');
        expect(tooltip).toBeInTheDocument();
        expect(tooltip).toHaveAttribute('role', 'tooltip');
        expect(trigger).toHaveAttribute('aria-describedby');
      });
    });

    it('supports custom ARIA labels', async () => {
      render(
        <Tooltip content='Custom ARIA tooltip' aria-label='Custom tooltip'>
          <button type='button'>Button</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');
      fireEvent.mouseEnter(trigger);

      await waitFor(() => {
        const tooltip = screen.getByText('Custom ARIA tooltip');
        expect(tooltip).toHaveAttribute('aria-label', 'Custom tooltip');
      });
    });
  });

  describe('Multiple Triggers', () => {
    it('supports multiple trigger types', async () => {
      render(
        <Tooltip content='Multi-trigger tooltip' trigger={['hover', 'focus']}>
          <button type='button'>Multi trigger</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');

      // Test hover
      fireEvent.mouseEnter(trigger);
      await waitFor(() => {
        expect(screen.getByText('Multi-trigger tooltip')).toBeInTheDocument();
      });

      fireEvent.mouseLeave(trigger);
      await waitFor(() => {
        expect(screen.queryByText('Multi-trigger tooltip')).not.toBeInTheDocument();
      });

      // Test focus
      fireEvent.focus(trigger);
      await waitFor(() => {
        expect(screen.getByText('Multi-trigger tooltip')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('handles rapid hover events gracefully', async () => {
      render(
        <Tooltip content='Rapid hover tooltip'>
          <button type='button'>Rapid hover</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');

      // Rapid mouse enter/leave
      for (let i = 0; i < 5; i++) {
        fireEvent.mouseEnter(trigger);
        fireEvent.mouseLeave(trigger);
      }

      // Final enter should still work
      fireEvent.mouseEnter(trigger);
      await waitFor(() => {
        expect(screen.getByText('Rapid hover tooltip')).toBeInTheDocument();
      });
    });

    it('handles disabled triggers', async () => {
      render(
        <Tooltip content='Disabled tooltip'>
          <button type='button' disabled>
            Disabled button
          </button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');
      fireEvent.mouseEnter(trigger);

      // Tooltip should still show for disabled elements
      await waitFor(() => {
        expect(screen.getByText('Disabled tooltip')).toBeInTheDocument();
      });
    });

    it('cleans up on unmount', async () => {
      const { unmount } = render(
        <Tooltip content='Unmount tooltip'>
          <button type='button'>Unmount me</button>
        </Tooltip>
      );

      const trigger = screen.getByRole('button');
      fireEvent.mouseEnter(trigger);

      await waitFor(() => {
        expect(screen.getByText('Unmount tooltip')).toBeInTheDocument();
      });

      unmount();

      // Should not cause any errors
      expect(screen.queryByText('Unmount tooltip')).not.toBeInTheDocument();
    });
  });
});
