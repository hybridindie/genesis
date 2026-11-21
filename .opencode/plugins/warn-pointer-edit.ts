import { Plugin } from "@opencode/plugin"
import { execFile } from "node:child_process"
import { fileURLToPath } from "node:url"
import { promisify } from "node:util"

// The rules live once, in the Claude Code hook. This plugin hands it the same
// JSON shape Claude Code would and surfaces its reminder, so the two harnesses
// cannot drift apart. Resolved from this file, so the hook is found whichever
// directory OpenCode was launched from.
const HOOK = fileURLToPath(new URL("../../.claude/hooks/warn-pointer-edit.sh", import.meta.url))
const run = promisify(execFile)

type ToolInput = {
  filePath?: string
  path?: string
}

type HookOutput = {
  hookSpecificOutput?: { additionalContext?: string }
}

let warnedUnavailable = false

async function reminderFor(filePath: string): Promise<string | undefined> {
  const child = run("bash", [HOOK])
  // If bash is missing, the spawn fails while this write is in flight and the
  // stream emits EPIPE; without a listener that is an uncaught exception that
  // takes the harness down. The spawn failure itself rejects `child` below.
  child.child.stdin?.on("error", () => {})
  child.child.stdin?.end(JSON.stringify({ tool_input: { file_path: filePath } }))
  const { stdout } = await child
  if (!stdout.trim()) return undefined
  return (JSON.parse(stdout) as HookOutput).hookSpecificOutput?.additionalContext
}

export default Plugin.define({
  id: "warn-pointer-edit",
  async setup(ctx) {
    await ctx.tool.hook("execute.before", async (event) => {
      if (event.tool !== "edit" && event.tool !== "write") return

      const input = event.input as ToolInput | undefined
      const filePath = input?.filePath ?? input?.path ?? ""
      if (!filePath) return

      try {
        const reminder = await reminderFor(filePath)
        if (reminder) console.warn(`[warn-pointer-edit] ${reminder}`)
      } catch (err) {
        // Never block an edit, but say once that the guardrail is off (no bash
        // or jq, a missing hook) instead of failing silently on every edit.
        if (!warnedUnavailable) {
          warnedUnavailable = true
          console.warn(`[warn-pointer-edit] guardrail unavailable: ${(err as Error).message}`)
        }
      }
    })
  },
})
