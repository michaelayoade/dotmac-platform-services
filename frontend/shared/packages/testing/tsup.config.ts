import { defineConfig } from 'tsup';

export default defineConfig({
  entry: {
    index: 'src/index.ts',
    'jest/setup': 'src/jest/setup.ts',
    'utils/matchers': 'src/utils/matchers.ts',
    'utils/render': 'src/utils/render.tsx',
  },
  format: ['cjs', 'esm'],
  dts: true,
  splitting: false,
  sourcemap: true,
  clean: true,
  minify: false,
  external: ['react', 'react-dom', 'jest', '@testing-library/react', '@testing-library/jest-dom'],
});
