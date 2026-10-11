// FastAPI serialises datetimes as ISO 8601. Timestamps written by the backend
// are timezone-aware; treat any naive value as UTC.
function parseDate(value: string): Date {
  const hasZone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(value);
  return new Date(hasZone ? value : `${value}Z`);
}

const shortDate = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" });
const longDate = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" });
const timeOnly = new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" });

export function formatRelative(value: string): string {
  const date = parseDate(value);
  if (Number.isNaN(date.getTime())) return "";
  const now = new Date();
  const minutes = Math.round((now.getTime() - date.getTime()) / 60_000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes} min ago`;
  if (date.toDateString() === now.toDateString()) return timeOnly.format(date);
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (date.toDateString() === yesterday.toDateString()) return "Yesterday";
  return date.getFullYear() === now.getFullYear() ? shortDate.format(date) : longDate.format(date);
}

export function formatDate(value: string): string {
  const date = parseDate(value);
  return Number.isNaN(date.getTime()) ? "" : longDate.format(date);
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
