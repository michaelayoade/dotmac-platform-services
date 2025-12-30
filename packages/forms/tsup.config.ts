import { defineConfig } from "tsup";

export default defineConfig({
  entry: {
    index: "src/index.ts",
    zod: "src/adapters/zod.ts",
    yup: "src/adapters/yup.ts",
  },
  format: ["cjs", "esm"],
  dts: true,
  splitting: true,
  sourcemap: true,
  clean: true,
  external: ["react", "react-dom", "zod", "yup"],
  treeshake: true,
});
