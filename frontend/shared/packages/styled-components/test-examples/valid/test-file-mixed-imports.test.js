/* eslint-env jest */
/**
 * Test file demonstrating mixed imports in test files
 *
 * This file should pass ESLint validation because test files
 * are exempted from the cross-portal import restrictions.
 */

// ✅ VALID in test files: Mixed portal imports allowed for testing
import { AdminButton } from '@dotmac/styled-components/admin';
import { CustomerCard } from '@dotmac/styled-components/customer';
import { ResellerInput } from '@dotmac/styled-components/reseller';
import { Badge } from '@dotmac/styled-components/shared';

describe('Cross-portal component testing', () => {
  it('should render admin components', () => {
    // Test admin components
    expect(AdminButton).toBeDefined();
  });

  it('should render customer components', () => {
    // Test customer components
    expect(CustomerCard).toBeDefined();
  });

  it('should render reseller components', () => {
    // Test reseller components
    expect(ResellerInput).toBeDefined();
  });

  it('should render shared components', () => {
    // Test shared components
    expect(Badge).toBeDefined();
  });
});

// ✅ VALID: Component comparison testing
function ComponentComparison() {
  return (
    <div>
      <div data-testid='admin-section'>
        <AdminButton>Admin Button</AdminButton>
      </div>

      <div data-testid='customer-section'>
        <CustomerCard>Customer Card</CustomerCard>
      </div>

      <div data-testid='reseller-section'>
        <ResellerInput placeholder='Reseller Input' />
      </div>

      <div data-testid='shared-section'>
        <Badge>Shared Badge</Badge>
      </div>
    </div>
  );
}

export default ComponentComparison;
