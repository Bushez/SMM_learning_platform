import { describe, expect, it } from "vitest";

import {
  getApiAuthError,
  registerSchema,
} from "./auth-validation";

describe("registration validation", () => {
  it("requires the documented password and display-name lengths", () => {
    const result = registerSchema.safeParse({
      email: "learner@example.com",
      password: "short",
      displayName: "A",
    });

    expect(result.success).toBe(false);
  });

  it("maps a duplicate-email response to the email field", () => {
    expect(getApiAuthError({ code: "conflict" })).toEqual({
      field: "email",
      message: "На этот адрес уже зарегистрирован аккаунт. Попробуйте войти.",
    });
  });

  it("maps backend validation details to a Russian field error", () => {
    expect(
      getApiAuthError({
        code: "validation_error",
        details: [{ loc: ["body", "password"] }],
      }),
    ).toEqual({ field: "password", message: "Пароль должен содержать от 10 до 128 символов." });
  });
});
