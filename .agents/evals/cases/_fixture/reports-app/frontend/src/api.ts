const BASE = "/api/reports"; // proxied to the backend's /reports (vite.config.ts)

export type Report = { id: number; title: string; rows: Record<string, unknown>[] };

export async function getReport(id: number): Promise<Report> {
  const res = await fetch(`${BASE}/${id}`);
  if (!res.ok) throw new Error(`report ${id}: ${res.status}`);
  return res.json();
}

export function csvUrl(id: number): string {
  return `${BASE}/${id}/export.csv`;
}
