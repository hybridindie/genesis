import { Plugin } from "@opencode/plugin"
import { spawnSync } from "node:child_process"

// The rules live once, in the Claude Code hook. This plugin hands it the same
// JSON shape Claude Code would and surfaces its reminder, so the two harnesses
// cannot drift apart.
const HOOK = ".claude/hooks/warn-pointer-edit.sh"

type ToolInput = {
  filePath?: string
  path?: string
}

export default Plugin.define({
  id: "warn-pointer-edit",
  async setup(ctx) {
    await ctx.tool.hook("execute.before", (event) => {
      if (event.tool !== "edit" && event.tool !== "write") return

      const input = event.input as ToolInput | undefined
      const filePath = input?.filePath ?? input?.path ?? ""
      if (!filePath) return

      const run = spawnSync("bash", [HOOK], {
        input: JSON.stringify({ tool_input: { file_path: filePath } }),
        encoding: "utf8",
      })
      if (run.status !== 0 || !run.stdout.trim()) return
      try {
        const reminder = JSON.parse(run.stdout)?.hookSpecificOutput?.additionalContext
        if (reminder) console.warn(`[warn-pointer-edit] ${reminder}`)
      } catch {
        // a hook that prints something unexpected must never block an edit
      }
    })
  },
})
