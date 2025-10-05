# Dependency Upgrades - Migration Guide

## Overview
This document outlines critical dependency upgrades and migration steps required.

## ✅ Completed Upgrades

### 1. @hookform/resolvers (3.3.4 → 3.9.1)
**Status**: Package version updated in package.json

**Changes:**
- No breaking changes in this version range
- Improved TypeScript types
- Better Zod resolver performance

**Action Required:**
```bash
pnpm install
```

**Code Changes:**
None required - backward compatible upgrade.

---

### 2. Storybook (8.4.7 → 9.0.0)
**Status**: Package versions updated in package.json

**Major Breaking Changes:**
- **Removed support for Node.js 16**
  - Minimum requirement: Node.js 18.x
- **New default renderer configuration**
- **Updated addon API**
- **Framework-specific changes for Next.js**

**Action Required:**

1. **Update Storybook config** (`.storybook/main.ts`):
```typescript
// Old format (Storybook 8)
module.exports = {
  stories: ['../stories/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: ['@storybook/addon-essentials'],
  framework: '@storybook/nextjs',
};

// New format (Storybook 9)
import type { StorybookConfig } from '@storybook/nextjs';

const config: StorybookConfig = {
  stories: ['../stories/**/*.mdx', '../stories/**/*.stories.@(js|jsx|mjs|ts|tsx)'],
  addons: ['@storybook/addon-essentials', '@storybook/addon-links'],
  framework: {
    name: '@storybook/nextjs',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
};

export default config;
```

2. **Install new dependencies:**
```bash
pnpm install
```

3. **Run Storybook upgrade command:**
```bash
pnpm dlx storybook@latest upgrade
```

**References:**
- [Storybook 9.0 Migration Guide](https://storybook.js.org/docs/migration-guide)

---

### 3. ESLint (8.57.1 → 9.17.0)
**Status**: Package updated, flat config created

**Major Breaking Changes:**
- **Flat config is now the default** (replaces `.eslintrc.*`)
- Removed formatters deprecated in v8
- Updated rule configurations

**Action Required:**

1. **✅ New flat config created**: `eslint.config.mjs`
2. **Remove old config files**:
```bash
rm -f .eslintrc.js .eslintrc.json .eslintrc.yml
```

3. **Install compatibility package** (already added):
```bash
pnpm add -D @eslint/eslintrc
```

4. **Update scripts** (if needed):
```json
{
  "scripts": {
    "lint": "eslint .",
    "lint:fix": "eslint . --fix"
  }
}
```

**Migration Notes:**
- Flat config uses `export default` instead of `module.exports`
- Plugin names no longer need `eslint-plugin-` prefix
- Config extends using `FlatCompat` for backward compatibility

**References:**
- [ESLint 9.0 Migration Guide](https://eslint.org/docs/latest/use/migrate-to-9.0.0)
- [Flat Config Migration](https://eslint.org/docs/latest/use/configure/migration-guide)

---

## TypeScript Strict Mode Enhancements

### Enabled Compiler Options

**Already Enabled:**
- `strict: true` ✅

**New Additions:**
- `noUncheckedIndexedAccess: true` - Adds `| undefined` to indexed access types
- `noImplicitReturns: true` - Ensures all code paths return a value
- `noFallthroughCasesInSwitch: true` - Prevents switch fallthrough bugs
- `noUnusedLocals: true` - Warns about unused local variables
- `noUnusedParameters: true` - Warns about unused function parameters
- `exactOptionalPropertyTypes: true` - Stricter optional property handling

**Impact:**
These changes will surface additional type errors that need to be fixed. Common patterns:

```typescript
// Before
const item = array[0]; // Type: Item
item.property; // Unsafe!

// After (with noUncheckedIndexedAccess)
const item = array[0]; // Type: Item | undefined
item?.property; // Safe!

// Before
function process(data?: string) {
  // No explicit return
}

// After (with noImplicitReturns)
function process(data?: string): void {
  // Must explicitly return or have void return type
}
```

---

## Code Quality Improvements

### Removed `any` Types
**File**: `components/ui/data-table.tsx`

**Changes:**
- Replaced `any` with proper generic types in `createSortableHeader`
- Added `Column<TData, TValue>` type import from `@tanstack/react-table`

**Before:**
```typescript
export function createSortableHeader(label: string) {
  return ({ column }: { column: any }) => {
    // ...
  };
}
```

**After:**
```typescript
export function createSortableHeader<TData, TValue>(label: string) {
  return ({ column }: { column: Column<TData, TValue> }) => {
    // ...
  };
}
```

---

## Next Steps

### 1. Install Updated Dependencies
```bash
pnpm install
```

### 2. Fix Type Errors
Run type checking to identify issues from stricter TypeScript:
```bash
pnpm type-check
```

### 3. Update Storybook Config
If using Storybook, update configuration files in `.storybook/` directory.

### 4. Test Application
```bash
# Run tests
pnpm test

# Run Storybook
pnpm storybook

# Build production
pnpm build
```

### 5. Monitor for Runtime Issues
- Watch for deprecation warnings in console
- Test critical user flows
- Check for type-related runtime errors

---

## Rollback Plan

If issues arise, you can rollback by reverting `package.json` changes:

```json
{
  "@hookform/resolvers": "^3.3.4",
  "@storybook/addon-essentials": "^8.4.7",
  "eslint": "^8.57.1",
  "storybook": "^8.4.7"
}
```

Then run:
```bash
pnpm install
git checkout tsconfig.json eslint.config.mjs
```

---

## Support & Resources

- **Storybook Discord**: https://discord.gg/storybook
- **ESLint Discussion**: https://github.com/eslint/eslint/discussions
- **TypeScript Issues**: https://github.com/microsoft/TypeScript/issues

Last Updated: 2025-10-04
