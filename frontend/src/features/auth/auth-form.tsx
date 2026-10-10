"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import messages from "../../../messages/ru.json";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-provider";
import { ApiError, apiFetch } from "@/shared/api/http-client";
import { siteConfig } from "@/shared/config/site";
import {
  fieldFromValidationPath,
  getApiAuthError,
  loginSchema,
  messageForAuthField,
  registerSchema,
  type AuthField,
  type RegisterValues,
} from "@/features/auth/auth-validation";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const isLogin = mode === "login";
  const form = useForm<RegisterValues>({
    defaultValues: { email: "", password: "", displayName: "" },
  });

  async function submit(values: RegisterValues) {
    setError(null);
    form.clearErrors();
    const validation = (isLogin ? loginSchema : registerSchema).safeParse(values);
    if (!validation.success) {
      for (const issue of validation.error.issues) {
        const field = fieldFromValidationPath(issue.path);
        if (field) form.setError(field as never, { message: messageForAuthField(field) });
      }
      return;
    }
    try {
      if (isLogin) {
        await login(validation.data.email, validation.data.password);
      } else {
        const registration = validation.data as RegisterValues;
        await apiFetch("/api/v1/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: registration.email,
            password: registration.password,
            display_name: registration.displayName,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "Europe/Moscow",
            preferred_locale: "ru",
          }),
        });
        await login(registration.email, registration.password);
      }
      router.replace("/");
    } catch (submissionError) {
      if (submissionError instanceof ApiError) {
        const apiError = getApiAuthError(submissionError);
        if (apiError.field) {
          form.setError(apiError.field as never, { message: apiError.message });
        } else {
          setError(apiError.message);
        }
      } else {
        setError(messages.auth.genericError);
      }
    }
  }

  function fieldError(field: AuthField): string | undefined {
    return form.formState.errors[field]?.message as string | undefined;
  }

  const title = isLogin ? messages.auth.loginTitle : messages.auth.registerTitle;
  const description = isLogin ? messages.auth.loginDescription : messages.auth.registerDescription;

  return (
    <main className="grid min-h-screen place-items-center px-5 py-10">
      <section className="w-full max-w-md rounded-[2rem] border border-border bg-surface p-6 shadow-2xl sm:p-8">
        <Link className="eyebrow" href="/">{`← ${siteConfig.name}`}</Link>
        <h1 className="mt-6 text-3xl font-black tracking-tight">{title}</h1>
        <p className="mt-2 text-muted-foreground">{description}</p>
        <form className="mt-8 grid gap-5" onSubmit={form.handleSubmit(submit)}>
          {!isLogin && (
            <label className="grid gap-2 text-sm font-bold">
              {messages.auth.displayName}
              <input aria-describedby="display-name-hint" aria-invalid={Boolean(fieldError("displayName"))} className="field-control" maxLength={80} minLength={2} required {...form.register("displayName" as never, { onChange: () => form.clearErrors("displayName" as never) })} />
              <span className="text-xs font-medium text-muted-foreground" id="display-name-hint">{messages.auth.displayNameHint}</span>
              {fieldError("displayName") && <span className="text-xs font-bold text-danger" role="alert">{fieldError("displayName")}</span>}
            </label>
          )}
          <label className="grid gap-2 text-sm font-bold">
            {messages.auth.email}
            <input aria-describedby="email-hint" aria-invalid={Boolean(fieldError("email"))} autoComplete="email" className="field-control" maxLength={320} required type="email" {...form.register("email", { onChange: () => form.clearErrors("email") })} />
            <span className="text-xs font-medium text-muted-foreground" id="email-hint">{messages.auth.emailHint}</span>
            {fieldError("email") && <span className="text-xs font-bold text-danger" role="alert">{fieldError("email")}</span>}
          </label>
          <label className="grid gap-2 text-sm font-bold">
            {messages.auth.password}
            <input aria-describedby={isLogin ? undefined : "password-hint"} aria-invalid={Boolean(fieldError("password"))} autoComplete={isLogin ? "current-password" : "new-password"} className="field-control" maxLength={128} minLength={isLogin ? 1 : 10} required type="password" {...form.register("password", { onChange: () => form.clearErrors("password") })} />
            {!isLogin && <span className="text-xs font-medium text-muted-foreground" id="password-hint">{messages.auth.passwordHint}</span>}
            {fieldError("password") && <span className="text-xs font-bold text-danger" role="alert">{fieldError("password")}</span>}
          </label>
          {error && <p className="rounded-xl border border-danger/50 bg-danger/10 p-3 text-sm font-semibold text-danger" role="alert">{error}</p>}
          <Button disabled={form.formState.isSubmitting} type="submit">
            {isLogin ? messages.auth.submitLogin : messages.auth.submitRegister}
          </Button>
        </form>
        <Link className="mt-5 block text-center text-sm font-semibold text-secondary hover:underline" href={isLogin ? "/register" : "/login"}>
          {isLogin ? messages.auth.registerLink : messages.auth.loginLink}
        </Link>
      </section>
    </main>
  );
}
