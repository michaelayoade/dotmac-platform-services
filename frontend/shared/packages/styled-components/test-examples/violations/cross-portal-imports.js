/**
 * Test file demonstrating cross-portal import violations
 *
 * This file should trigger ESLint errors when linted.
 * Used for testing the no-cross-portal-imports rule.
 */

// ❌ VIOLATION: Mixing admin and customer components
import { AdminButton } from '@dotmac/styled-components/admin';
import { CustomerCard } from '@dotmac/styled-components/customer'; // This should error

// ❌ VIOLATION: Unknown portal

function ViolationExample() {
  return (
    <div>
      <AdminButton>Admin Action</AdminButton>
      <CustomerCard>Customer Content</CustomerCard>
    </div>
  );
}

export default ViolationExample;
