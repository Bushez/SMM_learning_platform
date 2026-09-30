import { defineConfig } from "orval";

export default defineConfig({
  api: {
    input: "../openapi.json",
    output: {
      mode: "tags-split",
      target: "src/shared/api/generated/client.ts",
      schemas: "src/shared/api/generated/models",
      client: "react-query",
      httpClient: "fetch",
      clean: true,
      override: {
        mutator: {
          path: "src/shared/api/http-client.ts",
          name: "apiFetch",
        },
      },
    },
  },
});
