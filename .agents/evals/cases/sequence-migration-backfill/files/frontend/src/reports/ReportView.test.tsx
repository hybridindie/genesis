import { render, screen } from "@testing-library/react";
import { ReportView } from "./ReportView";

test("shows a CSV link", async () => {
  render(<ReportView id={1} />);
  expect(await screen.findByText("Download CSV")).toBeTruthy();
});
