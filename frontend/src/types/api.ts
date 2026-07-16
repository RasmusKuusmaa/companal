/** Mirrors the backend's Problem Details error shape (see API architecture §04). */
export interface ApiProblemDetails {
  type?: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
}

/** Cursor-paginated collection shape used by feed-like endpoints. */
export interface PaginatedResponse<T> {
  items: T[];
  nextCursor: string | null;
}
