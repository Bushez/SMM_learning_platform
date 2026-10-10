"use client";

import { Download, ImagePlus, RotateCcw, SlidersHorizontal, Sparkles } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { apiFetch } from "@/shared/api/http-client";
import { ErrorState, LoadingState } from "@/shared/ui/query-state";
import { AppShell } from "@/widgets/navigation/app-shell";

type Adjustments = {
  exposure: number; temperature: number; tint: number; contrast: number;
  highlights: number; shadows: number; saturation: number; aperture: number;
  shutter_speed: number; iso: number;
};
type Preset = { id: string; title: string; author_name: string; description: string; adjustments: Adjustments };

const defaults: Adjustments = { exposure: 0, temperature: 0, tint: 0, contrast: 0, highlights: 0, shadows: 0, saturation: 0, aperture: 8, shutter_speed: 1 / 125, iso: 100 };

export function PhotoLab() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [source, setSource] = useState("/images/photo-lab-mountain-source.png");
  const [settings, setSettings] = useState(defaults);
  const presets = useQuery({ queryKey: ["photo-lab-presets"], queryFn: () => apiFetch<Preset[]>("/api/v1/photo-lab/presets") });
  const effectiveExposure = exposureStops(settings);

  useEffect(() => {
    const image = new Image();
    image.src = source;
    image.onload = () => renderPreview(canvasRef.current, image, settings);
  }, [source, settings]);

  const upload = (file: File) => {
    const next = URL.createObjectURL(file);
    setSource((current) => { if (current.startsWith("blob:")) URL.revokeObjectURL(current); return next; });
  };
  const download = () => {
    const link = document.createElement("a");
    link.download = "photo-lab-result.jpg";
    link.href = canvasRef.current?.toDataURL("image/jpeg", 0.94) ?? "";
    link.click();
  };

  return <AppShell><main className="mx-auto max-w-[1500px] px-4 py-8 lg:px-8"><header className="flex flex-wrap items-end justify-between gap-4"><div><p className="eyebrow">Интерактивная практика</p><h1 className="mt-3 text-4xl font-black">Фотолаборатория</h1><p className="mt-3 max-w-2xl text-muted-foreground">Меняйте параметры камеры и обработки, сравнивайте результат и изучайте рецепты фотографов.</p></div><div className="flex gap-2"><label className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-border px-5 py-3 text-sm font-bold hover:border-primary"><ImagePlus className="size-4" />Свой кадр<input accept="image/jpeg,image/png,image/webp" className="sr-only" onChange={(event) => { const file = event.target.files?.[0]; if (file) upload(file); }} type="file" /></label><Button onClick={download}><Download className="size-4" />Скачать</Button></div></header>
    <div className="mt-6 flex flex-wrap gap-2"><button className={`rounded-full border px-4 py-2 text-sm font-bold ${source === "/images/photo-lab-mountain-source.png" ? "border-primary bg-primary/10 text-primary" : "border-border"}`} onClick={() => setSource("/images/photo-lab-mountain-source.png")}>Горное озеро</button><button className={`rounded-full border px-4 py-2 text-sm font-bold ${source === "/images/studio-course-cover.png" ? "border-primary bg-primary/10 text-primary" : "border-border"}`} onClick={() => setSource("/images/studio-course-cover.png")}>Предметная сцена</button></div>
    <div className="mt-4 grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]"><section className="overflow-hidden rounded-[2rem] border border-border bg-black"><div className="relative grid min-h-[420px] place-items-center"><canvas className="max-h-[72vh] w-full object-contain" ref={canvasRef} /></div><div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/10 bg-black px-5 py-4 text-sm text-white/70"><span>Предпросмотр обработки · исходник остаётся неизменным</span><span>ΔEV {effectiveExposure > 0 ? "+" : ""}{effectiveExposure.toFixed(1)} · f/{settings.aperture} · {formatShutter(settings.shutter_speed)} · ISO {settings.iso}</span></div></section>
      <aside className="rounded-[2rem] border border-border bg-surface p-5"><div className="flex items-center justify-between"><h2 className="flex items-center gap-2 text-xl font-black"><SlidersHorizontal className="size-5 text-primary" />Настройки</h2><button aria-label="Сбросить настройки" className="icon-action" onClick={() => setSettings(defaults)}><RotateCcw className="size-4" /></button></div><div className="mt-5 space-y-4"><Range label="Экспозиция" min={-3} max={3} step={0.1} suffix=" EV" value={settings.exposure} onChange={(value) => setSettings({ ...settings, exposure: value })} /><Range label="Температура" min={-50} max={50} value={settings.temperature} onChange={(value) => setSettings({ ...settings, temperature: value })} /><Range label="Оттенок" min={-50} max={50} value={settings.tint} onChange={(value) => setSettings({ ...settings, tint: value })} /><Range label="Контраст" min={-50} max={50} value={settings.contrast} onChange={(value) => setSettings({ ...settings, contrast: value })} /><Range label="Света" min={-50} max={50} value={settings.highlights} onChange={(value) => setSettings({ ...settings, highlights: value })} /><Range label="Тени" min={-50} max={50} value={settings.shadows} onChange={(value) => setSettings({ ...settings, shadows: value })} /><Range label="Насыщенность" min={-50} max={50} value={settings.saturation} onChange={(value) => setSettings({ ...settings, saturation: value })} /><Range label="Диафрагма" min={1.4} max={16} step={0.1} prefix="f/" value={settings.aperture} onChange={(value) => setSettings({ ...settings, aperture: value })} /><Select label="Выдержка" value={String(settings.shutter_speed)} onChange={(value) => setSettings({ ...settings, shutter_speed: Number(value) })} options={[["1/1000", 1/1000], ["1/250", 1/250], ["1/125", 1/125], ["1/30", 1/30], ["1/8", 1/8], ["1 сек", 1]]} /><Select label="ISO" value={String(settings.iso)} onChange={(value) => setSettings({ ...settings, iso: Number(value) })} options={[["100",100],["200",200],["400",400],["800",800],["1600",1600],["3200",3200]]} /></div></aside></div>
    <section className="mt-8"><div className="flex items-center gap-3"><Sparkles className="size-5 text-primary" /><div><h2 className="text-2xl font-black">Пресеты мастеров</h2><p className="text-sm text-muted-foreground">Примените рецепт, затем изучите, какие ползунки изменились.</p></div></div>{presets.isLoading ? <LoadingState /> : presets.isError ? <ErrorState retry={() => void presets.refetch()} /> : <div className="mt-5 grid gap-4 md:grid-cols-3">{presets.data?.map((preset) => <button className="rounded-3xl border border-border bg-surface p-5 text-left transition hover:-translate-y-1 hover:border-primary" key={preset.id} onClick={() => setSettings(preset.adjustments)}><span className="eyebrow">{preset.author_name}</span><h3 className="mt-3 text-lg font-black">{preset.title}</h3><p className="mt-2 text-sm leading-6 text-muted-foreground">{preset.description}</p></button>)}</div>}</section></main></AppShell>;
}

function Range({ label, value, onChange, min, max, step = 1, prefix = "", suffix = "" }: { label: string; value: number; onChange: (value: number) => void; min: number; max: number; step?: number; prefix?: string; suffix?: string }) {
  return <label className="block"><span className="mb-2 flex justify-between text-sm font-bold"><span>{label}</span><output className="text-primary">{prefix}{Number(value.toFixed(1))}{suffix}</output></span><input className="w-full accent-primary" max={max} min={min} onChange={(event) => onChange(Number(event.target.value))} step={step} type="range" value={value} /></label>;
}
function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: Array<[string, number]> }) {
  return <label className="grid gap-2 text-sm font-bold">{label}<select className="field-control" onChange={(event) => onChange(event.target.value)} value={value}>{options.map(([text, option]) => <option key={option} value={option}>{text}</option>)}</select></label>;
}
function formatShutter(value: number) { return value >= 1 ? `${value} сек` : `1/${Math.round(1 / value)}`; }

function exposureStops(settings: Adjustments) {
  const isoStops = Math.log2(settings.iso / 100);
  const apertureStops = 2 * Math.log2(8 / settings.aperture);
  const shutterStops = Math.log2(settings.shutter_speed / (1 / 125));
  return settings.exposure + isoStops + apertureStops + shutterStops;
}

function renderPreview(canvas: HTMLCanvasElement | null, image: HTMLImageElement, settings: Adjustments) {
  if (!canvas) return;
  const maxWidth = 1100; const scale = Math.min(1, maxWidth / image.naturalWidth);
  canvas.width = Math.round(image.naturalWidth * scale); canvas.height = Math.round(image.naturalHeight * scale);
  const context = canvas.getContext("2d", { willReadFrequently: true }); if (!context) return;
  const brightness = Math.pow(2, Math.max(-5, Math.min(5, exposureStops(settings)))) * 100;
  const blur = Math.max(0, (5.6 - settings.aperture) * 0.35) + Math.max(0, settings.shutter_speed - 1 / 30) * 4;
  context.filter = `brightness(${brightness}%) contrast(${100 + settings.contrast}%) saturate(${100 + settings.saturation}%) sepia(${Math.abs(settings.temperature) * .25}%) hue-rotate(${settings.temperature + settings.tint * .5}deg) blur(${blur}px)`;
  context.drawImage(image, 0, 0, canvas.width, canvas.height); context.filter = "none";
  const pixels = context.getImageData(0, 0, canvas.width, canvas.height); const data = pixels.data; const noise = Math.max(0, Math.log2(settings.iso / 100)) * 4.5;
  for (let index = 0; index < data.length; index += 4) { const luminance = (data[index] + data[index + 1] + data[index + 2]) / 3; const tone = luminance > 150 ? settings.highlights : settings.shadows; const shadowNoise = noise * (1 + (255 - luminance) / 420); const grain = hashedNoise(index) * shadowNoise; const chroma = shadowNoise * .45; const delta = tone * .45 + grain; data[index] = clamp(data[index] + delta + hashedNoise(index + 17) * chroma + settings.temperature * .28 + settings.tint * .12); data[index + 1] = clamp(data[index + 1] + delta + hashedNoise(index + 31) * chroma - settings.tint * .2); data[index + 2] = clamp(data[index + 2] + delta + hashedNoise(index + 47) * chroma - settings.temperature * .28 + settings.tint * .12); }
  context.putImageData(pixels, 0, 0);
}
function clamp(value: number) { return Math.max(0, Math.min(255, value)); }
function hashedNoise(seed: number) { return ((((seed * 1103515245 + 12345) >>> 16) & 255) / 127.5) - 1; }
