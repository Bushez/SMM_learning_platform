import {
  Aperture,
  ArrowRight,
  Flame,
  Grid2X2,
  LockKeyhole,
  Sparkles,
  Trophy,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";

import messages from "../../messages/ru.json";
import { Button } from "@/components/ui/button";
import { siteConfig } from "@/shared/config/site";

const lessonSteps = [
  { label: messages.home.exposure, state: messages.home.current, active: true },
  { label: messages.home.composition, state: messages.home.next, active: false },
  { label: messages.home.typography, state: messages.home.locked, active: false },
] as const;

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border/80 bg-background/90 backdrop-blur">
        <div className="mx-auto flex h-18 max-w-7xl items-center justify-between px-5 lg:px-8">
          <Link className="flex items-center gap-3 font-bold tracking-tight" href="/">
            <span className="grid size-9 place-items-center rounded-xl bg-primary text-primary-foreground">
              <Aperture aria-hidden="true" className="size-5" />
            </span>
            <span className="text-lg">{siteConfig.name}</span>
          </Link>

          <nav aria-label="Основная навигация" className="hidden items-center gap-7 md:flex">
            <Link className="nav-link" href="/courses">
              {messages.navigation.courses}
            </Link>
            <Link className="nav-link text-foreground" href="/learn">
              {messages.navigation.learning}
            </Link>
            <Link className="nav-link" href="/leaderboard">
              {messages.navigation.leaderboard}
            </Link>
          </nav>

          <div className="flex items-center gap-2">
            <div className="metric-pill hidden sm:flex" aria-label="120 очков опыта">
              <Sparkles aria-hidden="true" className="size-4 text-primary" />
              <span>120 XP</span>
            </div>
            <div className="metric-pill" aria-label="Серия: 3 дня подряд">
              <Flame aria-hidden="true" className="size-4 text-warning" />
              <span>3</span>
            </div>
            <Button render={<Link href="/login" />} variant="ghost">
              {messages.navigation.login}
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-8 px-5 py-8 lg:grid-cols-[minmax(0,1.45fr)_minmax(19rem,0.75fr)] lg:px-8 lg:py-12">
        <section aria-labelledby="continue-title" className="overflow-hidden rounded-[2rem] border border-border bg-surface shadow-2xl">
          <div className="relative aspect-[16/9] min-h-72 overflow-hidden">
            <Image
              src="/images/studio-course-cover.png"
              alt="Камера, контактные листы и карточки композиции"
              fill
              priority
              sizes="(min-width: 1024px) 60vw, 100vw"
              className="object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-background via-background/10 to-transparent" />
            <div className="contact-grid absolute inset-0" aria-hidden="true" />
            <div className="absolute inset-x-0 bottom-0 p-6 sm:p-8">
              <div className="mb-3 flex flex-wrap items-center gap-3 text-sm font-semibold text-muted-foreground">
                <span className="eyebrow">{messages.home.eyebrow}</span>
                <span>{messages.home.course}</span>
              </div>
              <h1 id="continue-title" className="max-w-3xl text-3xl font-black leading-tight tracking-[-0.035em] sm:text-5xl">
                {messages.home.title}
              </h1>
            </div>
          </div>

          <div className="grid gap-6 p-6 sm:p-8">
            <p className="max-w-2xl text-base leading-7 text-muted-foreground sm:text-lg">
              {messages.home.description}
            </p>
            <div className="rounded-2xl border border-border bg-surface-muted p-4 sm:p-5">
              <div className="mb-3 flex items-end justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-muted-foreground">{messages.home.lesson}</p>
                  <p className="mt-1 font-bold">{messages.home.progress}</p>
                </div>
                <span className="text-sm font-bold">{messages.home.taskCount}</span>
              </div>
              <div className="h-2.5 overflow-hidden rounded-full bg-border" aria-label="Прогресс урока: 57%" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={57}>
                <div className="h-full w-[57%] rounded-full bg-primary" />
              </div>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Button className="sm:min-w-52">
                {messages.home.continue}
                <ArrowRight aria-hidden="true" className="size-4" />
              </Button>
              <Button variant="secondary">{messages.home.browse}</Button>
            </div>
          </div>
        </section>

        <aside className="grid content-start gap-5">
          <div className="grid grid-cols-2 gap-4">
            <div className="stat-card">
              <Trophy aria-hidden="true" className="size-5 text-primary" />
              <strong className="mt-5 text-2xl">120</strong>
              <span>{messages.home.xp}</span>
            </div>
            <div className="stat-card">
              <Flame aria-hidden="true" className="size-5 text-warning" />
              <strong className="mt-5 text-2xl">3</strong>
              <span>{messages.home.streak}</span>
            </div>
          </div>

          <section className="rounded-[1.75rem] border border-border bg-surface p-5 sm:p-6" aria-labelledby="path-title">
            <div className="mb-6 flex gap-3">
              <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-secondary text-secondary-foreground">
                <Grid2X2 aria-hidden="true" className="size-5" />
              </span>
              <div>
                <h2 id="path-title" className="font-heading text-xl font-bold">{messages.home.pathTitle}</h2>
                <p className="mt-1 text-sm leading-5 text-muted-foreground">{messages.home.pathDescription}</p>
              </div>
            </div>

            <ol className="space-y-3">
              {lessonSteps.map((step, index) => (
                <li
                  className={step.active ? "path-step path-step-active" : "path-step"}
                  key={step.label}
                >
                  <span className="grid size-9 shrink-0 place-items-center rounded-full border border-current text-sm font-black">
                    {step.state === messages.home.locked ? (
                      <LockKeyhole aria-label={step.state} className="size-4" />
                    ) : (
                      index + 1
                    )}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-bold">{step.label}</span>
                    <span className="text-xs font-semibold uppercase tracking-wider opacity-70">{step.state}</span>
                  </span>
                </li>
              ))}
            </ol>
          </section>
        </aside>
      </main>
    </div>
  );
}
