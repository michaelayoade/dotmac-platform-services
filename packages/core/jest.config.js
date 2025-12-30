/** @type {import('jest').Config} */
export default {
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  preset: "ts-jest",
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  transform: {
    "^.+\\.tsx?$": [
      "ts-jest",
      {
        useESM: true,
        tsconfig: {
          jsx: "react-jsx",
        },
      },
    ],
  },
  transformIgnorePatterns: ["/node_modules/(?!(@dotmac)/)"],
  testMatch: ["**/__tests__/**/*.test.(ts|tsx)"],
  collectCoverageFrom: [
    "src/**/*.{ts,tsx}",
    "!src/**/*.stories.{ts,tsx}",
    "!src/**/*.d.ts",
    "!src/index.ts",
  ],
};
