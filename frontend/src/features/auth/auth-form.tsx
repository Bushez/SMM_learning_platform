"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import messages from "../../../messages/ru.json";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-provider";
import { ApiError, apiFetch } from "@/shared/api/http-client";
import { siteConfig } from "@/shared/config/site";

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

const registerSchema = loginSchema.extend({
  password: z.string().min(10),
  displayName: z.string().trim().min(2).max(80),
});

type LoginValues = z.infer<typeof loginSchema>;
type RegisterValues = z.infer<typeof registerSchema>;

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const isLogin = mode === "login";
  const form = useForm<LoginValues | RegisterValues>({
    defaultValues: { email: "", password: "", ...(isLogin ? {} : { displayName: "" }) },
  });

  async function submit(values: LoginValues | RegisterValues) {
    setError(null);
    try {
      if (isLogin) {
        await login(values.email, values.password);
      } else {
        const registration = registerSchema.parse(values);
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
      setError(
        submissionError instanceof ApiError
          ? submissionError.message
          : "Проверьте введённые данные и попробуйте ещё раз.",
      );
    }
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
              <input className="field-control" {...form.register("displayName" as never)} />
            </label>
          )}
          <label className="grid gap-2 text-sm font-bold">
            {messages.auth.email}
            <input autoComplete="email" className="field-control" type="email" {...form.register("email")} />
          </label>
          <label className="grid gap-2 text-sm font-bold">
            {messages.auth.password}
            <input autoComplete={isLogin ? "current-password" : "new-password"} className="field-control" type="password" {...form.register("password")} />
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
