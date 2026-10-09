"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, ImagePlus, Pencil, Plus, Trash2, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import type { MediaAssetResponse, TeacherTaskResponse } from "@/shared/api/generated/models";
import { apiFetch } from "@/shared/api/http-client";
import { ProtectedImage } from "@/shared/ui/protected-image";
import { ErrorState, LoadingState } from "@/shared/ui/query-state";
import { AppShell } from "@/widgets/navigation/app-shell";

type ChoiceOption = {
  id?: string;
  text: string;
  mediaId: string | null;
  correct: boolean;
  feedbackText: string;
  feedbackMediaId: string | null;
};

function useImageUpload() {
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return apiFetch<MediaAssetResponse>("/api/v1/media/images", { method: "POST", body: form });
    },
  });
}

function ImagePicker({ label, mediaId, onChange }: { label: string; mediaId: string | null; onChange: (id: string | null) => void }) {
  const upload = useImageUpload();
  return (
    <div className="mt-4">
      <p className="text-sm font-bold">{label}</p>
      {mediaId ? (
        <div className="group relative mt-2 overflow-hidden rounded-2xl">
          <ProtectedImage alt={label} className="aspect-video w-full rounded-2xl object-cover" mediaId={mediaId} />
          <button aria-label={`Убрать: ${label}`} className="absolute right-3 top-3 grid size-9 place-items-center rounded-full bg-background/90 text-foreground opacity-0 transition group-hover:opacity-100" onClick={() => onChange(null)} type="button">
            <X className="size-4" />
          </button>
        </div>
      ) : (<>
        <label className="mt-2 flex cursor-pointer items-center justify-center gap-2 rounded-2xl border border-dashed border-border bg-surface-muted px-4 py-4 text-sm font-bold text-muted-foreground transition hover:border-primary hover:text-foreground">
          <ImagePlus className="size-4" />
          {upload.isPending ? "Загружаем…" : "Добавить изображение"}
          <input accept="image/jpeg,image/png,image/webp" className="sr-only" disabled={upload.isPending} onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) upload.mutate(file, { onSuccess: (media) => onChange(media.id) });
          }} type="file" />
        </label>
      </>)}
      {upload.isError && <p className="mt-2 text-xs text-danger">Не удалось загрузить изображение.</p>}
    </div>
  );
}

export function LessonEditor() {
  const { courseId, lessonId } = useParams<{ courseId: string; lessonId: string }>();
  const client = useQueryClient();
  const [editing, setEditing] = useState<string | null>(null);
  const tasks = useQuery({
    queryKey: ["teacher-tasks", courseId],
    queryFn: () => apiFetch<TeacherTaskResponse[]>(`/api/v1/teacher/courses/${courseId}/tasks`),
  });
  const command = useMutation({
    mutationFn: ({ path, method, body }: { path: string; method: string; body?: object }) => apiFetch(path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    }),
    onSuccess: () => void client.invalidateQueries({ queryKey: ["teacher-tasks", courseId] }),
  });

  if (tasks.isLoading) return <AppShell><LoadingState /></AppShell>;
  if (!tasks.data || tasks.isError) return <AppShell><ErrorState retry={() => void tasks.refetch()} /></AppShell>;

  const lessonTasks = tasks.data.filter((task) => task.lesson_id === lessonId);
  return (
    <AppShell>
      <main className="mx-auto max-w-4xl px-5 py-8 lg:py-12">
        <Link className="text-sm font-bold text-secondary" href={`/teacher/courses/${courseId}/edit`}>← К структуре курса</Link>
        <header className="mt-5 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="eyebrow">Редактор урока</p>
            <h1 className="mt-3 text-3xl font-black">Задания</h1>
            <p className="mt-2 text-muted-foreground">Редактируйте задание в представлении, близком к экрану ученика.</p>
          </div>
          <Button onClick={() => setEditing("new")}><Plus className="size-4" />Новое задание</Button>
        </header>
        {command.isError && <p className="mt-5 rounded-xl bg-danger/10 p-3 text-sm text-danger">Не удалось выполнить действие. Удаление и перестановка недоступны для уже пройденного задания.</p>}
        <div className="mt-8 space-y-7">
          {lessonTasks.map((task, index) => (
            <article className="overflow-hidden rounded-[2rem] border border-border bg-surface" key={task.id}>
              <div className="flex items-center justify-between border-b border-border px-5 py-4">
                <span className="eyebrow">ЗАДАНИЕ {index + 1}</span>
                <div className="flex gap-2">
                  <button aria-label="Поднять задание" className="icon-action" disabled={index === 0} onClick={() => command.mutate({ path: `/api/v1/teacher/tasks/${task.id}/move`, method: "POST", body: { position: task.position - 1 } })}><ChevronUp className="size-4" /></button>
                  <button aria-label="Опустить задание" className="icon-action" disabled={index === lessonTasks.length - 1} onClick={() => command.mutate({ path: `/api/v1/teacher/tasks/${task.id}/move`, method: "POST", body: { position: task.position + 1 } })}><ChevronDown className="size-4" /></button>
                  <button aria-label={task.task_type === "MULTIPLE_CHOICE" ? "Несколько правильных ответов временно нельзя редактировать" : "Редактировать задание"} className="icon-action" disabled={task.task_type === "MULTIPLE_CHOICE"} onClick={() => setEditing(task.id)} title={task.task_type === "MULTIPLE_CHOICE" ? "Этот тип временно недоступен для редактирования" : undefined}><Pencil className="size-4" /></button>
                  <button aria-label="Удалить задание" className="icon-action" onClick={() => { if (window.confirm("Удалить задание?")) command.mutate({ path: `/api/v1/teacher/tasks/${task.id}`, method: "DELETE" }); }}><Trash2 className="size-4" /></button>
                </div>
              </div>
              {editing === task.id ? <TaskEditor courseId={courseId} lessonId={lessonId} onClose={() => setEditing(null)} task={task} /> : <TaskPreview task={task} />}
            </article>
          ))}
          {editing === "new" && <article className="overflow-hidden rounded-[2rem] border border-primary/50 bg-surface"><TaskEditor courseId={courseId} lessonId={lessonId} onClose={() => setEditing(null)} /></article>}
          {lessonTasks.length === 0 && editing !== "new" && <div className="rounded-3xl border border-dashed border-border p-10 text-center text-muted-foreground">В уроке пока нет заданий.</div>}
        </div>
      </main>
    </AppShell>
  );
}

function TaskPreview({ task }: { task: TeacherTaskResponse }) {
  return (
    <div className="p-6 sm:p-8">
      <h2 className="text-2xl font-black">{task.prompt}</h2>
      {task.prompt_media_id && <ProtectedImage alt={task.prompt} className="mt-6 aspect-video w-full rounded-3xl object-cover" mediaId={task.prompt_media_id} />}
      {task.task_type === "TEXT_INPUT" ? <input className="field-control mt-6" disabled placeholder="Текстовый ответ" /> : (
        <div className="mt-6 grid gap-3">{task.options.map((option, index) => (
          <div className="rounded-2xl border border-border bg-background p-4" key={option.id}>
            <span className="mr-3 inline-grid size-10 place-items-center rounded-full border-2 border-primary/50 bg-primary/10 text-sm font-black text-primary">{index + 1}</span>
            <span className="font-bold">{option.text || "Вариант с изображением"}</span>
            {option.media_id && <ProtectedImage alt={option.text || "Вариант"} className="mt-3 aspect-video w-full rounded-xl object-cover" mediaId={option.media_id} />}
          </div>
        ))}</div>
      )}
    </div>
  );
}

function TaskEditor({ courseId, lessonId, onClose, task }: { courseId: string; lessonId: string; onClose: () => void; task?: TeacherTaskResponse }) {
  const client = useQueryClient();
  const [type, setType] = useState<string>(task?.task_type ?? "SINGLE_CHOICE");
  const [prompt, setPrompt] = useState(task?.prompt ?? "");
  const [promptMediaId, setPromptMediaId] = useState(task?.prompt_media_id ?? null);
  const [answerFeedbackText, setAnswerFeedbackText] = useState(task?.answer_feedback_text ?? "");
  const [answerFeedbackMediaId, setAnswerFeedbackMediaId] = useState(task?.answer_feedback_media_id ?? null);
  const [acceptedAnswers, setAcceptedAnswers] = useState(task?.accepted_answers.join("\n") ?? "");
  const [options, setOptions] = useState<ChoiceOption[]>(task?.options.map((option) => ({
    id: option.id,
    text: option.text ?? "",
    mediaId: option.media_id,
    correct: option.is_correct,
    feedbackText: option.feedback_text ?? "",
    feedbackMediaId: option.feedback_media_id,
  })) ?? [
    { text: "", mediaId: null, correct: true, feedbackText: "", feedbackMediaId: null },
    { text: "", mediaId: null, correct: false, feedbackText: "", feedbackMediaId: null },
  ]);
  const updateOption = (index: number, update: Partial<ChoiceOption>) => setOptions((items) => items.map((item, current) => current === index ? { ...item, ...update } : item));
  const setCorrect = (index: number, checked: boolean) => setOptions((items) => items.map((item, current) => ({ ...item, correct: type === "SINGLE_CHOICE" ? current === index : current === index ? checked : item.correct })));
  const save = useMutation({
    mutationFn: () => {
      const body = {
        task_type: type,
        position: task?.position ?? 1,
        prompt,
        prompt_media_id: promptMediaId,
        answer_feedback_text: type === "TEXT_INPUT" ? answerFeedbackText || null : null,
        answer_feedback_media_id: type === "TEXT_INPUT" ? answerFeedbackMediaId : null,
        options: type === "TEXT_INPUT" ? [] : options.map((option, index) => ({
          text: option.text || null,
          media_id: option.mediaId,
          position: index + 1,
          is_correct: option.correct,
          feedback_text: option.feedbackText || null,
          feedback_media_id: option.feedbackMediaId,
        })),
        accepted_answers: type === "TEXT_INPUT" ? acceptedAnswers.split("\n").map((value) => value.trim()).filter(Boolean) : [],
      };
      return apiFetch(task ? `/api/v1/teacher/tasks/${task.id}` : `/api/v1/teacher/lessons/${lessonId}/tasks`, {
        method: task ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    },
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["teacher-tasks", courseId] });
      onClose();
    },
  });
  const choice = type !== "TEXT_INPUT";

  return (
    <form className="p-6 sm:p-8" onSubmit={(event) => { event.preventDefault(); save.mutate(); }}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-black">{task ? "Настроить задание" : "Новое задание"}</h2>
        <select className="field-control w-auto" onChange={(event) => setType(event.target.value)} value={type}>
          <option value="SINGLE_CHOICE">Один правильный ответ</option>
          <option value="TEXT_INPUT">Текстовый ответ</option>
        </select>
      </div>
      <label className="mt-6 grid gap-2 text-sm font-bold">Вопрос
        <textarea className="field-control min-h-28 py-3" onChange={(event) => setPrompt(event.target.value)} required value={prompt} />
      </label>
      <ImagePicker label="Изображение вопроса" mediaId={promptMediaId} onChange={setPromptMediaId} />
      {choice ? (
        <div className="mt-6">
          <div className="flex items-center justify-between gap-4">
            <div><h3 className="font-black">Варианты ответа</h3><p className="text-sm text-muted-foreground">Отметьте правильные варианты. Для нескольких ответов можно выбрать больше одного.</p></div>
            <Button onClick={() => setOptions((items) => [...items, { text: "", mediaId: null, correct: false, feedbackText: "", feedbackMediaId: null }])} type="button" variant="secondary"><Plus className="size-4" />Вариант</Button>
          </div>
          <div className="mt-4 space-y-4">
            {options.map((option, index) => (
              <div className="rounded-3xl border border-border bg-background p-4" key={option.id ?? index}>
                <div className="flex items-center gap-3">
                  <input aria-label={`Правильный вариант ${index + 1}`} checked={option.correct} className="size-6 accent-primary" onChange={(event) => setCorrect(index, event.target.checked)} type={type === "SINGLE_CHOICE" ? "radio" : "checkbox"} />
                  <input className="field-control flex-1" onChange={(event) => updateOption(index, { text: event.target.value })} placeholder={`Вариант ${index + 1}`} required={!option.mediaId} value={option.text} />
                  {options.length > 2 && <button aria-label="Удалить вариант" className="icon-action" onClick={() => setOptions((items) => items.filter((_, current) => current !== index))} type="button"><Trash2 className="size-4" /></button>}
                </div>
                <ImagePicker label="Изображение варианта" mediaId={option.mediaId} onChange={(mediaId) => updateOption(index, { mediaId })} />
                <div className="mt-4 rounded-2xl border border-primary/20 bg-primary/5 p-4">
                  <p className="text-sm font-black">Обратный ответ для этого варианта</p>
                  <textarea className="field-control mt-3 min-h-20 py-3" onChange={(event) => updateOption(index, { feedbackText: event.target.value })} placeholder="Что увидит ученик после выбора этого варианта" value={option.feedbackText} />
                  <ImagePicker label="Изображение после выбора" mediaId={option.feedbackMediaId} onChange={(feedbackMediaId) => updateOption(index, { feedbackMediaId })} />
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (<>
        <label className="mt-6 grid gap-2 text-sm font-bold">Допустимые ответы — по одному в строке
          <textarea className="field-control min-h-28 py-3" onChange={(event) => setAcceptedAnswers(event.target.value)} required value={acceptedAnswers} />
        </label>
        <div className="mt-4 rounded-2xl border border-primary/20 bg-primary/5 p-4">
          <p className="text-sm font-black">Обратный ответ после текстового ответа</p>
          <textarea className="field-control mt-3 min-h-20 py-3" onChange={(event) => setAnswerFeedbackText(event.target.value)} placeholder="Что увидит ученик после проверки" value={answerFeedbackText} />
          <ImagePicker label="Изображение после проверки" mediaId={answerFeedbackMediaId} onChange={setAnswerFeedbackMediaId} />
        </div>
      </>)}
      <div className="mt-7 flex flex-wrap gap-3"><Button disabled={save.isPending} type="submit">Сохранить задание</Button><Button onClick={onClose} type="button" variant="secondary">Отмена</Button></div>
      {save.isError && <p className="mt-3 text-sm text-danger">Не удалось сохранить задание. Проверьте обязательные поля и правильные ответы.</p>}
    </form>
  );
}
