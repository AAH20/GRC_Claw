export interface ParsedToolCall {
  tool: string;
  args: Record<string, unknown>;
}

const TOOL_LINE = /TOOL_CALL:\s*(\{[\s\S]*?\})\s*$/im;
const FINAL_LINE = /FINAL_ANSWER:\s*([\s\S]+)$/im;
const JSON_BLOCK = /```(?:json)?\s*(\{[\s\S]*?"tool"[\s\S]*?\})\s*```/i;

export function parseFinalAnswer(text: string): string | null {
  const m = text.match(FINAL_LINE);
  return m ? m[1]!.trim() : null;
}

export function parseToolCall(text: string): ParsedToolCall | null {
  const line = text.match(TOOL_LINE);
  if (line) {
    try {
      const obj = JSON.parse(line[1]!) as { tool?: string; args?: Record<string, unknown> };
      if (obj.tool) return { tool: obj.tool, args: obj.args ?? {} };
    } catch {
      /* fall through */
    }
  }
  const block = text.match(JSON_BLOCK);
  if (block) {
    try {
      const obj = JSON.parse(block[1]!) as { tool?: string; args?: Record<string, unknown> };
      if (obj.tool) return { tool: obj.tool, args: obj.args ?? {} };
    } catch {
      /* ignore */
    }
  }
  return null;
}
