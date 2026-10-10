import { z } from "zod";

import messages from "../../../messages/ru.json";

export const loginSchema = z.object({
  email: z.string().trim().email(),
  password: z.string().min(1).max(128),
});

export const registerSchema = loginSchema.extend({
  password: z.string().min(10).max(128),
  displayName: z.string().trim().min(2).max(80),
});

export type LoginValues = z.infer<typeof loginSchema>;
export type RegisterValues = z.infer<typeof registerSchema>;
export type AuthField = "email" | "password" | "displayName";

type ApiValidationDetail = {
  loc?: unknown;
};

type ApiErrorLike = {
  code: string;
  details?: unknown;
};

export function messageForAuthField(field: AuthField): string {
  if (field === "email") return messages.auth.invalidEmail;
  if (field === "password") return messages.auth.invalidPassword;
  return messages.auth.invalidDisplayName;
}

export function fieldFromValidationPath(path: unknown): AuthField | null {
  if (!Array.isArray(path)) return null;
  const name = path.at(-1);
  if (name === "email" || name === "password") return name;
  if (name === "displayName" || name === "display_name") return "displayName";
  return null;
}

export function getApiAuthError(error: ApiErrorLike): { field?: AuthField; message: string } {
  if (error.code === "conflict") {
    return { field: "email", message: messages.auth.emailExists };
  }
  if (error.code === "authentication_failed") {
    return { message: messages.auth.invalidCredentials };
  }
  if (error.code === "validation_error" && Array.isArray(error.details)) {
    const detail = error.details[0] as ApiValidationDetail | undefined;
    const field = fieldFromValidationPath(detail?.loc);
    if (field) return { field, message: messageForAuthField(field) };
  }
  return { message: messages.auth.genericError };
}
