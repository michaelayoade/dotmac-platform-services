#!/usr/bin/env node

/**
 * Migration Script: MUI to DotMac Primitives
 *
 * This script automatically migrates Material-UI imports and components
 * to DotMac Primitives equivalents.
 *
 * Usage: node migrate-mui-to-primitives.js [path]
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

// Import migration maps
const {
  iconMigrationMap,
  componentNameMap,
  propMigrationMap
} = require('./mui-to-primitives-migration.ts');

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function migrateFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let modified = false;
  const changes = [];

  // Track imports to be replaced
  const muiImports = new Map();
  const iconImports = new Map();

  // 1. Find and collect MUI imports
  const muiImportRegex = /import\s+{([^}]+)}\s+from\s+['"]@mui\/material(?:\/([^'"]+))?['"]/g;
  const muiIconImportRegex = /import\s+(?:{([^}]+)}|(\w+))\s+from\s+['"]@mui\/icons-material(?:\/([^'"]+))?['"]/g;

  // Collect MUI component imports
  let match;
  while ((match = muiImportRegex.exec(content)) !== null) {
    const imports = match[1].split(',').map(i => i.trim());
    imports.forEach(imp => {
      muiImports.set(imp, true);
    });
  }

  // Collect MUI icon imports
  content.replace(muiIconImportRegex, (fullMatch, namedImports, defaultImport, iconPath) => {
    if (namedImports) {
      const imports = namedImports.split(',').map(i => i.trim());
      imports.forEach(imp => {
        iconImports.set(imp, iconMigrationMap[imp] || imp);
      });
    } else if (defaultImport) {
      iconImports.set(defaultImport, iconMigrationMap[defaultImport] || defaultImport);
    } else if (iconPath) {
      const iconName = iconPath;
      iconImports.set(iconName, iconMigrationMap[iconName] || iconName);
    }
    return fullMatch;
  });

  // 2. Replace MUI imports with Primitives imports
  if (muiImports.size > 0) {
    // Remove all MUI imports
    content = content.replace(/import\s+{[^}]+}\s+from\s+['"]@mui\/material(?:\/[^'"]+)?['"];?\n?/g, '');

    // Add primitives import
    const primitivesImports = Array.from(muiImports.keys())
      .map(imp => componentNameMap[imp] || imp)
      .filter(imp => imp !== 'div' && imp !== 'ul' && imp !== 'li' && imp !== 'span' && imp !== 'header' && imp !== 'nav' && imp !== 'option');

    if (primitivesImports.length > 0) {
      const importStatement = `import { ${primitivesImports.join(', ')} } from '@dotmac/primitives';\n`;

      // Add import after existing imports or at the beginning
      const firstImportMatch = content.match(/^import\s+/m);
      if (firstImportMatch) {
        const insertPosition = content.indexOf(firstImportMatch[0]);
        content = content.slice(0, insertPosition) + importStatement + content.slice(insertPosition);
      } else {
        content = importStatement + content;
      }

      changes.push(`Added primitives import: ${primitivesImports.join(', ')}`);
      modified = true;
    }
  }

  // 3. Replace MUI icon imports with Lucide icons
  if (iconImports.size > 0) {
    // Remove all MUI icon imports
    content = content.replace(/import\s+(?:{[^}]+}|\w+)\s+from\s+['"]@mui\/icons-material(?:\/[^'"]+)?['"];?\n?/g, '');

    // Add lucide-react import
    const lucideIcons = Array.from(iconImports.values()).filter(Boolean);
    if (lucideIcons.length > 0) {
      const lucideImport = `import { ${lucideIcons.join(', ')} } from 'lucide-react';\n`;

      // Add import after existing imports or at the beginning
      const firstImportMatch = content.match(/^import\s+/m);
      if (firstImportMatch) {
        const insertPosition = content.indexOf(firstImportMatch[0]);
        content = content.slice(0, insertPosition) + lucideImport + content.slice(insertPosition);
      } else {
        content = lucideImport + content;
      }

      changes.push(`Added lucide icons: ${lucideIcons.join(', ')}`);
      modified = true;
    }
  }

  // 4. Replace component usage in JSX
  muiImports.forEach((_, componentName) => {
    const newName = componentNameMap[componentName];
    if (newName && newName !== componentName) {
      // Replace opening tags
      const openTagRegex = new RegExp(`<${componentName}([\\s>])`, 'g');
      content = content.replace(openTagRegex, `<${newName}$1`);

      // Replace closing tags
      const closeTagRegex = new RegExp(`</${componentName}>`, 'g');
      content = content.replace(closeTagRegex, `</${newName}>`);

      // Replace self-closing tags
      const selfCloseRegex = new RegExp(`<${componentName}([^>]*/)>`, 'g');
      content = content.replace(selfCloseRegex, `<${newName}$1>`);

      changes.push(`Replaced ${componentName} with ${newName}`);
      modified = true;
    }
  });

  // 5. Replace icon component usage
  iconImports.forEach((lucideName, muiName) => {
    if (lucideName && lucideName !== muiName) {
      // Replace in JSX
      const iconRegex = new RegExp(`<${muiName}([\\s/>])`, 'g');
      content = content.replace(iconRegex, `<${lucideName}$1`);

      // Replace closing tags if any
      const closeRegex = new RegExp(`</${muiName}>`, 'g');
      content = content.replace(closeRegex, `</${lucideName}>`);

      changes.push(`Replaced icon ${muiName} with ${lucideName}`);
      modified = true;
    }
  });

  // 6. Migrate common props
  // Button props
  content = content.replace(/variant=["']contained["']/g, 'variant="default"');
  content = content.replace(/variant=["']outlined["']/g, 'variant="outline"');
  content = content.replace(/variant=["']text["']/g, 'variant="ghost"');

  // Color props to variants
  content = content.replace(/color=["']primary["']/g, 'variant="default"');
  content = content.replace(/color=["']secondary["']/g, 'variant="secondary"');
  content = content.replace(/color=["']error["']/g, 'variant="destructive"');

  // Size props
  content = content.replace(/size=["']small["']/g, 'size="sm"');
  content = content.replace(/size=["']medium["']/g, 'size="default"');
  content = content.replace(/size=["']large["']/g, 'size="lg"');

  // Icon props
  content = content.replace(/startIcon=/g, 'leftIcon=');
  content = content.replace(/endIcon=/g, 'rightIcon=');

  // TextField to Input
  content = content.replace(/<TextField/g, '<Input');
  content = content.replace(/<\/TextField>/g, '</Input>');

  // Dialog to Modal
  content = content.replace(/<Dialog/g, '<Modal');
  content = content.replace(/<\/Dialog>/g, '</Modal>');
  content = content.replace(/<DialogTitle/g, '<ModalHeader');
  content = content.replace(/<\/DialogTitle>/g, '</ModalHeader>');
  content = content.replace(/<DialogContent/g, '<ModalBody');
  content = content.replace(/<\/DialogContent>/g, '</ModalBody>');
  content = content.replace(/<DialogActions/g, '<ModalFooter');
  content = content.replace(/<\/DialogActions>/g, '</ModalFooter>');

  // 7. Handle emotion/styled components
  content = content.replace(/import\s+styled\s+from\s+['"]@emotion\/styled['"];?\n?/g, '');
  content = content.replace(/import\s+{[^}]*css[^}]*}\s+from\s+['"]@emotion\/react['"];?\n?/g, '');

  // Add TODO for styled components that need manual migration
  if (content.includes('styled(') || content.includes('styled.')) {
    content = '// TODO: Migrate styled components to Tailwind CSS classes\n' + content;
    changes.push('Added TODO for styled components migration');
    modified = true;
  }

  // 8. Clean up empty imports
  content = content.replace(/import\s+{\s*}\s+from\s+['"][^'"]+['"];?\n?/g, '');

  // Write the modified file
  if (modified) {
    fs.writeFileSync(filePath, content);
    log(`✅ Migrated: ${path.relative(process.cwd(), filePath)}`, 'green');
    changes.forEach(change => log(`   - ${change}`, 'cyan'));
  }

  return { modified, changes };
}

function findAndMigrateFiles(searchPath) {
  const pattern = path.join(searchPath, '**/*.{tsx,ts,jsx,js}');
  const files = glob.sync(pattern, {
    ignore: ['**/node_modules/**', '**/dist/**', '**/.next/**', '**/build/**']
  });

  log(`\n🔍 Found ${files.length} files to check\n`, 'blue');

  let totalModified = 0;
  const allChanges = [];

  files.forEach((file) => {
    const { modified, changes } = migrateFile(file);
    if (modified) {
      totalModified++;
      allChanges.push({ file, changes });
    }
  });

  // Summary
  log(`\n✨ Migration Complete!`, 'green');
  log(`📊 Modified ${totalModified} out of ${files.length} files`, 'yellow');

  if (totalModified > 0) {
    log(`\n📝 Summary of changes:`, 'blue');
    allChanges.forEach(({ file, changes }) => {
      log(`\n${path.relative(process.cwd(), file)}:`, 'cyan');
      changes.forEach(change => log(`  - ${change}`, 'reset'));
    });
  }

  // Recommendations
  if (totalModified > 0) {
    log(`\n⚠️  Important Notes:`, 'yellow');
    log(`1. Review all migrated components for proper functionality`, 'reset');
    log(`2. Update any styled-components to use Tailwind CSS classes`, 'reset');
    log(`3. Test form components thoroughly (TextField → Input migration)`, 'reset');
    log(`4. Verify icon replacements match your UI requirements`, 'reset');
    log(`5. Check for any remaining emotion/styled imports`, 'reset');
    log(`6. Run 'pnpm type-check' to catch any TypeScript issues`, 'reset');
  }
}

// Main execution
const targetPath = process.argv[2] || 'frontend/apps/base-app';

log(`🚀 Starting MUI to Primitives migration...`, 'blue');
log(`📂 Target directory: ${targetPath}\n`, 'cyan');

if (!fs.existsSync(targetPath)) {
  log(`❌ Error: Path "${targetPath}" does not exist`, 'red');
  process.exit(1);
}

findAndMigrateFiles(targetPath);