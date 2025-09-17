import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    '../../shared/packages/ui/src/**/*.{ts,tsx}',
    '../../shared/packages/design-system/src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#0ea5e9',
          foreground: '#f8fafc',
        },
      },
    },
  },
  plugins: [],
};

export default config;
