/**
 * Test file demonstrating valid portal imports
 *
 * This file should pass ESLint validation.
 * Shows correct usage patterns for the no-cross-portal-imports rule.
 */

// ✅ VALID: Single portal imports
import { AdminButton, AdminCard, AdminCardHeader } from '@dotmac/styled-components/admin';

// ✅ VALID: Shared components (always allowed)
import { Avatar, Badge } from '@dotmac/styled-components/shared';

// ✅ VALID: Mixed shared and single portal

function ValidExample() {
  return (
    <div>
      <AdminCard>
        <AdminCardHeader>
          <h2>Admin Dashboard</h2>
          <Badge variant='success'>Active</Badge>
        </AdminCardHeader>
      </AdminCard>

      <AdminButton>Admin Action</AdminButton>
      <Avatar fallback='AD' />
    </div>
  );
}

export default ValidExample;
