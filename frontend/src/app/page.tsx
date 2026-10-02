"use client";

import { ArrowRight, Flame, Sparkles } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import messages from "../../messages/ru.json";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-provider";
import type { GamificationSummaryResponse } from "@/shared/api/generated/models";
import { apiFetch } from "@/shared/api/http-client";
import { AppShell } from "@/widgets/navigation/app-shell";

export default function Home() {
  const { user } = useAuth();
  const summary = useQuery({ queryKey: ["gamification-summary"], queryFn: () => apiFetch<GamificationSummaryResponse>("/api/v1/users/me/gamification"), enabled: Boolean(user) });
  return <AppShell><main className="mx-auto grid max-w-7xl gap-8 px-5 py-8 lg:grid-cols-[1.45fr_0.75fr] lg:px-8 lg:py-12"><section className="overflow-hidden rounded-[2rem] border border-border bg-surface shadow-2xl"><div className="relative aspect-[16/9] min-h-72 overflow-hidden"><Image alt="Камера, контактные листы и карточки композиции" className="object-cover" fill priority sizes="(min-width: 1024px) 60vw, 100vw" src="/images/studio-course-cover.png" /><div className="absolute inset-0 bg-gradient-to-t from-background via-background/10 to-transparent" /><div aria-hidden="true" className="contact-grid absolute inset-0" /><div className="absolute inset-x-0 bottom-0 p-6 sm:p-8"><span className="eyebrow">{messages.home.eyebrow}</span><h1 className="mt-4 max-w-3xl text-3xl font-black leading-tight tracking-[-0.035em] sm:text-5xl">{messages.home.title}</h1></div></div><div className="p-6 sm:p-8"><p className="max-w-2xl text-base leading-7 text-muted-foreground sm:text-lg">{messages.home.description}</p><div className="mt-7 flex flex-col gap-3 sm:flex-row"><Button className="sm:min-w-52" render={<Link href="/courses" />}>{user ? messages.home.continue : messages.home.start}<ArrowRight aria-hidden="true" className="size-4" /></Button><Button render={<Link href="/leaderboard" />} variant="secondary">{messages.navigation.leaderboard}</Button></div></div></section><aside className="grid content-start gap-5"><div className="grid grid-cols-2 gap-4"><div className="stat-card"><Sparkles className="size-5 text-primary" /><strong className="mt-5 text-2xl">{summary.data?.total_xp ?? 0}</strong><span>{messages.home.xp}</span></div><div className="stat-card"><Flame className="size-5 text-warning" /><strong className="mt-5 text-2xl">{summary.data?.current_streak ?? 0}</strong><span>{messages.home.streak}</span></div></div><section className="rounded-[1.75rem] border border-border bg-surface p-5 sm:p-6"><h2 className="font-heading text-xl font-bold">{messages.home.pathTitle}</h2><p className="mt-1 text-sm leading-5 text-muted-foreground">{messages.home.pathDescription}</p><ol className="mt-6 space-y-3">{[messages.home.stepOne, messages.home.stepTwo, messages.home.stepThree].map((step, index) => <li className="path-step" key={step}><span className="grid size-9 place-items-center rounded-full border border-current font-black">{index + 1}</span><span className="font-bold">{step}</span></li>)}</ol></section></aside></main></AppShell>;
}
