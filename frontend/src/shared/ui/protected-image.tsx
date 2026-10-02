"use client";

/* eslint-disable @next/next/no-img-element */
import { useEffect, useState } from "react";

import { apiFetchBlob } from "@/shared/api/http-client";

export function ProtectedImage({
  alt,
  className = "mt-5 aspect-[4/3] w-full rounded-2xl object-cover",
  mediaId,
}: {
  alt: string;
  className?: string;
  mediaId: string;
}) {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    void apiFetchBlob(`/api/v1/media/${mediaId}/download`)
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      })
      .catch(() => setUrl(null));
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [mediaId]);

  if (!url) return <div className="mt-5 aspect-[4/3] animate-pulse rounded-2xl bg-surface-muted" aria-label={alt} role="img" />;
  return <img alt={alt} className={className} src={url} />;
}
