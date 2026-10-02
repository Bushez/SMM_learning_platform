"use client";

import { Aperture, Flame, Sparkles } from "lucide-react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";

import messages from "../../../messages/ru.json";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-provider";
import type { GamificationSummaryResponse } from "@/shared/api/generated/models";
import { apiFetch } from "@/shared/api/http-client";
import { siteConfig } from "@/shared/config/site";

function AccountActions() {
  const { isRestoring, logout, user } = useAuth();
  const summary = useQuery({
    queryKey: ["gamification-summary"],
    queryFn: () => apiFetch<GamificationSummaryResponse>("/api/v1/users/me/gamification"),
    enabled: Boolean(user),
  });

  if (isRestoring) {
    return <span className="text-sm text-muted-foreground">…</span>;
  }
  if (!user) {
    return <Button render={<Link href="/login" />} variant="ghost">{messages.navigation.login}</Button>;
  }
  return (
    <div className="flex items-center gap-2">
      <div className="metric-pill hidden sm:flex" aria-label={`${summary.data?.total_xp ?? 0} XP`}>
        <Sparkles aria-hidden="true" className="size-4 text-primary" />
        <span>{summary.data?.total_xp ?? 0} XP</span>
      </div>
      <div className="metric-pill" aria-label={`${summary.data?.current_streak ?? 0} ${messages.home.streak}`}>
        <Flame aria-hidden="true" className="size-4 text-warning" />
        <span>{summary.data?.current_streak ?? 0}</span>
      </div>
      <Link aria-label={messages.navigation.profile} className="hidden text-sm font-bold text-foreground hover:text-primary md:block" href="/profile">
        {user.display_name}
      </Link>
      <Button onClick={() => void logout()} variant="ghost">{messages.navigation.logout}</Button>
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-20 border-b border-border/80 bg-background/90 backdrop-blur">
        <div className="mx-auto flex min-h-18 max-w-7xl items-center justify-between gap-4 px-5 lg:px-8">
          <Link className="flex shrink-0 items-center gap-3 font-bold tracking-tight" href="/">
            <span className="grid size-9 place-items-center rounded-xl bg-primary text-primary-foreground"><Aperture aria-hidden="true" className="size-5" /></span>
            <span className="text-lg">{siteConfig.name}</span>
          </Link>
          <nav aria-label="Основная навигация" className="hidden items-center gap-6 md:flex">
            <Link className="nav-link" href="/courses">{messages.navigation.courses}</Link>
            <Link className="nav-link" href="/learn">{messages.navigation.learning}</Link>
            <Link className="nav-link" href="/leaderboard">{messages.navigation.leaderboard}</Link>
            {user?.role === "TEACHER" && <Link className="nav-link" href="/teacher">{messages.navigation.teacher}</Link>}
          </nav>
          <AccountActions />
        </div>
      </header>
      {children}
    </div>
  );
}
