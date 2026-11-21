import { useEffect, useState } from "react";
import { csvUrl, getReport, type Report } from "../api";

export function ReportView({ id }: { id: number }) {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let current = true; // ignore a response for an id we have moved past
    setReport(null);
    setError(null);
    getReport(id)
      .then((r) => { if (current) setReport(r); })
      .catch((e: Error) => { if (current) setError(e.message); });
    return () => { current = false; };
  }, [id]);
  if (error) return <p role="alert">Could not load the report: {error}</p>;
  if (!report) return <p>Loading…</p>;
  return (
    <section>
      <h1>{report.title}</h1>
      <a href={csvUrl(id)}>Download CSV</a>
      <table>{/* rows */}</table>
    </section>
  );
}
