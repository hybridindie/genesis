Planning call — reports app, 2026-11-12
Attendees: Priya (PM), Marco (backend), Jen (frontend), Sam (ops)

Priya: Finance keeps asking for PDF, they paste CSVs into slides today. Also they
want the weekly regional report emailed to them Monday 8am without logging in.
Marco: PDF rendering is slow for big reports — anything over ~2k rows we should do
in the background, not in the request. Small ones can be synchronous.
Jen: UI needs a "Download PDF" next to the CSV link, and a way to set up a
schedule on the report page (weekday + time + recipients).
Sam: email goes through the existing SMTP relay; ops already has creds in the
secret store. Don't send more than 50 emails per schedule.
Priya: first release — PDF for any report, schedules weekly only. Daily/monthly later.
Marco: we'll need a schedules table and a job runner; we already run a cron
container we can reuse.
Open: does finance need the PDF to match their branded template? Priya to check.
Decision: PDFs under 2k rows return directly; bigger ones return a job id and the
UI polls.
