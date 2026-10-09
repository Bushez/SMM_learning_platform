"use client";

import { CheckCircle2, CircleAlert, Flame, Sparkles } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import messages from "../../../messages/ru.json";
import { Button } from "@/components/ui/button";
import type { AttemptFeedbackResponse, LearnerTaskResponse } from "@/shared/api/generated/models";
import { apiFetch } from "@/shared/api/http-client";
import { ProtectedImage } from "@/shared/ui/protected-image";
import { ErrorState, LoadingState } from "@/shared/ui/query-state";
import { AppShell } from "@/widgets/navigation/app-shell";

export function LessonPlayer() {
  const { lessonId } = useParams<{ lessonId: string }>(); const router = useRouter(); const client = useQueryClient();
  const tasks = useQuery({ queryKey: ["lesson-tasks", lessonId], queryFn: () => apiFetch<LearnerTaskResponse[]>(`/api/v1/learning/lessons/${lessonId}/tasks`) });
  const [index, setIndex] = useState(0); const [selected, setSelected] = useState<string[]>([]); const [textAnswer, setTextAnswer] = useState(""); const [feedback, setFeedback] = useState<AttemptFeedbackResponse | null>(null);
  const submit = useMutation({ mutationFn: ({ task, body }: { task: LearnerTaskResponse; body: object }) => apiFetch<AttemptFeedbackResponse>(`/api/v1/learning/tasks/${task.id}/attempts`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }), onSuccess: (result) => { setFeedback(result); void client.invalidateQueries({ queryKey: ["gamification-summary"] }); void client.invalidateQueries({ queryKey: ["course-progress"] }); } });
  if (tasks.isLoading) return <AppShell><LoadingState /></AppShell>;
  if (tasks.isError) return <AppShell><main className="px-5 py-16"><ErrorState retry={() => void tasks.refetch()} /></main></AppShell>;
  const task = tasks.data?.[index]; const total = tasks.data?.length ?? 0;
  if (!task) return <AppShell><main className="mx-auto max-w-xl px-5 py-20 text-center"><h1 className="text-3xl font-black">{messages.learning.lessonCompleted}</h1><p className="mt-3 text-muted-foreground">{messages.learning.lessonFinished}</p><Button className="mt-8" onClick={() => router.back()}>{messages.learning.backToCourse}</Button></main></AppShell>;
  const isText = task.task_type === "TEXT_INPUT"; const canSubmit = isText ? Boolean(textAnswer.trim()) : selected.length > 0;
  const choose = (optionId: string) => { if (feedback) return; setSelected((items) => task.task_type === "MULTIPLE_CHOICE" ? items.includes(optionId) ? items.filter((id) => id !== optionId) : [...items, optionId] : [optionId]); };
  const check = () => submit.mutate({ task, body: isText ? { task_type: "TEXT_INPUT", answer_text: textAnswer } : { task_type: task.task_type, selected_option_ids: selected } });
  const next = () => { if (feedback?.correct) { setIndex((value) => value + 1); setSelected([]); setTextAnswer(""); } setFeedback(null); };
  return <AppShell><main className="mx-auto max-w-3xl px-5 py-8 lg:py-12"><div className="mb-6 flex items-center gap-4"><Link className="text-sm font-bold text-secondary" href="/learn">← {messages.common.back}</Link><div className="h-2 flex-1 overflow-hidden rounded-full bg-surface-muted"><div className="h-full rounded-full bg-primary" style={{ width: `${((index + 1) / total) * 100}%` }} /></div><span className="text-sm font-bold text-muted-foreground">{index + 1}/{total}</span></div><article className="overflow-hidden rounded-[2rem] border border-border bg-surface"><div className="p-6 sm:p-9"><p className="eyebrow">{messages.learning.task} {index + 1}</p><h1 className="mt-5 text-2xl font-black sm:text-3xl">{task.prompt}</h1>{task.prompt_media_id && <ProtectedImage alt={task.prompt} mediaId={task.prompt_media_id} />}{isText ? <input className="field-control mt-8" disabled={Boolean(feedback)} onChange={(event) => setTextAnswer(event.target.value)} placeholder={messages.learning.answerPlaceholder} value={textAnswer} /> : <div className="mt-8 grid gap-3">{task.options.map((option, optionIndex) => { const chosen = selected.includes(option.id); const correct = feedback?.correct_option_ids.includes(option.id); const wrong = Boolean(feedback && chosen && !correct); return <button aria-pressed={chosen} className={`rounded-2xl border p-4 text-left font-bold transition ${correct ? "border-success bg-success/10" : wrong ? "border-danger bg-danger/10" : chosen ? "border-primary bg-primary/10" : "border-border bg-background hover:border-primary/60"}`} disabled={Boolean(feedback)} key={option.id} onClick={() => choose(option.id)} type="button"><span className="flex items-center gap-4"><span className={`grid size-11 shrink-0 place-items-center rounded-full border-2 text-sm ${chosen ? "border-primary bg-primary text-primary-foreground" : "border-primary/40 text-primary"}`}>{optionIndex + 1}</span><span>{option.text || "Вариант с изображением"}</span></span>{option.media_id && <ProtectedImage alt={option.text || "Вариант"} className="mt-3 aspect-video w-full rounded-xl object-cover" mediaId={option.media_id} />}</button>; })}</div>}{feedback && <FeedbackPanel feedback={feedback} />}{submit.isError && <p className="mt-4 text-sm font-bold text-danger">{messages.common.error}</p>}<div className="mt-8"><Button className="w-full" disabled={!canSubmit || submit.isPending} onClick={feedback ? next : check}>{feedback ? messages.learning.continue : messages.learning.check}</Button></div></div></article></main></AppShell>;
}

function FeedbackPanel({ feedback }: { feedback: AttemptFeedbackResponse }) {
  const entries = [...feedback.option_feedback, ...(feedback.answer_feedback ? [feedback.answer_feedback] : [])];
  return <section className={`mt-7 rounded-2xl border p-5 ${feedback.correct ? "border-success/50 bg-success/10" : "border-danger/50 bg-danger/10"}`} aria-live="polite"><div className="flex items-center gap-3 font-black">{feedback.correct ? <CheckCircle2 className="size-6 text-success" /> : <CircleAlert className="size-6 text-danger" />}{feedback.correct ? "Верно!" : "Пока нет"}</div>{entries.map((item) => <div className="mt-4 rounded-xl bg-background/50 p-4" key={item.option_id}>{item.text && <p className="leading-6">{item.text}</p>}{item.media_id && <ProtectedImage alt="Результат проверки" className="mt-3 aspect-video w-full rounded-xl object-cover" mediaId={item.media_id} />}</div>)}{feedback.xp_awarded > 0 && <div className="mt-4 flex gap-3"><span className="metric-pill"><Sparkles className="size-4 text-primary" />+{feedback.xp_awarded} XP</span>{feedback.current_streak !== null && <span className="metric-pill"><Flame className="size-4 text-warning" />{feedback.current_streak}</span>}</div>}</section>;
}
