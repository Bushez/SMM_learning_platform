const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
  }
}

let accessToken: string | null = null;
let refreshInFlight: Promise<void> | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

type RefreshResponse = { access_token: string };

async function refreshAccessToken(): Promise<void> {
  if (refreshInFlight === null) {
    refreshInFlight = fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: { Accept: "application/json" },
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("Refresh failed");
        }
        const payload = (await response.json()) as RefreshResponse;
        setAccessToken(payload.access_token);
      })
      .finally(() => {
        refreshInFlight = null;
      });
  }
  return refreshInFlight;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  retryAfterRefresh = true,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(accessToken === null ? {} : { Authorization: `Bearer ${accessToken}` }),
      ...options.headers,
    },
  });

  if (
    response.status === 401 &&
    retryAfterRefresh &&
    !path.startsWith("/api/v1/auth/")
  ) {
    try {
      await refreshAccessToken();
      return apiFetch<T>(path, options, false);
    } catch {
      setAccessToken(null);
    }
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      error?: { code?: string; message?: string };
    } | null;
    throw new ApiError(
      response.status,
      body?.error?.code ?? "request_failed",
      body?.error?.message ?? `API request failed with status ${response.status}`,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function apiFetchBlob(path: string, retryAfterRefresh = true): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    // The authenticated API response redirects to a signed, cross-origin MinIO URL.
    // The signed URL is self-contained and must not carry browser cookies.
    credentials: "omit",
    headers: {
      Accept: "image/*",
      ...(accessToken === null ? {} : { Authorization: `Bearer ${accessToken}` }),
    },
  });
  if (response.status === 401 && retryAfterRefresh) {
    try {
      await refreshAccessToken();
      return apiFetchBlob(path, false);
    } catch {
      setAccessToken(null);
    }
  }
  if (!response.ok) {
    throw new ApiError(response.status, "media_download_failed", "Unable to download media");
  }
  return response.blob();
}
