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
  const { lessonId } = useParams<{ lessonId: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const tasks = useQuery({ queryKey: ["lesson-tasks", lessonId], queryFn: () => apiFetch<LearnerTaskResponse[]>(`/api/v1/learning/lessons/${lessonId}/tasks`) });
  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState<string[]>([]);
  const [textAnswer, setTextAnswer] = useState("");
  const [feedback, setFeedback] = useState<AttemptFeedbackResponse | null>(null);
  const submit = useMutation({
    mutationFn: ({ task, body }: { task: LearnerTaskResponse; body: object }) => apiFetch<AttemptFeedbackResponse>(`/api/v1/learning/tasks/${task.id}/attempts`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }),
    onSuccess: (data) => {
      setFeedback(data);
      void queryClient.invalidateQueries({ queryKey: ["gamification-summary"] });
      void queryClient.invalidateQueries({ queryKey: ["course-progress"] });
    },
  });
  if (tasks.isLoading) return <AppShell><LoadingState /></AppShell>;
  if (tasks.isError) return <AppShell><main className="px-5 py-16"><ErrorState retry={() => void tasks.refetch()} /></main></AppShell>;
  const taskCount = tasks.data?.length ?? 0;
  const task = tasks.data?.[index];
  if (!task) return <AppShell><main className="mx-auto max-w-xl px-5 py-20 text-center"><h1 className="text-3xl font-black">{messages.learning.lessonCompleted}</h1><p className="mt-3 text-muted-foreground">{messages.learning.lessonFinished}</p><Button className="mt-8" onClick={() => router.back()}>{messages.learning.backToCourse}</Button></main></AppShell>;
  const isText = task.task_type === "TEXT_INPUT";
  const canSubmit = isText ? textAnswer.trim().length > 0 : selected.length > 0;
  const choose = (optionId: string) => {
    if (feedback) return;
    if (task.task_type === "MULTIPLE_CHOICE") setSelected((value) => value.includes(optionId) ? value.filter((id) => id !== optionId) : [...value, optionId]);
    else setSelected([optionId]);
  };
  const check = () => {
    const body = isText ? { task_type: "TEXT_INPUT", answer_text: textAnswer } : { task_type: task.task_type, selected_option_ids: selected };
    submit.mutate({ task, body });
  };
  const next = () => { if (feedback?.correct) { setIndex((value) => value + 1); setSelected([]); setTextAnswer(""); setFeedback(null); } else setFeedback(null); };
  return <AppShell><main className="mx-auto max-w-3xl px-5 py-8 lg:py-12"><div className="mb-6 flex items-center gap-4"><Link className="text-sm font-bold text-secondary hover:underline" href="/learn">← {messages.common.back}</Link><div className="h-2 flex-1 overflow-hidden rounded-full bg-surface-muted"><div className="h-full rounded-full bg-primary transition-all" style={{ width: `${((index + 1) / taskCount) * 100}%` }} /></div><span className="text-sm font-bold text-muted-foreground">{index + 1}/{taskCount}</span></div><article className="overflow-hidden rounded-[2rem] border border-border bg-surface shadow-2xl"><div className="p-6 sm:p-9"><p className="eyebrow">{messages.learning.task} {index + 1}</p><h1 className="mt-5 text-2xl font-black leading-tight sm:text-3xl">{task.prompt}</h1>{task.prompt_media_id && <ProtectedImage alt={task.prompt} mediaId={task.prompt_media_id} />}<div className="mt-8 grid gap-3">{isText ? <label className="grid gap-2 text-sm font-bold"><span className="sr-only">{messages.learning.answerPlaceholder}</span><input className="field-control" disabled={Boolean(feedback)} onChange={(event) => setTextAnswer(event.target.value)} placeholder={messages.learning.answerPlaceholder} value={textAnswer} /></label> : task.options.map((option, optionIndex) => { const selectedOption = selected.includes(option.id); const correct = feedback?.correct_option_ids.includes(option.id); const wrong = feedback && selectedOption && !correct; return <button aria-pressed={selectedOption} className={`min-h-16 rounded-2xl border p-4 text-left font-bold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${correct ? "border-success bg-success/10" : wrong ? "border-danger bg-danger/10" : selectedOption ? "border-primary bg-primary/10" : "border-border bg-background hover:border-primary/60"}`} disabled={Boolean(feedback)} key={option.id} onClick={() => choose(option.id)} type="button"><span className="flex items-center gap-4"><span className="grid size-8 shrink-0 place-items-center rounded-full border border-current text-sm">{optionIndex + 1}</span><span>{option.text ?? "Вариант с изображением"}</span></span>{option.media_id && <ProtectedImage alt={option.text ?? "Вариант ответа"} className="mt-3 aspect-video w-full rounded-xl object-cover" mediaId={option.media_id} />}</button>; })}</div>{feedback && <section className={`mt-7 rounded-2xl border p-5 ${feedback.correct ? "border-success/50 bg-success/10" : "border-danger/50 bg-danger/10"}`} aria-live="polite"><div className="flex items-center gap-3 font-black">{feedback.correct ? <CheckCircle2 className="size-6 text-success" /> : <CircleAlert className="size-6 text-danger" />}{feedback.correct ? messages.learning.correct : messages.learning.incorrect}</div><p className="mt-3 leading-6 text-muted-foreground">{feedback.explanation}</p>{feedback.result_media_id && <ProtectedImage alt="Правильный результат" mediaId={feedback.result_media_id} />}{!feedback.correct && <p className="mt-3 text-sm font-bold">{messages.learning.correctAnswer}</p>}{feedback.course_progress_percent !== null && <div className="mt-4 rounded-xl bg-background/60 px-4 py-3 text-sm font-bold">{messages.learning.courseProgressNow}: {feedback.course_progress_percent}%</div>}{feedback.xp_awarded > 0 && <div className="mt-4 flex gap-3"><span className="metric-pill"><Sparkles className="size-4 text-primary" />+{feedback.xp_awarded} XP</span>{feedback.current_streak !== null && <span className="metric-pill"><Flame className="size-4 text-warning" />{feedback.current_streak}</span>}</div>}</section>}{submit.isError && <p className="mt-4 text-sm font-bold text-danger">{messages.common.error}</p>}<div className="mt-8"><Button className="w-full" disabled={!canSubmit || submit.isPending} onClick={feedback ? next : check}>{feedback ? messages.learning.continue : messages.learning.check}</Button>{!canSubmit && !feedback && <p className="mt-3 text-center text-sm text-muted-foreground">{messages.learning.chooseAnswer}</p>}</div></div></article></main></AppShell>;
}
