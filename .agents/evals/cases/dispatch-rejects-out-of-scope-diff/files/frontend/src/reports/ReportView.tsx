import { useEffect, useState } from "react";
import { csvUrl, getReport, type Report } from "../api";

export function ReportView({ id }: { id: number }) {
  const [report, setReport] = useState<Report | null>(null);
  useEffect(() => { getReport(id).then(setReport); }, [id]);
  if (!report) return <p>Loading…</p>;
  return (
    <section>
      <h1>{report.title}</h1>
      <a href={csvUrl(id)}>Download CSV</a>
      <table>{/* rows */}</table>
    </section>
  );
}
