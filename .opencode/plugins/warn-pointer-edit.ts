import { Plugin } from "@opencode/plugin"

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

      const lower = filePath.toLowerCase()

      let message: string | null = null
      if (lower.includes("/.opencode/") || lower.includes("/.claude/")) {
        message = `Editing harness pointer file: ${filePath}. Edit canonical content in .agents/ instead.`
      } else if (lower.includes("/.agents/doctrine/")) {
        message = `Editing load-bearing doctrine file: ${filePath}. Multiple skills and rubrics reference it by path — edits here propagate everywhere. Confirm the change is intended for all callers; if a rule needs to diverge per skill, it does not belong in shared doctrine.`
      } else if (lower.includes("/templates/_shared/doctrine/")) {
        message = `Editing load-bearing genesis doctrine file: ${filePath}. Multiple articles and agents reference it by path, and it renders into target projects at .claude/rules/doctrine/. Edits here propagate everywhere. Confirm the change is intended for all callers; if a rule needs to diverge per article, it does not belong in shared doctrine.`
      }

      if (message !== null) console.warn(`[warn-pointer-edit] ${message}`)
    })
  },
})
