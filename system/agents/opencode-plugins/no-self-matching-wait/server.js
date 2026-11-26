// OpenCode v2 plugin: refuse self-matching `pgrep -f` wait loops.
//
// The check itself is the shared script ~/.agents/hooks/no-self-matching-wait.sh,
// which Claude Code also runs as a PreToolUse hook; this plugin feeds it the
// same JSON before every shell call. When the script refuses, the command is
// replaced with one that prints the reason and exits 1, so the model sees why
// and nothing waits forever. (v2 tool hooks mutate event.input in place, as
// OpenCode's own opencode.tool.input.repair hook does.)
//
// `Plugin.define` from @opencode/plugin is an identity helper, so a plain
// default object with an `id` and `setup(ctx)` is equivalent and dependency-free.
import { spawnSync } from "child_process";
import { existsSync } from "fs";
import { homedir } from "os";
import { join } from "path";

const SCRIPT = join(homedir(), ".agents", "hooks", "no-self-matching-wait.sh");
const SHELL_TOOLS = new Set(["shell", "bash"]);

function refusal(command) {
  const run = spawnSync("bash", [SCRIPT], {
    input: JSON.stringify({ tool_input: { command } }),
    encoding: "utf8",
    timeout: 10000,
  });
  if (run.status !== 0 || !run.stdout.trim()) return null;
  try {
    const out = JSON.parse(run.stdout).hookSpecificOutput;
    return out?.permissionDecision === "deny" ? out.permissionDecisionReason : null;
  } catch {
    return null;
  }
}

export default {
  id: "no-self-matching-wait",
  async setup(ctx) {
    if (!existsSync(SCRIPT)) return;

    await ctx.tool.hook("execute.before", (event) => {
      if (!SHELL_TOOLS.has(event.tool)) return;
      const command = event.input?.command;
      if (typeof command !== "string") return;
      const reason = refusal(command);
      if (!reason) return;
      const quoted = "'" + reason.replaceAll("'", "'\\''") + "'";
      event.input = { ...event.input, command: `printf '%s\\n' ${quoted} >&2; exit 1` };
    });
  },
};
