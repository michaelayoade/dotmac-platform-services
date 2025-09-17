import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/index.ts'],
  format: ['cjs', 'esm'],
  dts: true,
  sourcemap: true,
  clean: true,
  minify: false,
  external: [
    'react',
    'react-dom',
    '@dotmac/ui',
    'lucide-react',
    'recharts',
    'framer-motion',
    'class-variance-authority',
    'clsx',
    'date-fns',
  ],
  esbuildOptions(options) {
    options.jsx = 'automatic';
  },
  onSuccess: async () => {
    console.log('✅ Dashboard package built successfully');
  },
});
