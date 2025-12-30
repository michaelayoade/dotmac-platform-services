import { defineConfig } from "tsup";

export default defineConfig({
  entry: {
    index: "src/index.ts",
    primitives: "src/primitives/index.ts",
    styled: "src/styled/index.ts",
  },
  format: ["cjs", "esm"],
  dts: true,
  splitting: true,
  sourcemap: true,
  clean: true,
  external: ["react", "react-dom"],
  treeshake: true,
});
