"use client";

import { Flame, Sparkles, Trophy } from "lucide-react";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import messages from "../../../messages/ru.json";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-provider";
import type { GamificationSummaryResponse, LeaderboardResponse } from "@/shared/api/generated/models";
import { apiFetch } from "@/shared/api/http-client";
import { ErrorState, LoadingState } from "@/shared/ui/query-state";
import { AppShell } from "@/widgets/navigation/app-shell";

export function LeaderboardPage() {
  const [period, setPeriod] = useState<"WEEKLY" | "ALL_TIME">("WEEKLY");
  const { user } = useAuth();
  const leaderboard = useQuery({ queryKey: ["leaderboard", period], queryFn: () => apiFetch<LeaderboardResponse>(`/api/v1/leaderboards?period=${period}&scope=GLOBAL`), enabled: Boolean(user) });
  return <AppShell><main className="mx-auto max-w-3xl px-5 py-10"><p className="eyebrow">{messages.leaderboard.eyebrow}</p><h1 className="mt-5 text-4xl font-black tracking-tight">{messages.leaderboard.title}</h1><div className="mt-8 flex gap-2" role="tablist">{(["WEEKLY", "ALL_TIME"] as const).map((item) => <Button aria-selected={period === item} key={item} onClick={() => setPeriod(item)} role="tab" variant={period === item ? "default" : "secondary"}>{item === "WEEKLY" ? messages.leaderboard.weekly : messages.leaderboard.allTime}</Button>)}</div>{!user ? <p className="mt-10 text-muted-foreground">Войдите, чтобы увидеть рейтинг.</p> : leaderboard.isLoading ? <LoadingState /> : leaderboard.isError ? <div className="mt-10"><ErrorState retry={() => void leaderboard.refetch()} /></div> : <section className="mt-8 overflow-hidden rounded-[2rem] border border-border bg-surface">{leaderboard.data?.entries.length === 0 ? <p className="p-8 text-center text-muted-foreground">{messages.common.empty}</p> : leaderboard.data?.entries.map((entry) => <div className={`flex items-center gap-4 border-b border-border p-5 last:border-0 ${entry.user_id === user.id ? "bg-primary/10" : ""}`} key={entry.user_id}><span className="grid size-9 place-items-center rounded-full bg-surface-muted font-black">{entry.rank}</span><span className="grid size-10 place-items-center rounded-xl bg-secondary/20 font-black text-secondary">{entry.display_name.slice(0, 1).toUpperCase()}</span><span className="min-w-0 flex-1 truncate font-bold">{entry.display_name}{entry.user_id === user.id && <span className="ml-2 text-sm text-primary">{messages.leaderboard.you}</span>}</span><span className="flex items-center gap-1 font-black"><Sparkles className="size-4 text-primary" />{entry.xp}</span></div>)}</section>}</main></AppShell>;
}

export function ProfilePage() {
  const { user, isRestoring } = useAuth();
  const summary = useQuery({ queryKey: ["gamification-summary"], queryFn: () => apiFetch<GamificationSummaryResponse>("/api/v1/users/me/gamification"), enabled: Boolean(user) });
  if (isRestoring || (user && summary.isLoading)) return <AppShell><LoadingState /></AppShell>;
  if (!user) return <AppShell><main className="mx-auto max-w-xl px-5 py-20 text-center"><h1 className="text-3xl font-black">Войдите в аккаунт</h1></main></AppShell>;
  if (summary.isError) return <AppShell><main className="px-5 py-16"><ErrorState retry={() => void summary.refetch()} /></main></AppShell>;
  const items = [{ label: messages.profile.totalXp, value: summary.data?.total_xp ?? 0, icon: Sparkles, tone: "text-primary" }, { label: messages.profile.currentStreak, value: summary.data?.current_streak ?? 0, icon: Flame, tone: "text-warning" }, { label: messages.profile.longestStreak, value: summary.data?.longest_streak ?? 0, icon: Trophy, tone: "text-secondary" }];
  return <AppShell><main className="mx-auto max-w-4xl px-5 py-10"><section className="rounded-[2rem] border border-border bg-surface p-7 sm:p-10"><div className="flex items-center gap-5"><span className="grid size-16 place-items-center rounded-2xl bg-primary text-2xl font-black text-primary-foreground">{user.display_name.slice(0, 1).toUpperCase()}</span><div><h1 className="text-3xl font-black">{user.display_name}</h1><p className="mt-1 text-muted-foreground">{user.email}</p></div></div><p className="mt-8 text-muted-foreground">{messages.profile.description}</p><div className="mt-8 grid gap-4 sm:grid-cols-3">{items.map(({ icon: Icon, label, tone, value }) => <article className="rounded-2xl border border-border bg-surface-muted p-5" key={label}><Icon className={`size-5 ${tone}`} /><strong className="mt-5 block text-3xl">{value}</strong><span className="mt-1 block text-sm font-semibold text-muted-foreground">{label}</span></article>)}</div><div className="mt-7 rounded-2xl border border-border p-5"><p className="text-sm font-bold text-muted-foreground">{messages.profile.timezone}</p><p className="mt-1 font-bold">{user.timezone}</p></div></section></main></AppShell>;
}
