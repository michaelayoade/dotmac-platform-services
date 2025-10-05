# Accessibility Implementation Plan

## Current State Audit

**Statistics** (as of 2025-10-04):
- **Total Component Files**: 64 (.tsx files in app/)
- **Button Elements**: 246 `<button>` tags
- **Button Components**: 229 `<Button>` components
- **Total Buttons**: ~475 buttons
- **Existing ARIA Labels**: 27 (5.7% coverage)
- **Images**: 1 `<img>` element
- **Images Needing Alt**: ~1

**Accessibility Gaps**:
1. ❌ **94.3% of buttons** lack ARIA labels (448/475)
2. ❌ Many interactive elements use `<div>` instead of semantic HTML
3. ❌ Inconsistent keyboard navigation
4. ❌ Forms lack proper labels and validation messages
5. ❌ Missing skip links and landmarks
6. ❌ No focus management for modals/dialogs
7. ❌ Insufficient color contrast in some areas

## Implementation Strategy

### Phase 1: Infrastructure & Tooling (2 hours)
1. Create accessibility helper utilities
2. Set up automated linting (eslint-plugin-jsx-a11y)
3. Create reusable accessible components
4. Document accessibility patterns

### Phase 2: Core Component Fixes (10 hours)
1. Fix Button component to require accessible labels
2. Fix Input/Form components with proper labels
3. Fix Modal/Dialog components with focus traps
4. Create accessible Table component
5. Fix Navigation components with keyboard support

### Phase 3: Page-by-Page Fixes (20 hours)
1. Dashboard pages (8 hours)
2. Settings pages (4 hours)
3. Operations pages (4 hours)
4. Infrastructure pages (4 hours)

### Phase 4: Testing & Validation (8 hours)
1. Automated accessibility testing
2. Keyboard navigation testing
3. Screen reader testing
4. WCAG 2.1 AA compliance verification

**Total Estimated Time**: 40 hours

## WCAG 2.1 AA Compliance Checklist

### 1. Perceivable

#### 1.1 Text Alternatives
- [ ] All images have alt text
- [ ] Decorative images have empty alt=""
- [ ] Icon buttons have aria-label
- [ ] Complex images have detailed descriptions

#### 1.2 Time-based Media
- [ ] Audio content has captions (N/A - no audio/video)
- [ ] Video content has audio descriptions (N/A)

#### 1.3 Adaptable
- [x] Semantic HTML used (heading hierarchy)
- [ ] Info/relationships programmatically determined
- [ ] Reading order is logical
- [ ] Sensory characteristics not sole means

#### 1.4 Distinguishable
- [ ] Color not sole means of conveying info
- [ ] Text contrast ratio ≥ 4.5:1 (normal), ≥ 3:1 (large)
- [ ] Text can be resized 200% without loss
- [ ] No images of text (use actual text)

### 2. Operable

#### 2.1 Keyboard Accessible
- [ ] All functionality keyboard accessible
- [ ] No keyboard traps
- [ ] Keyboard shortcuts documented
- [ ] Focus visible on all interactive elements

#### 2.2 Enough Time
- [ ] User can extend time limits
- [ ] Auto-updating content can be paused
- [ ] No unexpected time limits

#### 2.3 Seizures
- [ ] No content flashing > 3 times/second

#### 2.4 Navigable
- [ ] Skip link to main content
- [ ] Page titles describe topic/purpose
- [ ] Focus order preserves meaning
- [ ] Link purpose clear from context
- [ ] Multiple ways to locate pages
- [ ] Headings and labels descriptive
- [ ] Focus visible

### 3. Understandable

#### 3.1 Readable
- [x] Page language identified (lang="en")
- [ ] Language of parts identified
- [ ] Unusual words explained

#### 3.2 Predictable
- [ ] Focus doesn't cause context change
- [ ] Input doesn't cause context change
- [ ] Navigation consistent across pages
- [ ] Components identified consistently

#### 3.3 Input Assistance
- [ ] Errors identified and described
- [ ] Labels/instructions provided
- [ ] Error suggestions provided
- [ ] Error prevention for legal/financial

### 4. Robust

#### 4.1 Compatible
- [x] Valid HTML
- [ ] Name, role, value programmatically determined
- [ ] Status messages communicated to AT

## Automated Fixes

### 1. Button Accessibility Script

Create script to add ARIA labels to all buttons:

```bash
#!/bin/bash
# scripts/add-button-aria-labels.sh

# Find all Button components without aria-label
grep -r "<Button" app/ components/ | \
  grep -v "aria-label" | \
  grep -v "aria-labelledby" | \
  awk -F: '{print $1}' | \
  sort -u
```

### 2. ESLint Configuration

```json
// .eslintrc.json
{
  "extends": [
    "next/core-web-vitals",
    "plugin:jsx-a11y/recommended"
  ],
  "plugins": ["jsx-a11y"],
  "rules": {
    "jsx-a11y/alt-text": "error",
    "jsx-a11y/aria-props": "error",
    "jsx-a11y/aria-proptypes": "error",
    "jsx-a11y/aria-unsupported-elements": "error",
    "jsx-a11y/role-has-required-aria-props": "error",
    "jsx-a11y/role-supports-aria-props": "error",
    "jsx-a11y/click-events-have-key-events": "error",
    "jsx-a11y/no-noninteractive-element-interactions": "error"
  }
}
```

### 3. Accessibility Testing

```typescript
// __tests__/a11y/accessibility.test.ts
import { axe, toHaveNoViolations } from 'jest-axe';
import { render } from '@testing-library/react';

expect.extend(toHaveNoViolations);

describe('Accessibility Tests', () => {
  it('Dashboard should have no a11y violations', async () => {
    const { container } = render(<DashboardPage />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

## Implementation Patterns

### Pattern 1: Button with Icon Only

```typescript
// ❌ Bad
<Button>
  <Trash2 className="h-4 w-4" />
</Button>

// ✅ Good
<Button aria-label="Delete item">
  <Trash2 className="h-4 w-4" />
  <span className="sr-only">Delete</span>
</Button>
```

### Pattern 2: Form Labels

```typescript
// ❌ Bad
<input type="text" placeholder="Email" />

// ✅ Good
<label htmlFor="email" className="block text-sm font-medium">
  Email
</label>
<input
  id="email"
  type="email"
  aria-required="true"
  aria-invalid={!!errors.email}
  aria-describedby={errors.email ? "email-error" : undefined}
/>
{errors.email && (
  <p id="email-error" className="text-red-500 text-sm" role="alert">
    {errors.email}
  </p>
)}
```

### Pattern 3: Skip Link

```typescript
// Add to layout
<a
  href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-4"
>
  Skip to main content
</a>

<main id="main-content">
  {/* Page content */}
</main>
```

### Pattern 4: Modal Focus Trap

```typescript
// Modal component with focus management
const Modal = ({ isOpen, onClose, children }) => {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && modalRef.current) {
      const firstFocusable = modalRef.current.querySelector<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      firstFocusable?.focus();
    }
  }, [isOpen]);

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      ref={modalRef}
      onKeyDown={handleKeyDown}
    >
      <h2 id="modal-title">{title}</h2>
      {children}
    </div>
  );
};
```

### Pattern 5: Semantic HTML

```typescript
// ❌ Bad
<div className="card" onClick={handleClick}>
  <div className="title">Product</div>
  <div className="description">...</div>
</div>

// ✅ Good
<article className="card">
  <h3 className="title">Product</h3>
  <p className="description">...</p>
  <button onClick={handleClick}>View Details</button>
</article>
```

### Pattern 6: Keyboard Navigation

```typescript
const handleKeyDown = (e: React.KeyboardEvent) => {
  switch(e.key) {
    case 'ArrowDown':
      e.preventDefault();
      focusNext();
      break;
    case 'ArrowUp':
      e.preventDefault();
      focusPrevious();
      break;
    case 'Home':
      e.preventDefault();
      focusFirst();
      break;
    case 'End':
      e.preventDefault();
      focusLast();
      break;
  }
};
```

## Priority Files to Fix

### Critical (Week 1)
1. `components/ui/button.tsx` - Base button component
2. `components/ui/input.tsx` - Base input component
3. `components/ui/modal.tsx` - Modal/dialog component
4. `app/dashboard/layout.tsx` - Main layout with navigation

### High (Week 2)
5. `app/dashboard/page.tsx` - Dashboard homepage
6. `app/dashboard/operations/customers/page.tsx` - Customer management
7. `app/dashboard/billing-revenue/page.tsx` - Billing dashboard
8. `components/customers/CreateCustomerModal.tsx` - Complex form

### Medium (Week 3)
9. All remaining dashboard pages
10. Settings pages
11. Infrastructure pages

## Testing Strategy

### 1. Automated Testing

```bash
# Install dependencies
pnpm add -D @axe-core/react jest-axe @testing-library/jest-dom

# Run tests
pnpm test -- --testPathPattern=a11y
```

### 2. Manual Testing Checklist

- [ ] Navigate entire app with keyboard only
- [ ] Test with screen reader (NVDA/JAWS/VoiceOver)
- [ ] Test with 200% zoom
- [ ] Test with high contrast mode
- [ ] Test with browser zoom
- [ ] Test form validation messages
- [ ] Test modal focus trapping
- [ ] Test skip links

### 3. Browser Extensions

- **axe DevTools** - Automated scanning
- **WAVE** - Visual accessibility feedback
- **Lighthouse** - Accessibility audit
- **Tab Order Highlighter** - Tab order visualization

## Success Metrics

- [ ] **100%** of buttons have accessible labels
- [ ] **100%** of forms have proper labels
- [ ] **100%** of images have alt text
- [ ] **0** critical WCAG violations
- [ ] **0** serious WCAG violations
- [ ] **<5** moderate WCAG violations
- [ ] **Lighthouse Accessibility Score**: ≥95
- [ ] **Keyboard Navigation**: All functions accessible
- [ ] **Screen Reader**: All content readable

## Timeline

| Week | Focus | Hours | Deliverable |
|------|-------|-------|-------------|
| 1 | Core components + tooling | 12 | Accessible Button, Input, Modal |
| 2 | Dashboard pages | 12 | Main pages keyboard accessible |
| 3 | Settings & Operations | 12 | All pages keyboard accessible |
| 4 | Testing & documentation | 4 | Full compliance + docs |

**Total**: 40 hours

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [a11y Project Checklist](https://www.a11yproject.com/checklist/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)

---

**Status**: 📋 Planning Complete
**Next Step**: Implement core accessible components
**Priority**: CRITICAL - Impacts all users
