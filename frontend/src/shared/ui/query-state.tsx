import { AlertCircle, LoaderCircle } from "lucide-react";

import messages from "../../../messages/ru.json";
import { Button } from "@/components/ui/button";

export function LoadingState() {
  return <div className="flex min-h-56 items-center justify-center gap-3 text-muted-foreground"><LoaderCircle className="size-5 animate-spin" />{messages.common.loading}</div>;
}

export function ErrorState({ retry }: { retry?: () => void }) {
  return <div className="mx-auto grid max-w-md place-items-center gap-4 rounded-3xl border border-danger/40 bg-danger/10 p-8 text-center"><AlertCircle className="size-7 text-danger" /><p>{messages.common.error}</p>{retry && <Button onClick={retry} variant="secondary">{messages.common.retry}</Button>}</div>;
}
