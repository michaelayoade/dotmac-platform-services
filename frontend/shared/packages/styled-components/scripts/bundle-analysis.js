/**
 * Bundle Analysis Script
 *
 * Analyzes bundle size and verifies tree-shaking works correctly.
 * Ensures only used portal styles are included in final bundles.
 */

const { execSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

// Test scenarios for different import patterns
const testScenarios = [
  {
    name: 'admin-only',
    description: 'Only admin portal components',
    imports: ["import { AdminButton, AdminCard } from '@dotmac/styled-components/admin';"],
    expectedInBundle: ['admin-btn', 'admin-card', '--admin-primary'],
    shouldNotInclude: ['customer-btn', 'reseller-btn', '--customer-primary', '--reseller-primary'],
  },
  {
    name: 'customer-only',
    description: 'Only customer portal components',
    imports: ["import { CustomerButton, CustomerCard } from '@dotmac/styled-components/customer';"],
    expectedInBundle: ['customer-btn', 'customer-card', '--customer-primary'],
    shouldNotInclude: ['admin-btn', 'reseller-btn', '--admin-primary', '--reseller-primary'],
  },
  {
    name: 'reseller-only',
    description: 'Only reseller portal components',
    imports: ["import { ResellerButton, ResellerCard } from '@dotmac/styled-components/reseller';"],
    expectedInBundle: ['reseller-btn', 'reseller-card', '--reseller-primary'],
    shouldNotInclude: ['admin-btn', 'customer-btn', '--admin-primary', '--customer-primary'],
  },
  {
    name: 'shared-only',
    description: 'Only shared components',
    imports: ["import { Badge, Avatar } from '@dotmac/styled-components/shared';"],
    expectedInBundle: ['badge', 'avatar'],
    shouldNotInclude: ['admin-btn', 'customer-btn', 'reseller-btn'],
  },
  {
    name: 'mixed-portals',
    description: 'Multiple portals (should include all)',
    imports: [
      "import { AdminButton } from '@dotmac/styled-components/admin';",
      "import { CustomerCard } from '@dotmac/styled-components/customer';",
      "import { Badge } from '@dotmac/styled-components/shared';",
    ],
    expectedInBundle: [
      'admin-btn',
      'customer-card',
      'badge',
      '--admin-primary',
      '--customer-primary',
    ],
    shouldNotInclude: ['--reseller-primary'], // Reseller styles should not be included
  },
];

// Create test directory
const testDir = path.join(__dirname, '../test-builds');
if (!fs.existsSync(testDir)) {
  fs.mkdirSync(testDir, { recursive: true });
}

/**
 * Create a test app for bundle analysis
 */
function createTestApp(scenario) {
  const appContent = `
import React from 'react';
import { createRoot } from 'react-dom/client';
${scenario.imports.join('\n')}

function App() {
  return (
    <div>
      <h1>Bundle Analysis Test: ${scenario.name}</h1>
      {/* Components would be used here */}
    </div>
  );
}

const root = createRoot(document.getElementById('root'));
root.render(<App />);
`;

  const packageJson = {
    name: `bundle-test-${scenario.name}`,
    version: '1.0.0',
    private: true,
    dependencies: {
      react: '^18.2.0',
      'react-dom': '^18.2.0',
      '@dotmac/styled-components': 'file:../',
    },
    devDependencies: {
      '@vitejs/plugin-react': '^4.0.0',
      vite: '^4.0.0',
      'vite-bundle-analyzer': '^0.7.0',
    },
    scripts: {
      build: 'vite build',
      analyze: 'vite-bundle-analyzer',
    },
  };

  const viteConfig = `
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { analyzer } from 'vite-bundle-analyzer';

export default defineConfig({
  plugins: [
    react(),
    analyzer({
      analyzerMode: 'json',
      reportFilename: 'bundle-report.json'
    })
  ],
  build: {
    outDir: 'dist',
    rollupOptions: {
      output: {
        manualChunks: undefined
      }
    }
  }
});
`;

  const htmlTemplate = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bundle Test: ${scenario.name}</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.jsx"></script>
</body>
</html>
`;

  const scenarioDir = path.join(testDir, scenario.name);
  if (!fs.existsSync(scenarioDir)) {
    fs.mkdirSync(scenarioDir, { recursive: true });
  }

  // Write files
  fs.writeFileSync(path.join(scenarioDir, 'package.json'), JSON.stringify(packageJson, null, 2));
  fs.writeFileSync(path.join(scenarioDir, 'vite.config.js'), viteConfig);
  fs.writeFileSync(path.join(scenarioDir, 'index.html'), htmlTemplate);

  const srcDir = path.join(scenarioDir, 'src');
  if (!fs.existsSync(srcDir)) {
    fs.mkdirSync(srcDir);
  }
  fs.writeFileSync(path.join(srcDir, 'main.jsx'), appContent);

  return scenarioDir;
}

/**
 * Build and analyze bundle
 */
async function buildAndAnalyze(scenario) {
  console.log(`\n🔍 Testing scenario: ${scenario.name}`);
  console.log(`📝 Description: ${scenario.description}`);

  const scenarioDir = createTestApp(scenario);

  try {
    // Install dependencies
    console.log('📦 Installing dependencies...');
    execSync('npm install', { cwd: scenarioDir, stdio: 'pipe' });

    // Build the bundle
    console.log('🏗️  Building bundle...');
    execSync('npm run build', { cwd: scenarioDir, stdio: 'pipe' });

    // Analyze bundle contents
    const distDir = path.join(scenarioDir, 'dist');
    const assets = fs.readdirSync(path.join(distDir, 'assets'));

    let bundleContent = '';
    assets.forEach((file) => {
      if (file.endsWith('.js') || file.endsWith('.css')) {
        const content = fs.readFileSync(path.join(distDir, 'assets', file), 'utf8');
        bundleContent += content;
      }
    });

    // Check expectations
    const results = {
      scenario: scenario.name,
      description: scenario.description,
      bundleSize: bundleContent.length,
      expectedFound: [],
      expectedMissing: [],
      unexpectedFound: [],
      passed: true,
    };

    // Check what should be included
    scenario.expectedInBundle.forEach((expected) => {
      if (bundleContent.includes(expected)) {
        results.expectedFound.push(expected);
      } else {
        results.expectedMissing.push(expected);
        results.passed = false;
      }
    });

    // Check what should NOT be included
    scenario.shouldNotInclude.forEach((unexpected) => {
      if (bundleContent.includes(unexpected)) {
        results.unexpectedFound.push(unexpected);
        results.passed = false;
      }
    });

    // Print results
    console.log(`📊 Bundle size: ${(bundleContent.length / 1024).toFixed(2)} KB`);
    console.log(`✅ Expected found: ${results.expectedFound.join(', ') || 'none'}`);

    if (results.expectedMissing.length > 0) {
      console.log(`❌ Expected but missing: ${results.expectedMissing.join(', ')}`);
    }

    if (results.unexpectedFound.length > 0) {
      console.log(`⚠️  Unexpectedly found: ${results.unexpectedFound.join(', ')}`);
    }

    console.log(
      `${results.passed ? '✅' : '❌'} ${scenario.name}: ${results.passed ? 'PASSED' : 'FAILED'}`
    );

    return results;
  } catch (error) {
    console.error(`❌ Error testing ${scenario.name}:`, error.message);
    return {
      scenario: scenario.name,
      description: scenario.description,
      error: error.message,
      passed: false,
    };
  }
}

/**
 * Generate bundle size comparison report
 */
function generateSizeReport(results) {
  console.log('\n📊 BUNDLE SIZE ANALYSIS REPORT');
  console.log('='.repeat(50));

  const sizeData = results
    .filter((r) => r.bundleSize)
    .map((r) => ({ name: r.scenario, size: r.bundleSize }))
    .sort((a, b) => a.size - b.size);

  sizeData.forEach(({ name, size }) => {
    const sizeKB = (size / 1024).toFixed(2);
    const bar = '█'.repeat(Math.max(1, Math.floor(size / 1000)));
    console.log(`${name.padEnd(20)} ${sizeKB.padStart(8)} KB ${bar}`);
  });

  // Calculate tree-shaking effectiveness
  const adminOnlySize = sizeData.find((s) => s.name === 'admin-only')?.size || 0;
  const customerOnlySize = sizeData.find((s) => s.name === 'customer-only')?.size || 0;
  const mixedSize = sizeData.find((s) => s.name === 'mixed-portals')?.size || 0;

  if (adminOnlySize && customerOnlySize && mixedSize) {
    const expectedMixedSize = adminOnlySize + customerOnlySize;
    const overhead = mixedSize - expectedMixedSize;
    const efficiency = (1 - overhead / mixedSize) * 100;

    console.log(`\n🌳 Tree-shaking efficiency: ${efficiency.toFixed(1)}%`);
    console.log(`📦 Mixed bundle overhead: ${(overhead / 1024).toFixed(2)} KB`);
  }
}

/**
 * Main analysis function
 */
async function runBundleAnalysis() {
  console.log('🚀 Starting Bundle Analysis');
  console.log('Testing tree-shaking and bundle size optimization...\n');

  const results = [];

  for (const scenario of testScenarios) {
    const result = await buildAndAnalyze(scenario);
    results.push(result);
  }

  // Generate reports
  generateSizeReport(results);

  // Overall results
  const passed = results.filter((r) => r.passed).length;
  const total = results.length;

  console.log('\n🏁 FINAL RESULTS');
  console.log('='.repeat(30));
  console.log(`✅ Passed: ${passed}/${total}`);
  console.log(`❌ Failed: ${total - passed}/${total}`);

  if (passed === total) {
    console.log('🎉 All bundle analysis tests passed!');
    console.log('✅ Tree-shaking is working correctly');
    console.log('✅ Portal styles are properly isolated');
  } else {
    console.log('⚠️  Some tests failed - check tree-shaking configuration');
    process.exit(1);
  }

  // Save detailed report
  const reportPath = path.join(testDir, 'bundle-analysis-report.json');
  fs.writeFileSync(
    reportPath,
    JSON.stringify(
      {
        timestamp: new Date().toISOString(),
        results,
        summary: {
          passed,
          total,
          success: passed === total,
        },
      },
      null,
      2
    )
  );

  console.log(`📄 Detailed report saved to: ${reportPath}`);
}

// Run if called directly
if (require.main === module) {
  runBundleAnalysis().catch(console.error);
}

module.exports = { runBundleAnalysis, testScenarios };
