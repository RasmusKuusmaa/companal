import { AxiosError } from "axios";

import type { ApiProblemDetails } from "@/types/api";

/** Normalizes any thrown error into the app's Problem Details shape, so callers never branch on axios internals. */
export function toApiProblem(error: unknown): ApiProblemDetails {
  if (error instanceof AxiosError) {
    const data = error.response?.data as Partial<ApiProblemDetails> | undefined;
    return {
      type: data?.type,
      title: data?.title ?? error.message,
      status: error.response?.status ?? 0,
      detail: data?.detail,
      instance: data?.instance,
    };
  }

  if (error instanceof Error) {
    return { title: error.message, status: 0 };
  }

  return { title: "Unexpected error", status: 0 };
}
