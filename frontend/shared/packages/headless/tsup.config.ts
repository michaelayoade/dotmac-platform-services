import { defineConfig } from 'tsup';

export default defineConfig({
  entry: {
    index: 'src/index.ts',
    'utils/csp': 'src/utils/csp.ts',
    'utils/production-data-guard': 'src/utils/production-data-guard.ts',
  },
  format: ['cjs', 'esm'],
  dts: false, // Skip DTS generation due to many TS errors - will fix separately
  external: ['next/navigation', 'next/router', 'react', 'react-dom', '@dotmac/primitives'],
  clean: true,
  splitting: false,
  sourcemap: true,
  treeshake: true,
  skipNodeModulesBundle: true,
  esbuildOptions(options) {
    options.logLevel = 'error'; // Only show errors
  },
});
