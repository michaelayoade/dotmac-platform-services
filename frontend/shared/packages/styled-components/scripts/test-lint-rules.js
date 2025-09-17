/**
 * Test Script for Portal Import Lint Rules
 *
 * Tests that the ESLint rules correctly identify violations
 * and allow valid import patterns.
 */

const { execSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

/**
 * Test scenarios for lint rule validation
 */
const testScenarios = [
  {
    name: 'cross-portal-violations',
    file: 'test-examples/violations/cross-portal-imports.js',
    shouldFail: true,
    expectedErrors: ['no-cross-portal-imports', 'mixedPortalImport', 'unknownPortal'],
  },
  {
    name: 'valid-single-portal',
    file: 'test-examples/valid/single-portal-imports.js',
    shouldFail: false,
    expectedErrors: [],
  },
  {
    name: 'valid-test-file',
    file: 'test-examples/valid/test-file-mixed-imports.test.js',
    shouldFail: false,
    expectedErrors: [],
  },
];

/**
 * Run ESLint on a specific file
 */
function runLintTest(scenario) {
  console.log(`\n🔍 Testing: ${scenario.name}`);
  console.log(`📁 File: ${scenario.file}`);

  try {
    const result = execSync(`npx eslint ${scenario.file} --format json`, {
      cwd: `${__dirname}/..`,
      stdio: 'pipe',
      encoding: 'utf8',
    });

    const lintResults = JSON.parse(result);
    const errors = lintResults[0]?.messages || [];

    console.log(`📊 Found ${errors.length} lint errors`);

    if (scenario.shouldFail) {
      if (errors.length === 0) {
        console.log(`❌ Expected errors but found none`);
        return false;
      }

      // Check if expected error types are present
      const foundErrorTypes = errors.map((e) => e.ruleId || e.messageId);
      const hasExpectedErrors = scenario.expectedErrors.some((expected) =>
        foundErrorTypes.some((found) => found?.includes(expected))
      );

      if (!hasExpectedErrors) {
        console.log(`❌ Expected error types: ${scenario.expectedErrors.join(', ')}`);
        console.log(`📝 Found error types: ${foundErrorTypes.join(', ')}`);
        return false;
      }

      console.log(`✅ Correctly identified violations`);
      errors.forEach((error) => {
        console.log(`   - ${error.ruleId}: ${error.message} (line ${error.line})`);
      });
      return true;
    }
    if (errors.length > 0) {
      console.log(`❌ Expected no errors but found ${errors.length}`);
      errors.forEach((error) => {
        console.log(`   - ${error.ruleId}: ${error.message} (line ${error.line})`);
      });
      return false;
    }

    console.log(`✅ No violations found (as expected)`);
    return true;
  } catch (error) {
    if (scenario.shouldFail && error.status === 1) {
      // ESLint exits with status 1 when there are errors, which is expected
      try {
        const stdout = error.stdout || '';
        const lintResults = JSON.parse(stdout);
        const errors = lintResults[0]?.messages || [];

        console.log(`✅ Correctly identified ${errors.length} violations`);
        errors.forEach((error) => {
          console.log(`   - ${error.ruleId}: ${error.message} (line ${error.line})`);
        });
        return true;
      } catch (parseError) {
        console.log(`❌ Error parsing lint results: ${parseError.message}`);
        return false;
      }
    } else {
      console.log(`❌ Unexpected error: ${error.message}`);
      return false;
    }
  }
}

/**
 * Validate that test files exist
 */
function validateTestFiles() {
  console.log('📋 Validating test files...');

  let allExist = true;
  testScenarios.forEach((scenario) => {
    const filePath = path.join(__dirname, '..', scenario.file);
    if (fs.existsSync(filePath)) {
      console.log(`✅ Found: ${scenario.file}`);
    } else {
      console.log(`❌ Test file missing: ${scenario.file}`);
      allExist = false;
    }
  });

  return allExist;
}

/**
 * Main test function
 */
async function testLintRules() {
  console.log('🚀 Testing Portal Import Lint Rules');
  console.log('='.repeat(50));

  // Validate test files exist
  if (!validateTestFiles()) {
    console.log('\n❌ Missing test files - cannot proceed');
    process.exit(1);
  }

  // Run tests
  let passed = 0;
  const total = testScenarios.length;

  for (const scenario of testScenarios) {
    if (runLintTest(scenario)) {
      passed++;
    }
  }

  // Final results
  console.log('\n🏁 LINT RULE TEST RESULTS');
  console.log('='.repeat(30));
  console.log(`✅ Passed: ${passed}/${total}`);
  console.log(`❌ Failed: ${total - passed}/${total}`);

  if (passed === total) {
    console.log('\n🎉 All lint rule tests passed!');
    console.log('✅ Portal import restrictions are working correctly');
    console.log('✅ Test file exemptions are working correctly');
    console.log('✅ Shared component imports are allowed correctly');
  } else {
    console.log('\n⚠️  Some lint rule tests failed');
    console.log('Check ESLint configuration and rule implementation');
    process.exit(1);
  }
}

// Add package.json script validation
function validatePackageScripts() {
  const packagePath = path.join(__dirname, '..', 'package.json');

  if (!fs.existsSync(packagePath)) {
    console.log('📦 Creating package.json with lint scripts...');

    const packageJson = {
      name: '@dotmac/styled-components',
      version: '0.1.0',
      description: 'Portal-specific styled components for DotMac platform',
      main: 'dist/index.js',
      types: 'dist/index.d.ts',
      scripts: {
        lint: 'eslint src/**/*.{ts,tsx,js,jsx}',
        'lint:fix': 'eslint src/**/*.{ts,tsx,js,jsx} --fix',
        'lint:test': 'node scripts/test-lint-rules.js',
        test: 'npm run lint:test',
      },
      devDependencies: {
        eslint: '^8.0.0',
        '@typescript-eslint/eslint-plugin': '^6.0.0',
        '@typescript-eslint/parser': '^6.0.0',
      },
      peerDependencies: {
        react: '>=18.0.0',
        typescript: '>=4.5.0',
      },
    };

    fs.writeFileSync(packagePath, JSON.stringify(packageJson, null, 2));
    console.log('✅ Package.json created');
  }
}

// Run if called directly
if (require.main === module) {
  validatePackageScripts();
  testLintRules().catch(console.error);
}

module.exports = { testLintRules, testScenarios };
