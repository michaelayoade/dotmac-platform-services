import { defineConfig } from 'tsup';

export default defineConfig({
  entry: {
    index: 'src/index.ts',
    hooks: 'src/hooks/index.ts',
    components: 'src/components/index.ts',
    services: 'src/services/index.ts',
    utils: 'src/utils/index.ts',
  },
  format: ['cjs', 'esm'],
  dts: false, // Disable DTS generation for now
  splitting: false,
  sourcemap: true,
  clean: true,
  external: [
    'react',
    'react-dom',
    '@dotmac/headless',
    '@dotmac/primitives',
    '@dotmac/providers',
    '@dotmac/dashboard',
    'recharts',
    'd3',
    'lodash',
    'date-fns',
  ],
  treeshake: true,
  minify: false,
});
