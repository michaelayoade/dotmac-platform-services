/**
 * Avatar component comprehensive tests
 * Testing avatar display, fallbacks, status, utility functions and composition patterns
 */

import { render, screen, waitFor } from '@testing-library/react';
import { axe } from 'jest-axe';
import React from 'react';

import {
  Avatar,
  AvatarFallback,
  AvatarGroup,
  AvatarImage,
  AvatarStatus,
  AvatarUtils,
} from '../Avatar';

// Mock OptimizedImage primitive
jest.mock('@dotmac/primitives', () => ({
  OptimizedImage: React.forwardRef(
    ({ src, alt, onLoad, onError, className, ...props }: unknown, ref: unknown) => {
      // Simulate loading state
      React.useEffect(() => {
        const timer = setTimeout(() => {
          if (src && onLoad) {
            onLoad();
          }
          if (!src && onError) {
            onError();
          }
        }, 100);

        return () => clearTimeout(timer);
      }, [src, onLoad, onError]);

      return (
        <img
          ref={ref}
          src={src}
          alt={alt}
          className={className}
          onLoad={onLoad}
          onError={onError}
          {...props}
        />
      );
    }
  ),
}));

describe('Avatar Components', () => {
  describe('AvatarUtils', () => {
    describe('getTextSize', () => {
      it('returns correct text size for each size variant', () => {
        expect(AvatarUtils.getTextSize('sm')).toBe('text-xs');
        expect(AvatarUtils.getTextSize('default')).toBe('text-sm');
        expect(AvatarUtils.getTextSize('lg')).toBe('text-base');
        expect(AvatarUtils.getTextSize('xl')).toBe('text-lg');
        expect(AvatarUtils.getTextSize('2xl')).toBe('text-xl');
      });

      it('returns default size for unknown size', () => {
        expect(AvatarUtils.getTextSize('unknown')).toBe('text-sm');
      });
    });

    describe('getStatusSize', () => {
      it('returns correct status configuration for each size', () => {
        const smConfig = AvatarUtils.getStatusSize('sm');
        expect(smConfig.class).toBe('h-2 w-2');
        expect(smConfig.position).toBe('-bottom-0 -right-0');

        const defaultConfig = AvatarUtils.getStatusSize('default');
        expect(defaultConfig.class).toBe('h-3 w-3');
        expect(defaultConfig.position).toBe('-bottom-0.5 -right-0.5');

        const lgConfig = AvatarUtils.getStatusSize('lg');
        expect(lgConfig.class).toBe('h-3.5 w-3.5');
        expect(lgConfig.position).toBe('-bottom-0.5 -right-0.5');

        const xlConfig = AvatarUtils.getStatusSize('xl');
        expect(xlConfig.class).toBe('h-4 w-4');
        expect(xlConfig.position).toBe('-bottom-1 -right-1');

        const xxlConfig = AvatarUtils.getStatusSize('2xl');
        expect(xxlConfig.class).toBe('h-5 w-5');
        expect(xxlConfig.position).toBe('-bottom-1 -right-1');
      });

      it('returns default configuration for unknown size', () => {
        const config = AvatarUtils.getStatusSize('unknown');
        expect(config.class).toBe('h-3 w-3');
        expect(config.position).toBe('-bottom-0.5 -right-0.5');
      });
    });

    describe('getStatusColor', () => {
      it('returns correct color for each status', () => {
        expect(AvatarUtils.getStatusColor('online')).toBe('bg-green-500');
        expect(AvatarUtils.getStatusColor('offline')).toBe('bg-gray-400');
        expect(AvatarUtils.getStatusColor('busy')).toBe('bg-red-500');
        expect(AvatarUtils.getStatusColor('away')).toBe('bg-yellow-500');
      });

      it('returns default color for unknown status', () => {
        expect(AvatarUtils.getStatusColor('unknown')).toBe('bg-gray-400');
      });
    });

    describe('getPortalStyles', () => {
      it('returns correct styles for each portal', () => {
        expect(AvatarUtils.getPortalStyles('admin')).toBe(
          'bg-admin-muted text-admin-muted-foreground'
        );
        expect(AvatarUtils.getPortalStyles('customer')).toBe(
          'bg-customer-muted text-customer-muted-foreground'
        );
        expect(AvatarUtils.getPortalStyles('reseller')).toBe(
          'bg-reseller-muted text-reseller-muted-foreground'
        );
      });

      it('returns default styles for unknown portal', () => {
        expect(AvatarUtils.getPortalStyles('unknown')).toBe('bg-muted text-muted-foreground');
        expect(AvatarUtils.getPortalStyles(undefined)).toBe('bg-muted text-muted-foreground');
      });
    });
  });

  describe('AvatarImage', () => {
    it('renders image with correct props', () => {
      render(<AvatarImage src='/test-avatar.jpg' alt='Test Avatar' data-testid='avatar-image' />);

      const image = screen.getByTestId('avatar-image');
      expect(image).toBeInTheDocument();
      expect(image).toHaveAttribute('src', '/test-avatar.jpg');
      expect(image).toHaveAttribute('alt', 'Test Avatar');
      expect(image).toHaveClass('aspect-square', 'h-full', 'w-full', 'object-cover');
    });

    it('uses default alt text when not provided', () => {
      render(<AvatarImage src='/test-avatar.jpg' data-testid='avatar-image' />);

      const image = screen.getByTestId('avatar-image');
      expect(image).toHaveAttribute('alt', 'Avatar');
    });

    it('calls onLoad when image loads successfully', async () => {
      const onLoad = jest.fn();

      render(<AvatarImage src='/test-avatar.jpg' onLoad={onLoad} data-testid='avatar-image' />);

      await waitFor(() => {
        expect(onLoad).toHaveBeenCalled();
      });
    });

    it('calls onError when image fails to load', async () => {
      const onError = jest.fn();

      render(<AvatarImage src='' onError={onError} data-testid='avatar-image' />);

      await waitFor(() => {
        expect(onError).toHaveBeenCalled();
      });
    });

    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLImageElement>();

      render(<AvatarImage ref={ref} src='/test.jpg' />);

      expect(ref.current).toBeInstanceOf(HTMLImageElement);
    });

    it('applies custom className', () => {
      render(<AvatarImage src='/test.jpg' className='custom-image' data-testid='avatar-image' />);

      const image = screen.getByTestId('avatar-image');
      expect(image).toHaveClass('custom-image');
    });
  });

  describe('AvatarFallback', () => {
    it('renders fallback with correct styling', () => {
      render(<AvatarFallback data-testid='avatar-fallback'>JD</AvatarFallback>);

      const fallback = screen.getByTestId('avatar-fallback');
      expect(fallback).toBeInTheDocument();
      expect(fallback).toHaveTextContent('JD');
      expect(fallback).toHaveClass(
        'flex',
        'h-full',
        'w-full',
        'items-center',
        'justify-center',
        'font-medium',
        'bg-muted',
        'text-muted-foreground',
        'text-sm'
      );
    });

    it('applies correct text size based on size prop', () => {
      const { rerender } = render(
        <AvatarFallback size='sm' data-testid='fallback'>
          JD
        </AvatarFallback>
      );

      expect(screen.getByTestId('fallback')).toHaveClass('text-xs');

      rerender(
        <AvatarFallback size='lg' data-testid='fallback'>
          JD
        </AvatarFallback>
      );
      expect(screen.getByTestId('fallback')).toHaveClass('text-base');

      rerender(
        <AvatarFallback size='xl' data-testid='fallback'>
          JD
        </AvatarFallback>
      );
      expect(screen.getByTestId('fallback')).toHaveClass('text-lg');
    });

    it('applies portal-specific styling', () => {
      const { rerender } = render(
        <AvatarFallback portal='admin' data-testid='fallback'>
          A
        </AvatarFallback>
      );

      expect(screen.getByTestId('fallback')).toHaveClass(
        'bg-admin-muted',
        'text-admin-muted-foreground'
      );

      rerender(
        <AvatarFallback portal='customer' data-testid='fallback'>
          C
        </AvatarFallback>
      );
      expect(screen.getByTestId('fallback')).toHaveClass(
        'bg-customer-muted',
        'text-customer-muted-foreground'
      );

      rerender(
        <AvatarFallback portal='reseller' data-testid='fallback'>
          R
        </AvatarFallback>
      );
      expect(screen.getByTestId('fallback')).toHaveClass(
        'bg-reseller-muted',
        'text-reseller-muted-foreground'
      );
    });

    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>();

      render(<AvatarFallback ref={ref}>JD</AvatarFallback>);

      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });

    it('applies custom className', () => {
      render(
        <AvatarFallback className='custom-fallback' data-testid='fallback'>
          JD
        </AvatarFallback>
      );

      const fallback = screen.getByTestId('fallback');
      expect(fallback).toHaveClass('custom-fallback');
    });
  });

  describe('AvatarStatus', () => {
    it('renders status indicator with correct styling', () => {
      render(<AvatarStatus status='online' data-testid='avatar-status' />);

      const status = screen.getByTestId('avatar-status');
      expect(status).toBeInTheDocument();
      expect(status).toHaveClass(
        'absolute',
        'rounded-full',
        'border-2',
        'border-background',
        'h-3',
        'w-3',
        '-bottom-0.5',
        '-right-0.5',
        'bg-green-500'
      );
    });

    it('renders different status colors correctly', () => {
      const { rerender } = render(<AvatarStatus status='online' data-testid='status' />);
      expect(screen.getByTestId('status')).toHaveClass('bg-green-500');

      rerender(<AvatarStatus status='offline' data-testid='status' />);
      expect(screen.getByTestId('status')).toHaveClass('bg-gray-400');

      rerender(<AvatarStatus status='busy' data-testid='status' />);
      expect(screen.getByTestId('status')).toHaveClass('bg-red-500');

      rerender(<AvatarStatus status='away' data-testid='status' />);
      expect(screen.getByTestId('status')).toHaveClass('bg-yellow-500');
    });

    it('applies correct size styling', () => {
      const { rerender } = render(<AvatarStatus status='online' size='sm' data-testid='status' />);
      expect(screen.getByTestId('status')).toHaveClass('h-2', 'w-2', '-bottom-0', '-right-0');

      rerender(<AvatarStatus status='online' size='lg' data-testid='status' />);
      expect(screen.getByTestId('status')).toHaveClass(
        'h-3.5',
        'w-3.5',
        '-bottom-0.5',
        '-right-0.5'
      );

      rerender(<AvatarStatus status='online' size='xl' data-testid='status' />);
      expect(screen.getByTestId('status')).toHaveClass('h-4', 'w-4', '-bottom-1', '-right-1');
    });

    it('shows animated ping for online status', () => {
      render(<AvatarStatus status='online' data-testid='status' />);

      const status = screen.getByTestId('status');
      const pingElement = status.querySelector('.animate-ping');
      expect(pingElement).toBeInTheDocument();
      expect(pingElement).toHaveClass(
        'absolute',
        'inset-0',
        'rounded-full',
        'bg-green-500',
        'animate-ping',
        'opacity-75'
      );
    });

    it('does not show ping for non-online status', () => {
      render(<AvatarStatus status='offline' data-testid='status' />);

      const status = screen.getByTestId('status');
      const pingElement = status.querySelector('.animate-ping');
      expect(pingElement).not.toBeInTheDocument();
    });

    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>();

      render(<AvatarStatus ref={ref} status='online' />);

      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });
  });

  describe('Avatar', () => {
    it('renders with default props', () => {
      render(
        <Avatar data-testid='avatar'>
          <AvatarFallback>JD</AvatarFallback>
        </Avatar>
      );

      const avatar = screen.getByTestId('avatar');
      expect(avatar).toBeInTheDocument();
      expect(avatar).toHaveClass(
        'relative',
        'flex',
        'shrink-0',
        'overflow-hidden',
        'rounded-full',
        'h-10',
        'w-10'
      );
    });

    it('applies size variants correctly', () => {
      const { rerender } = render(
        <Avatar size='sm' data-testid='avatar'>
          <AvatarFallback>JD</AvatarFallback>
        </Avatar>
      );

      expect(screen.getByTestId('avatar')).toHaveClass('h-8', 'w-8');

      rerender(
        <Avatar size='lg' data-testid='avatar'>
          <AvatarFallback>JD</AvatarFallback>
        </Avatar>
      );
      expect(screen.getByTestId('avatar')).toHaveClass('h-12', 'w-12');

      rerender(
        <Avatar size='xl' data-testid='avatar'>
          <AvatarFallback>JD</AvatarFallback>
        </Avatar>
      );
      expect(screen.getByTestId('avatar')).toHaveClass('h-16', 'w-16');

      rerender(
        <Avatar size='2xl' data-testid='avatar'>
          <AvatarFallback>JD</AvatarFallback>
        </Avatar>
      );
      expect(screen.getByTestId('avatar')).toHaveClass('h-20', 'w-20');
    });

    it('renders with custom children (composition pattern)', () => {
      render(
        <Avatar data-testid='avatar'>
          <div data-testid='custom-child'>Custom content</div>
        </Avatar>
      );

      expect(screen.getByTestId('custom-child')).toBeInTheDocument();
      expect(screen.getByText('Custom content')).toBeInTheDocument();
    });

    it('renders with image and fallback when no children provided', async () => {
      render(<Avatar src='/test-avatar.jpg' fallback='JD' data-testid='avatar' />);

      // Initially shows fallback while image loads
      expect(screen.getByTestId('avatar-fallback')).toBeInTheDocument();
      expect(screen.getByText('JD')).toBeInTheDocument();

      // After image loads, both are present but image is visible
      await waitFor(() => {
        expect(screen.getByTestId('avatar-image')).toBeInTheDocument();
      });
    });

    it('shows only fallback when no src provided', () => {
      render(<Avatar fallback='JD' data-testid='avatar' />);

      expect(screen.getByTestId('avatar-fallback')).toBeInTheDocument();
      expect(screen.queryByTestId('avatar-image')).not.toBeInTheDocument();
    });

    it('renders status indicator when status prop provided', () => {
      render(<Avatar status='online' fallback='JD' data-testid='avatar' />);

      expect(screen.getByTestId('avatar-status')).toBeInTheDocument();
    });

    it('passes portal prop to fallback', () => {
      render(<Avatar portal='admin' fallback='A' data-testid='avatar' />);

      const fallback = screen.getByTestId('avatar-fallback');
      expect(fallback).toHaveClass('bg-admin-muted', 'text-admin-muted-foreground');
    });

    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>();

      render(
        <Avatar ref={ref} fallback='JD'>
          <AvatarFallback>JD</AvatarFallback>
        </Avatar>
      );

      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });

    it('applies custom className', () => {
      render(
        <Avatar className='custom-avatar' data-testid='avatar'>
          <AvatarFallback>JD</AvatarFallback>
        </Avatar>
      );

      const avatar = screen.getByTestId('avatar');
      expect(avatar).toHaveClass('custom-avatar');
    });

    it('handles image loading states correctly', async () => {
      const { rerender } = render(
        <Avatar src='/test-avatar.jpg' fallback='JD' data-testid='avatar' />
      );

      // Initially fallback is shown
      expect(screen.getByTestId('avatar-fallback')).toBeInTheDocument();

      // Wait for image to load
      await waitFor(() => {
        const image = screen.getByTestId('avatar-image');
        expect(image).toHaveClass('opacity-100');
      });

      // Test error state
      rerender(<Avatar src='/invalid-image.jpg' fallback='JD' data-testid='avatar' />);

      await waitFor(() => {
        expect(screen.getByTestId('avatar-fallback')).toBeInTheDocument();
      });
    });
  });

  describe('AvatarGroup', () => {
    it('renders multiple avatars with correct styling', () => {
      render(
        <AvatarGroup data-testid='avatar-group'>
          <Avatar fallback='JD' />
          <Avatar fallback='SM' />
          <Avatar fallback='KL' />
        </AvatarGroup>
      );

      const group = screen.getByTestId('avatar-group');
      expect(group).toBeInTheDocument();
      expect(group).toHaveClass('flex', '-space-x-2');

      // All avatars should be rendered
      expect(screen.getByText('JD')).toBeInTheDocument();
      expect(screen.getByText('SM')).toBeInTheDocument();
      expect(screen.getByText('KL')).toBeInTheDocument();
    });

    it('limits avatars to max prop and shows remaining count', () => {
      render(
        <AvatarGroup max={2} data-testid='avatar-group'>
          <Avatar fallback='JD' />
          <Avatar fallback='SM' />
          <Avatar fallback='KL' />
          <Avatar fallback='OP' />
        </AvatarGroup>
      );

      // Only first 2 avatars shown
      expect(screen.getByText('JD')).toBeInTheDocument();
      expect(screen.getByText('SM')).toBeInTheDocument();

      // Remaining count shown
      expect(screen.getByText('+2')).toBeInTheDocument();

      // Hidden avatars not rendered
      expect(screen.queryByText('KL')).not.toBeInTheDocument();
      expect(screen.queryByText('OP')).not.toBeInTheDocument();
    });

    it('applies size prop to all avatars', () => {
      render(
        <AvatarGroup size='lg' data-testid='avatar-group'>
          <Avatar fallback='JD' />
          <Avatar fallback='SM' />
        </AvatarGroup>
      );

      const avatars = screen.getAllByTestId('avatar');
      avatars.forEach((avatar) => {
        expect(avatar).toHaveClass('h-12', 'w-12');
      });
    });

    it('applies portal prop to avatars', () => {
      render(
        <AvatarGroup portal='admin' data-testid='avatar-group'>
          <Avatar fallback='A' />
        </AvatarGroup>
      );

      const fallback = screen.getByTestId('avatar-fallback');
      expect(fallback).toHaveClass('bg-admin-muted', 'text-admin-muted-foreground');
    });

    it('handles empty group', () => {
      render(<AvatarGroup data-testid='avatar-group' />);

      const group = screen.getByTestId('avatar-group');
      expect(group).toBeInTheDocument();
      expect(group).toBeEmptyDOMElement();
    });

    it('handles single avatar without overflow', () => {
      render(
        <AvatarGroup max={3} data-testid='avatar-group'>
          <Avatar fallback='JD' />
        </AvatarGroup>
      );

      expect(screen.getByText('JD')).toBeInTheDocument();
      expect(screen.queryByText('+')).not.toBeInTheDocument();
    });

    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>();

      render(<AvatarGroup ref={ref} />);

      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });
  });

  describe('Accessibility', () => {
    it('Avatar should be accessible', async () => {
      const { container } = render(
        <Avatar>
          <AvatarImage src='/test.jpg' alt='User avatar' />
          <AvatarFallback>JD</AvatarFallback>
        </Avatar>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('AvatarGroup should be accessible', async () => {
      const { container } = render(
        <AvatarGroup>
          <Avatar>
            <AvatarImage src='/test1.jpg' alt='User 1' />
            <AvatarFallback>U1</AvatarFallback>
          </Avatar>
          <Avatar>
            <AvatarImage src='/test2.jpg' alt='User 2' />
            <AvatarFallback>U2</AvatarFallback>
          </Avatar>
        </AvatarGroup>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('supports ARIA attributes', () => {
      render(
        <Avatar role='img' aria-label='User profile picture' data-testid='avatar'>
          <AvatarFallback>JD</AvatarFallback>
        </Avatar>
      );

      const avatar = screen.getByTestId('avatar');
      expect(avatar).toHaveAttribute('role', 'img');
      expect(avatar).toHaveAttribute('aria-label', 'User profile picture');
    });
  });

  describe('Edge Cases', () => {
    it('handles very long fallback text', () => {
      render(
        <Avatar data-testid='avatar'>
          <AvatarFallback>VERY LONG FALLBACK TEXT</AvatarFallback>
        </Avatar>
      );

      const fallback = screen.getByTestId('avatar-fallback');
      expect(fallback).toHaveTextContent('VERY LONG FALLBACK TEXT');
    });

    it('handles special characters in fallback', () => {
      render(
        <Avatar data-testid='avatar'>
          <AvatarFallback>@#$%</AvatarFallback>
        </Avatar>
      );

      const fallback = screen.getByTestId('avatar-fallback');
      expect(fallback).toHaveTextContent('@#$%');
    });

    it('handles empty fallback gracefully', () => {
      render(
        <Avatar data-testid='avatar'>
          <AvatarFallback></AvatarFallback>
        </Avatar>
      );

      const fallback = screen.getByTestId('avatar-fallback');
      expect(fallback).toBeInTheDocument();
    });

    it('handles multiple status changes', () => {
      const { rerender } = render(<Avatar status='offline' fallback='JD' data-testid='avatar' />);

      expect(screen.getByTestId('avatar-status')).toHaveClass('bg-gray-400');

      rerender(<Avatar status='online' fallback='JD' data-testid='avatar' />);
      expect(screen.getByTestId('avatar-status')).toHaveClass('bg-green-500');

      rerender(<Avatar status='busy' fallback='JD' data-testid='avatar' />);
      expect(screen.getByTestId('avatar-status')).toHaveClass('bg-red-500');
    });
  });

  describe('Performance', () => {
    it('renders efficiently with complex content', () => {
      const startTime = performance.now();

      render(
        <AvatarGroup max={10}>
          {Array.from({ length: 20 }, (_, i) => (
            <Avatar key={`item-${i}`} fallback={`U${i}`} />
          ))}
        </AvatarGroup>
      );

      const endTime = performance.now();

      // Should render within reasonable time
      expect(endTime - startTime).toBeLessThan(100);

      // Should only show max avatars plus overflow
      expect(screen.getAllByTestId('avatar')).toHaveLength(11); // 10 + 1 overflow
    });
  });
});
