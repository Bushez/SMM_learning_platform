"use client";

import { ArrowRight, BookOpen, CheckCircle2, Play, Sparkles } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";

import messages from "../../../messages/ru.json";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-provider";
import type { CourseProgressResponse, CourseResponse } from "@/shared/api/generated/models";
import { apiFetch } from "@/shared/api/http-client";
import { ProtectedImage } from "@/shared/ui/protected-image";
import { ErrorState, LoadingState } from "@/shared/ui/query-state";
import { AppShell } from "@/widgets/navigation/app-shell";

const courseImage = "/images/studio-course-cover.png";

export function CourseCatalog() {
  const query = useQuery({
    queryKey: ["courses"],
    queryFn: () => apiFetch<CourseResponse[]>("/api/v1/courses?limit=30"),
  });
  return <AppShell><main className="mx-auto max-w-7xl px-5 py-10 lg:px-8"><p className="eyebrow">{messages.courses.eyebrow}</p><h1 className="mt-5 max-w-2xl text-4xl font-black tracking-tight sm:text-5xl">{messages.courses.title}</h1><p className="mt-4 max-w-xl text-lg text-muted-foreground">{messages.courses.description}</p>{query.isLoading ? <LoadingState /> : query.isError ? <div className="mt-10"><ErrorState retry={() => void query.refetch()} /></div> : <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-3">{query.data?.map((course) => <CourseCard course={course} key={course.id} />)}</div>}{!query.isLoading && !query.isError && query.data?.length === 0 && <p className="mt-10 text-muted-foreground">{messages.common.empty}</p>}</main></AppShell>;
}

function CourseCard({ course }: { course: CourseResponse }) {
  return <article className="group overflow-hidden rounded-[1.75rem] border border-border bg-surface transition hover:-translate-y-1 hover:border-primary/50"><div className="relative aspect-[16/9] overflow-hidden">{course.cover_media_id ? <ProtectedImage alt={`Обложка курса ${course.title}`} className="mt-0 size-full object-cover transition duration-500 group-hover:scale-105" fallbackSrc={courseImage} mediaId={course.cover_media_id} /> : <Image alt="" className="object-cover transition duration-500 group-hover:scale-105" fill sizes="(min-width: 1280px) 28vw, (min-width: 768px) 45vw, 100vw" src={courseImage} />}<div className="absolute inset-0 bg-gradient-to-t from-background/80 to-transparent" /><span className="absolute bottom-4 left-4 rounded-full bg-background/80 px-3 py-1 text-xs font-bold backdrop-blur">{course.category}</span></div><div className="p-5"><h2 className="text-xl font-black">{course.title}</h2><p className="mt-2 line-clamp-2 min-h-12 text-sm leading-6 text-muted-foreground">{course.description}</p><Button className="mt-5 w-full" render={<Link href={`/courses/${course.slug}`} />} variant="secondary">{messages.courses.open}<ArrowRight aria-hidden="true" className="size-4" /></Button></div></article>;
}

export function CourseDetails() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();
  const { user } = useAuth();
  const course = useQuery({ queryKey: ["course", slug], queryFn: () => apiFetch<CourseResponse>(`/api/v1/courses/${slug}`) });
  const enroll = useMutation({ mutationFn: (courseId: string) => apiFetch<CourseProgressResponse>(`/api/v1/learning/courses/${courseId}/enroll`, { method: "POST" }), onSuccess: () => router.push(`/learn/courses/${slug}`) });
  if (course.isLoading) return <AppShell><LoadingState /></AppShell>;
  if (course.isError || !course.data) return <AppShell><main className="px-5 py-16"><ErrorState retry={() => void course.refetch()} /></main></AppShell>;
  const item = course.data;
  return <AppShell><main className="mx-auto max-w-7xl px-5 py-8 lg:px-8 lg:py-12"><Link className="text-sm font-bold text-secondary hover:underline" href="/courses">← {messages.common.back}</Link><section className="mt-6 overflow-hidden rounded-[2rem] border border-border bg-surface lg:grid lg:grid-cols-2"><div className="relative min-h-72">{item.cover_media_id ? <ProtectedImage alt={`Обложка курса ${item.title}`} className="absolute inset-0 size-full object-cover" fallbackSrc={courseImage} mediaId={item.cover_media_id} /> : <Image alt="" className="object-cover" fill sizes="(min-width: 1024px) 50vw, 100vw" src={courseImage} />}<div className="absolute inset-0 bg-gradient-to-t from-background/90 to-transparent" /></div><div className="flex flex-col justify-center p-7 sm:p-10"><span className="eyebrow w-fit">{item.category}</span><h1 className="mt-5 text-4xl font-black tracking-tight">{item.title}</h1><p className="mt-4 leading-7 text-muted-foreground">{item.description}</p><div className="mt-8 flex flex-wrap gap-3"><span className="metric-pill"><BookOpen className="size-4 text-secondary" />Практический курс</span><span className="metric-pill"><Sparkles className="size-4 text-primary" />Русский</span></div><Button className="mt-8 w-full sm:w-fit" disabled={enroll.isPending} onClick={() => user ? enroll.mutate(item.id) : router.push("/login")}><Play aria-hidden="true" className="size-4" />{user ? messages.courses.start : messages.navigation.login}</Button>{enroll.isError && <p className="mt-3 text-sm text-danger">{messages.common.error}</p>}</div></section></main></AppShell>;
}

export function CourseLearningDashboard() {
  const { slug } = useParams<{ slug: string }>();
  const course = useQuery({ queryKey: ["course", slug], queryFn: () => apiFetch<CourseResponse>(`/api/v1/courses/${slug}`) });
  const progress = useQuery({ queryKey: ["course-progress", course.data?.id], queryFn: () => apiFetch<CourseProgressResponse>(`/api/v1/learning/courses/${course.data?.id}/outline`), enabled: Boolean(course.data?.id) });
  if (course.isLoading || progress.isLoading) return <AppShell><LoadingState /></AppShell>;
  if (course.isError || progress.isError || !course.data || !progress.data) return <AppShell><main className="px-5 py-16"><ErrorState retry={() => { void course.refetch(); void progress.refetch(); }} /></main></AppShell>;
  const data = progress.data;
  return <AppShell><main className="mx-auto max-w-5xl px-5 py-10 lg:px-8"><Link className="text-sm font-bold text-secondary hover:underline" href={`/courses/${slug}`}>← {messages.common.back}</Link><div className="mt-6 rounded-[2rem] border border-border bg-surface p-6 sm:p-8"><p className="eyebrow">{messages.learning.courseProgress}</p><h1 className="mt-4 text-3xl font-black">{course.data.title}</h1><div className="mt-6 h-3 overflow-hidden rounded-full bg-surface-muted" role="progressbar" aria-valuemax={100} aria-valuemin={0} aria-valuenow={data.progress_percent}><div className="h-full rounded-full bg-primary" style={{ width: `${data.progress_percent}%` }} /></div><p className="mt-3 text-sm font-bold text-muted-foreground">{data.completed_tasks} / {data.total_tasks} · {data.progress_percent}%</p></div><div className="mt-8 space-y-6">{data.modules.map((module) => <section key={module.id}><h2 className="mb-3 text-lg font-black">{module.position}. {module.title}</h2><div className="grid gap-3">{module.lessons.map((lesson) => <article className="flex flex-col justify-between gap-4 rounded-2xl border border-border bg-surface p-5 sm:flex-row sm:items-center" key={lesson.id}><div className="flex items-start gap-3"><span className={`grid size-10 place-items-center rounded-full ${lesson.completed ? "bg-success/20 text-success" : lesson.unlocked ? "bg-primary/15 text-primary" : "bg-surface-muted text-muted-foreground"}`}>{lesson.completed ? <CheckCircle2 className="size-5" /> : lesson.position}</span><div><h3 className="font-bold">{lesson.title}</h3><p className="mt-1 text-sm text-muted-foreground">{lesson.completed_tasks}/{lesson.total_tasks} · {lesson.completed ? messages.learning.completed : lesson.unlocked ? messages.learning.lesson : messages.learning.locked}</p></div></div>{lesson.unlocked && <Button render={<Link href={`/learn/lessons/${lesson.id}`} />} variant={lesson.completed ? "secondary" : "default"}>{messages.learning.continueLesson}<ArrowRight className="size-4" /></Button>}</article>)}</div></section>)}</div></main></AppShell>;
}
