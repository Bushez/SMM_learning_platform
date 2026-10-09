"use client";

import Link from "next/link";
import { ArrowRight, BookOpenCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-provider";
import { AppShell } from "@/widgets/navigation/app-shell";

export function LearningHome() {
  const { user } = useAuth();
  const destination = user ? "/courses" : "/login";
  return (
    <AppShell>
      <main className="mx-auto max-w-5xl px-5 py-12">
        <p className="eyebrow">Моё обучение</p>
        <section className="mt-5 rounded-[2rem] border border-border bg-surface p-8 sm:p-12">
          <BookOpenCheck className="size-10 text-primary" />
          <h1 className="mt-6 text-4xl font-black">Продолжайте с того места, где остановились</h1>
          <p className="mt-4 max-w-xl leading-7 text-muted-foreground">Здесь будет ваш учебный маршрут: начатые курсы, доступные уроки и текущий прогресс.</p>
          <Button className="mt-8" render={<Link href={destination} />}>
            {user ? "Открыть каталог" : "Войти"}<ArrowRight className="size-4" />
          </Button>
        </section>
      </main>
    </AppShell>
  );
}
