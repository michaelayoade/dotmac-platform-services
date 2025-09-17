/**
 * ESLint Rule: no-cross-portal-imports
 *
 * Prevents importing components from different portals within the same file.
 * This maintains portal isolation and prevents styling conflicts.
 *
 * Examples of violations:
 * - import { AdminButton } from '@dotmac/styled-components/admin';
 *   import { CustomerCard } from '@dotmac/styled-components/customer'; // ❌ Error
 *
 * - import { AdminButton, CustomerCard } from '@dotmac/styled-components'; // ❌ Error
 *
 * Allowed:
 * - import { AdminButton, AdminCard } from '@dotmac/styled-components/admin'; // ✅ OK
 * - import { Badge, Avatar } from '@dotmac/styled-components/shared'; // ✅ OK (shared is always allowed)
 */

module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Disallow mixing components from different portals',
      category: 'Best Practices',
      recommended: true,
    },
    fixable: null,
    schema: [
      {
        type: 'object',
        properties: {
          allowShared: {
            type: 'boolean',
            default: true,
          },
          allowMixedInTests: {
            type: 'boolean',
            default: true,
          },
          testFilePatterns: {
            type: 'array',
            items: { type: 'string' },
            default: ['**/*.test.*', '**/*.spec.*', '**/*.stories.*', '**/test/**/*'],
          },
        },
        additionalProperties: false,
      },
    ],
    messages: {
      crossPortalImport:
        'Cannot mix components from different portals. Found imports from "{{currentPortal}}" and "{{newPortal}}" in the same file.',
      mixedPortalImport:
        'Cannot import from multiple portals using the main package. Use specific portal imports: @dotmac/styled-components/{{portal}}',
      unknownPortal:
        'Unknown portal "{{portal}}". Valid portals are: admin, customer, reseller, shared.',
    },
  },

  create(context) {
    const options = context.getOptions()[0] || {};
    const allowShared = options.allowShared !== false;
    const allowMixedInTests = options.allowMixedInTests !== false;
    const testFilePatterns = options.testFilePatterns || [
      '**/*.test.*',
      '**/*.spec.*',
      '**/*.stories.*',
      '**/test/**/*',
    ];

    const filename = context.getFilename();
    const validPortals = ['admin', 'customer', 'reseller', 'shared'];

    // Check if this is a test file
    const isTestFile = testFilePatterns.some((pattern) => {
      const minimatch = require('minimatch');
      return minimatch(filename, pattern);
    });

    if (allowMixedInTests && isTestFile) {
      return {}; // Skip validation for test files
    }

    let currentPortal = null;
    const seenPortals = new Set();
    const importNodes = new Map(); // Track import nodes for better error reporting

    /**
     * Extract portal from import source
     */
    function getPortalFromSource(source) {
      // Handle @dotmac/styled-components/portal imports
      const portalMatch = source.match(/@dotmac\/styled-components\/([^/]+)/);
      if (portalMatch) {
        const portal = portalMatch[1];
        return validPortals.includes(portal) ? portal : null;
      }

      // Handle main package imports (should be discouraged for portal-specific components)
      if (source === '@dotmac/styled-components') {
        return 'mixed'; // Special case for mixed imports
      }

      return null;
    }

    /**
     * Check if imported specifiers are portal-specific
     */
    function hasPortalSpecificImports(specifiers) {
      const portalPrefixes = ['Admin', 'Customer', 'Reseller'];

      return specifiers.some((spec) => {
        if (spec.type === 'ImportSpecifier') {
          const name = spec.imported.name;
          return portalPrefixes.some((prefix) => name.startsWith(prefix));
        }
        return false;
      });
    }

    return {
      ImportDeclaration(node) {
        const source = node.source.value;
        const portal = getPortalFromSource(source);

        if (!portal) {
          return; // Not a styled-components import
        }

        // Handle mixed imports from main package
        if (portal === 'mixed') {
          if (hasPortalSpecificImports(node.specifiers)) {
            context.report({
              node,
              messageId: 'mixedPortalImport',
              data: {
                portal: 'admin|customer|reseller',
              },
            });
          }
          return;
        }

        // Validate portal exists
        if (!validPortals.includes(portal)) {
          context.report({
            node,
            messageId: 'unknownPortal',
            data: { portal },
          });
          return;
        }

        // Shared imports are always allowed
        if (portal === 'shared' && allowShared) {
          return;
        }

        // Track this portal
        seenPortals.add(portal);
        importNodes.set(portal, node);

        // Check for cross-portal violations
        if (currentPortal === null) {
          currentPortal = portal;
        } else if (currentPortal !== portal && portal !== 'shared') {
          // Report error on the newer import
          context.report({
            node,
            messageId: 'crossPortalImport',
            data: {
              currentPortal,
              newPortal: portal,
            },
          });
        }
      },
    };
  },
};

/**
 * ESLint configuration for the rule
 */
module.exports.configs = {
  recommended: {
    plugins: ['@dotmac/styled-components'],
    rules: {
      '@dotmac/styled-components/no-cross-portal-imports': 'error',
    },
  },
  strict: {
    plugins: ['@dotmac/styled-components'],
    rules: {
      '@dotmac/styled-components/no-cross-portal-imports': [
        'error',
        {
          allowShared: true,
          allowMixedInTests: false, // Strict mode doesn't allow mixed imports even in tests
          testFilePatterns: ['**/*.test.*', '**/*.spec.*'],
        },
      ],
    },
  },
};
