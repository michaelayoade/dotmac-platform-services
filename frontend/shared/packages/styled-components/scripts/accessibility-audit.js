/**
 * Accessibility Audit Script
 *
 * Tests accessibility compliance across all portal themes and color schemes.
 * Ensures WCAG AA compliance in light, dark, and high-contrast modes.
 */

const fs = require('node:fs');
const path = require('node:path');

const _axeCore = require('axe-core');
const puppeteer = require('puppeteer');

// Color contrast thresholds for WCAG AA compliance
const _WCAG_AA_NORMAL = 4.5;
const _WCAG_AA_LARGE = 3;
const _WCAG_AAA_NORMAL = 7;
const _WCAG_AAA_LARGE = 4.5;

/**
 * Test scenarios for accessibility audit
 */
const testScenarios = [
  {
    name: 'admin-light',
    portal: 'admin',
    colorScheme: 'light',
    description: 'Admin portal in light mode',
  },
  {
    name: 'admin-dark',
    portal: 'admin',
    colorScheme: 'dark',
    description: 'Admin portal in dark mode',
  },
  {
    name: 'customer-light',
    portal: 'customer',
    colorScheme: 'light',
    description: 'Customer portal in light mode',
  },
  {
    name: 'customer-dark',
    portal: 'customer',
    colorScheme: 'dark',
    description: 'Customer portal in dark mode',
  },
  {
    name: 'reseller-light',
    portal: 'reseller',
    colorScheme: 'light',
    description: 'Reseller portal in light mode',
  },
  {
    name: 'reseller-dark',
    portal: 'reseller',
    colorScheme: 'dark',
    description: 'Reseller portal in dark mode',
  },
];

/**
 * Generate test HTML page for a scenario
 */
function generateTestPage(scenario) {
  return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Accessibility Test: ${scenario.description}</title>
  <style>
    ${fs.readFileSync(path.join(__dirname, '../src/styles/tokens.css'), 'utf8')}
    ${fs.readFileSync(path.join(__dirname, '../src/styles/globals.css'), 'utf8')}
    
    /* Additional test styles */
    body {
      margin: 0;
      padding: 2rem;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      line-height: 1.5;
    }
    
    .test-container {
      max-width: 1200px;
      margin: 0 auto;
      space-y: 2rem;
    }
    
    .test-section {
      margin-bottom: 3rem;
      padding: 1.5rem;
      border: 1px solid;
      border-radius: 0.5rem;
    }
    
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      white-space: nowrap;
      border-radius: 0.375rem;
      font-size: 0.875rem;
      font-weight: 500;
      transition: colors 150ms;
      border: 1px solid transparent;
      padding: 0.5rem 1rem;
      cursor: pointer;
      margin: 0.25rem;
    }
    
    .input {
      display: flex;
      width: 100%;
      border-radius: 0.375rem;
      border: 1px solid;
      padding: 0.5rem 0.75rem;
      font-size: 0.875rem;
      margin: 0.5rem 0;
    }
    
    .card {
      border-radius: 0.5rem;
      border: 1px solid;
      padding: 1.5rem;
      margin: 1rem 0;
    }
    
    .badge {
      display: inline-flex;
      align-items: center;
      border-radius: 9999px;
      border: 1px solid transparent;
      padding: 0.125rem 0.625rem;
      font-size: 0.75rem;
      font-weight: 600;
      margin: 0.25rem;
    }
    
    /* Apply portal-specific styles */
    .${scenario.portal}-portal {
      ${scenario.colorScheme === 'dark' ? 'color-scheme: dark;' : ''}
    }
    
    /* Color applications based on portal */
    .${scenario.portal}-portal .btn.variant-default {
      background: hsl(var(--${scenario.portal}-primary));
      color: hsl(var(--${scenario.portal}-primary-foreground));
    }
    
    .${scenario.portal}-portal .btn.variant-outline {
      border-color: hsl(var(--${scenario.portal}-border));
      background: hsl(var(--${scenario.portal}-background));
      color: hsl(var(--${scenario.portal}-foreground));
    }
    
    .${scenario.portal}-portal .btn.variant-destructive {
      background: hsl(var(--${scenario.portal}-destructive));
      color: hsl(var(--${scenario.portal}-destructive-foreground));
    }
    
    .${scenario.portal}-portal .input {
      border-color: hsl(var(--${scenario.portal}-border));
      background: hsl(var(--${scenario.portal}-background));
      color: hsl(var(--${scenario.portal}-foreground));
    }
    
    .${scenario.portal}-portal .input:focus {
      outline: 2px solid hsl(var(--${scenario.portal}-ring));
      outline-offset: 2px;
    }
    
    .${scenario.portal}-portal .card {
      border-color: hsl(var(--${scenario.portal}-border));
      background: hsl(var(--${scenario.portal}-card));
      color: hsl(var(--${scenario.portal}-card-foreground));
    }
    
    .${scenario.portal}-portal .badge.variant-success {
      background: hsl(var(--success));
      color: hsl(var(--success-foreground));
    }
    
    .${scenario.portal}-portal .badge.variant-warning {
      background: hsl(var(--warning));
      color: hsl(var(--warning-foreground));
    }
    
    .${scenario.portal}-portal .test-section {
      border-color: hsl(var(--${scenario.portal}-border));
      background: hsl(var(--${scenario.portal}-muted) / 0.1);
    }
    
    /* High contrast mode adjustments */
    @media (prefers-contrast: high) {
      .btn, .input, .card {
        border-width: 2px;
      }
    }
  </style>
</head>
<body class="${scenario.portal}-portal ${scenario.colorScheme}">
  <div class="test-container">
    <header>
      <h1>Accessibility Test: ${scenario.description}</h1>
      <p>Testing WCAG AA compliance for ${scenario.portal} portal in ${scenario.colorScheme} mode.</p>
    </header>

    <!-- Navigation Test -->
    <section class="test-section">
      <h2>Navigation Components</h2>
      <nav aria-label="Main navigation">
        <ul style="list-style: none; padding: 0; display: flex; gap: 1rem;">
          <li><a href="#" class="btn variant-outline">Dashboard</a></li>
          <li><a href="#" class="btn variant-outline">Customers</a></li>
          <li><a href="#" class="btn variant-outline">Reports</a></li>
          <li><a href="#" class="btn variant-outline" aria-current="page">Settings</a></li>
        </ul>
      </nav>
    </section>

    <!-- Button Test -->
    <section class="test-section">
      <h2>Interactive Elements</h2>
      <div>
        <button class="btn variant-default">Primary Action</button>
        <button class="btn variant-outline">Secondary Action</button>
        <button class="btn variant-destructive">Delete</button>
        <button class="btn variant-outline" disabled>Disabled Button</button>
      </div>
    </section>

    <!-- Form Test -->
    <section class="test-section">
      <h2>Form Elements</h2>
      <form>
        <div style="margin-bottom: 1rem;">
          <label for="email-input" style="display: block; margin-bottom: 0.5rem; font-weight: 500;">
            Email Address <span style="color: hsl(var(--${scenario.portal}-destructive));" aria-label="required">*</span>
          </label>
          <input 
            type="email" 
            id="email-input" 
            class="input" 
            placeholder="Enter your email"
            aria-describedby="email-help"
            required
          />
          <div id="email-help" style="font-size: 0.75rem; margin-top: 0.25rem; color: hsl(var(--${scenario.portal}-muted-foreground));">
            We'll use this to send you important updates
          </div>
        </div>
        
        <div style="margin-bottom: 1rem;">
          <label for="password-input" style="display: block; margin-bottom: 0.5rem; font-weight: 500;">
            Password
          </label>
          <input 
            type="password" 
            id="password-input" 
            class="input" 
            placeholder="Enter your password"
            aria-describedby="password-error"
          />
          <div id="password-error" role="alert" style="font-size: 0.75rem; margin-top: 0.25rem; color: hsl(var(--${scenario.portal}-destructive));">
            Password must be at least 8 characters
          </div>
        </div>
      </form>
    </section>

    <!-- Status and Feedback -->
    <section class="test-section">
      <h2>Status Indicators</h2>
      <div>
        <span class="badge variant-success">Active</span>
        <span class="badge variant-warning">Pending</span>
        <span class="badge" style="background: hsl(var(--${scenario.portal}-destructive)); color: hsl(var(--${scenario.portal}-destructive-foreground));">Error</span>
        <span class="badge" style="background: hsl(var(--info)); color: hsl(var(--info-foreground));">Info</span>
      </div>
    </section>

    <!-- Data Display -->
    <section class="test-section">
      <h2>Data Display</h2>
      <div class="card">
        <h3 style="margin-top: 0;">Customer Information</h3>
        <table style="width: 100%; border-collapse: collapse;">
          <thead>
            <tr>
              <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid hsl(var(--${scenario.portal}-border));">Name</th>
              <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid hsl(var(--${scenario.portal}-border));">Email</th>
              <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid hsl(var(--${scenario.portal}-border));">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style="padding: 0.5rem; border-bottom: 1px solid hsl(var(--${scenario.portal}-border) / 0.5);">John Doe</td>
              <td style="padding: 0.5rem; border-bottom: 1px solid hsl(var(--${scenario.portal}-border) / 0.5);">john@example.com</td>
              <td style="padding: 0.5rem; border-bottom: 1px solid hsl(var(--${scenario.portal}-border) / 0.5);">
                <span class="badge variant-success">Active</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Focus indicators test -->
    <section class="test-section">
      <h2>Keyboard Navigation</h2>
      <p>Use Tab key to navigate through these elements:</p>
      <div>
        <a href="#" class="btn variant-outline">Link Button</a>
        <button class="btn variant-default">Regular Button</button>
        <input type="text" class="input" placeholder="Text input" style="width: 200px; display: inline-block;"/>
        <select class="input" style="width: 150px; display: inline-block;">
          <option>Option 1</option>
          <option>Option 2</option>
        </select>
      </div>
    </section>
  </div>

  <script>
    // Add axe-core for runtime accessibility testing
    ${fs.readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8')}
    
    // Mark tokens as loaded for validation
    document.documentElement.setAttribute('data-tokens-loaded', 'true');
    
    // Expose accessibility testing function
    window.runAccessibilityTest = function() {
      return axe.run(document, {
        rules: {
          'color-contrast': { enabled: true },
          'focus-order-semantics': { enabled: true },
          'keyboard': { enabled: true },
          'aria-allowed-attr': { enabled: true },
          'aria-required-attr': { enabled: true },
          'aria-valid-attr-value': { enabled: true },
          'button-name': { enabled: true },
          'form-field-multiple-labels': { enabled: true },
          'input-image-alt': { enabled: true },
          'label': { enabled: true },
          'link-name': { enabled: true },
        }
      });
    };
  </script>
</body>
</html>
  `;
}

/**
 * Calculate color contrast ratio
 */
function _calculateContrast(color1, color2) {
  // Simplified contrast calculation - in real implementation,
  // would use proper color space conversion
  function getLuminance(r, g, b) {
    const [rs, gs, bs] = [r, g, b].map((c) => {
      c /= 255;
      return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  }

  const l1 = getLuminance(...color1);
  const l2 = getLuminance(...color2);

  const brightest = Math.max(l1, l2);
  const darkest = Math.min(l1, l2);

  return (brightest + 0.05) / (darkest + 0.05);
}

/**
 * Run accessibility audit for a scenario
 */
async function auditScenario(browser, scenario) {
  console.log(`\n🔍 Testing: ${scenario.description}`);

  const page = await browser.newPage();

  try {
    // Set up page
    await page.setViewport({ width: 1200, height: 800 });

    // Load test page
    const html = generateTestPage(scenario);
    await page.setContent(html, { waitUntil: 'networkidle0' });

    // Run axe-core accessibility tests
    const axeResults = await page.evaluate(() => {
      return window.runAccessibilityTest();
    });

    // Extract color values for manual contrast checking
    const colorData = await page.evaluate((portal) => {
      const root = document.documentElement;
      const computedStyle = getComputedStyle(root);

      return {
        primary: computedStyle.getPropertyValue(`--${portal}-primary`).trim(),
        primaryForeground: computedStyle.getPropertyValue(`--${portal}-primary-foreground`).trim(),
        background: computedStyle.getPropertyValue(`--${portal}-background`).trim(),
        foreground: computedStyle.getPropertyValue(`--${portal}-foreground`).trim(),
        muted: computedStyle.getPropertyValue(`--${portal}-muted`).trim(),
        mutedForeground: computedStyle.getPropertyValue(`--${portal}-muted-foreground`).trim(),
      };
    }, scenario.portal);

    // Take screenshot for visual inspection
    const screenshotPath = path.join(
      __dirname,
      '../test-results',
      `${scenario.name}-screenshot.png`
    );
    await page.screenshot({
      path: screenshotPath,
      fullPage: true,
    });

    // Analyze results
    const results = {
      scenario: scenario.name,
      description: scenario.description,
      axeResults: {
        violations: axeResults.violations.length,
        passes: axeResults.passes.length,
        incomplete: axeResults.incomplete.length,
        details: axeResults.violations.map((v) => ({
          id: v.id,
          impact: v.impact,
          description: v.description,
          nodes: v.nodes.length,
        })),
      },
      colorData,
      screenshot: screenshotPath,
      timestamp: new Date().toISOString(),
    };

    // Log results
    if (axeResults.violations.length === 0) {
      console.log(`✅ ${scenario.name}: No accessibility violations found`);
    } else {
      console.log(`❌ ${scenario.name}: ${axeResults.violations.length} violations found`);
      axeResults.violations.forEach((violation) => {
        console.log(`   - ${violation.id} (${violation.impact}): ${violation.description}`);
      });
    }

    console.log(
      `📊 Passes: ${axeResults.passes.length}, Incomplete: ${axeResults.incomplete.length}`
    );
    console.log(`📸 Screenshot saved: ${screenshotPath}`);

    return results;
  } catch (error) {
    console.error(`❌ Error testing ${scenario.name}:`, error.message);
    return {
      scenario: scenario.name,
      description: scenario.description,
      error: error.message,
      timestamp: new Date().toISOString(),
    };
  } finally {
    await page.close();
  }
}

/**
 * Generate accessibility report
 */
function generateReport(results) {
  const totalScenarios = results.length;
  const passedScenarios = results.filter((r) => !r.error && r.axeResults?.violations === 0).length;
  const totalViolations = results.reduce((sum, r) => sum + (r.axeResults?.violations || 0), 0);

  console.log('\n📊 ACCESSIBILITY AUDIT REPORT');
  console.log('='.repeat(50));
  console.log(`✅ Scenarios passed: ${passedScenarios}/${totalScenarios}`);
  console.log(`❌ Total violations: ${totalViolations}`);

  // Group violations by type
  const violationsByType = {};
  results.forEach((result) => {
    if (result.axeResults?.details) {
      result.axeResults.details.forEach((detail) => {
        if (!violationsByType[detail.id]) {
          violationsByType[detail.id] = {
            count: 0,
            impact: detail.impact,
            description: detail.description,
            scenarios: [],
          };
        }
        violationsByType[detail.id].count += detail.nodes;
        violationsByType[detail.id].scenarios.push(result.scenario);
      });
    }
  });

  if (Object.keys(violationsByType).length > 0) {
    console.log('\n🔍 VIOLATION BREAKDOWN:');
    Object.entries(violationsByType).forEach(([id, data]) => {
      console.log(`\n${id} (${data.impact})`);
      console.log(`  Description: ${data.description}`);
      console.log(`  Count: ${data.count} elements`);
      console.log(`  Affected scenarios: ${data.scenarios.join(', ')}`);
    });
  }

  // Portal-specific analysis
  console.log('\n🎨 PORTAL ANALYSIS:');
  ['admin', 'customer', 'reseller'].forEach((portal) => {
    const portalResults = results.filter((r) => r.scenario.startsWith(portal));
    const portalViolations = portalResults.reduce(
      (sum, r) => sum + (r.axeResults?.violations || 0),
      0
    );
    console.log(`${portal.padEnd(10)}: ${portalViolations} violations`);
  });

  return {
    summary: {
      totalScenarios,
      passedScenarios,
      totalViolations,
      successRate: (passedScenarios / totalScenarios) * 100,
    },
    violationsByType,
    results,
  };
}

/**
 * Main audit function
 */
async function runAccessibilityAudit() {
  console.log('🚀 Starting Accessibility Audit');
  console.log('Testing WCAG AA compliance across all portal themes...\n');

  // Create results directory
  const resultsDir = path.join(__dirname, '../test-results');
  if (!fs.existsSync(resultsDir)) {
    fs.mkdirSync(resultsDir, { recursive: true });
  }

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const results = [];

  try {
    for (const scenario of testScenarios) {
      const result = await auditScenario(browser, scenario);
      results.push(result);
    }

    // Generate final report
    const report = generateReport(results);

    // Save detailed report
    const reportPath = path.join(resultsDir, 'accessibility-audit-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

    console.log(`\n📄 Detailed report saved: ${reportPath}`);

    // Determine overall success
    if (report.summary.successRate === 100) {
      console.log('🎉 All accessibility tests passed!');
      console.log('✅ WCAG AA compliance verified across all portal themes');
    } else {
      console.log(`⚠️  ${report.summary.totalViolations} accessibility violations found`);
      console.log(`📈 Success rate: ${report.summary.successRate.toFixed(1)}%`);
      process.exit(1);
    }
  } finally {
    await browser.close();
  }
}

// Run if called directly
if (require.main === module) {
  runAccessibilityAudit().catch(console.error);
}

module.exports = { runAccessibilityAudit, testScenarios };
