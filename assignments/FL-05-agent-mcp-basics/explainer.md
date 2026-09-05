# What an Agent Is, What MCP Is, and What FL-04 Would Need to Become an Agent

*Own-words explainer for FL-05, based on "Building Effective Agents" and the MCP
introduction.*

## Workflow vs agent, applied to my FL-04 build

Anthropic's essay draws the line I keep forgetting: the difference is not "is code involved"
but **who decides the order of steps**. A **workflow** is a predefined path — the code
decides that we gather, then synthesize, then draft, then format, in that fixed order every
run. An **agent** is when the model itself decides: the LLM looks at each step's result and
chooses what to do next, possibly looping or changing tools mid-task.

My FL-04 pipeline is unambiguously a **workflow**. `weekly_brief.py` runs its four functions
in a hard-coded sequence; the only place a model appears is the summary sentence in
step 2 — and only if an API key is present, where the model produces text but makes no
decision about flow. The pipeline never re-reads its own output, never changes topic on its
own, and publishes whatever matched the filter. That is the classic workflow shape: fast,
predictable, cheap, and completely frozen once written.

## What an agent is

An agent is a model wrapped in a decision loop over **tools**. The model does not just
answer a prompt; it receives a goal, sees a list of available actions (query an API, read a
file, run a script), picks one, inspects the result, and picks the next. The loop is what
makes it more than autocomplete with extra steps: the model can recover from a failing call,
change strategy, and spend many turns on one goal. The price of that autonomy is
predictability — the loop can wander, waste tokens, or do something the human did not
anticipate — which is why every serious agent design includes gating: approval steps, read-only
tools first, and checkpoints where a human says yes or no.

## What MCP is

MCP (Model Context Protocol) is the plumbing that makes "model + tools" practical. An MCP
**server** exposes three primitives to any capable client: **tools** (actions the model can
invoke, like "fetch this RSS feed"), **resources** (data the model can read, like a
file or a row), and **prompts** (reusable instructions, like my brief template). A client —
Claude Desktop, an IDE, or even a small script as I used for the three evidence runs
below — discovers that list and calls the tools. The point is standardization: one server
written once works with every MCP client, and one client can talk to many servers, instead
of every integration being a bespoke adapter.

## What FL-04 would need to become an agent

Three concrete changes, in increasing cost of doing business:

1. **A model-directed loop.** Today the fixed sequence is the workflow. To be an agent, an
   LLM would read the run log, decide whether yesterday's brief was thin (`items_kept: 0`,
   empty topics topic), choose new topic terms itself, and re-run the gather step before
   drafting. No new "steps" needed — only a controller that decides the order. Upfront
   this is ~40 lines that call the same functions.

2. **The pipeline's steps become MCP tools.** Instead of `weekly_brief.py` running top to
   bottom, I would publish `gather_feed`, `summarize_item`, `render_brief`, and `lint_brief`
   as tools — the same four functions, exposed so the controlling model can call the cheap,
   deterministic parts freely and spend model tokens only on real decisions. The run log and
   recent briefs become resources; the brief template becomes a prompt.

3. **Human gating stays.** The free-form Fourier transform an agent adds is exactly the part
   my FL-04 walkthrough flagged as "required human review". Agentic FL-04 must keep the
   checklist as a hard gate: the model proposes a brief, the lint passes, then a human
   approves before it ships to the thread. That keeps the speed of an LLM loop while the
   liability (hallucinated summaries, junk links) stays clamped behind an explicit review.

**The one agent upgrade I would ship first:** replace the fixed topic filter with a
model-driven topic step. The agent reads `run-log.jsonl`, spots a weak run, proposes fresh
topic terms, and triggers a re-gather — while every other step stays exactly as it is today.
That is the smallest change that turns FL-04 from "workflow that summarizes" into "agent
that researches."

## Files in this folder

- `explainer.md` — this document (workflow/agent + MCP primitives + FL-04 upgrade path).
- `mcp-evidence.md` — one live MCP session against the `flyrank` MCP server: three tool
  calls that chat alone could not perform, with the raw transcript.
- `README.md` — folder index and how the evidence was produced.