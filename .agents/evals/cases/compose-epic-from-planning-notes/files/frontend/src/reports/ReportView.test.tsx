import { render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { ReportView } from "./ReportView";

afterEach(() => vi.unstubAllGlobals());

test("shows a CSV link once the report loads", async () => {
  vi.stubGlobal("fetch", vi.fn(async () =>
    new Response(JSON.stringify({ id: 1, title: "Weekly", rows: [] }), { status: 200 })));
  render(<ReportView id={1} />);
  expect(await screen.findByText("Download CSV")).toBeTruthy();
});

test("shows an error when the report fails to load", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => new Response("", { status: 500 })));
  render(<ReportView id={1} />);
  expect((await screen.findByRole("alert")).textContent).toContain("500");
});
