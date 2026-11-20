export type Report = { id: number; title: string; rows: Record<string, unknown>[] };

export async function getReport(id: number): Promise<Report> {
  const res = await fetch(`/api/reports/${id}`);
  if (!res.ok) throw new Error(`report ${id}: ${res.status}`);
  return res.json();
}

export function csvUrl(id: number): string {
  return `/api/reports/${id}/export.csv`;
}
