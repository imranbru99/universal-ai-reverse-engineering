# AI ORCHESTRATION

## Provider abstraction

`packages/ai` / `workers` use `LLMClient.complete_structured(schema, prompt, evidence_refs)`.

- If `AI_API_KEY` unset → deterministic heuristic agents (still structured).
- Model output must validate; on failure, retry ≤2 then mark stage error with partial results.

## Agent I/O contract

Every agent returns:

```json
{
  "status": "ok|partial|error",
  "outputs": {},
  "claims": [],
  "errors": [],
  "next_actions": [],
  "evidence_ids": []
}
```

## Safety

- Credentials redacted before prompt assembly
- No tool that executes arbitrary shell from model text
- High-risk proposals → `approvals` queue
