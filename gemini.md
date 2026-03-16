# GEMINI.md - Workspace-Specific Mandates

This file defines the foundational mandates and workflows for Gemini CLI in the KRAI-minimal workspace. These rules take precedence over general defaults.

## Core Philosophy (Superpowers & Orchestration)

1.  **Process Over Intuition:** Follow disciplined workflows (Research -> Strategy -> Execution) to prevent hallucinations or skipping critical steps.
2.  **Evidence Over Claims:** Never mark a task complete without proving it works via tests or logs.
3.  **Simplicity First:** Make every change as simple as possible. Minimal impact, maximum clarity. No "just-in-case" code.
4.  **No Laziness:** Find root causes. No temporary fixes. Senior developer standards are mandatory.
5.  **Context Efficiency:** Treat context as a precious resource. Minimize unnecessary turns and optimize tool usage.

---

## 1. Workflow Orchestration

### Plan Mode Default
- **Enter Plan Mode (`enter_plan_mode`)** for ANY non-trivial task (3+ steps or architectural decisions).
- If execution deviates or hits an obstacle: **STOP and re-plan immediately**.
- Use plan mode for **verification steps**, not just implementation details.
- Write detailed specs upfront to reduce ambiguity. Coding begins ONLY after user approval.

### Task Management (tasks/todo.md)
1.  **Plan First:** Write the plan to `tasks/todo.md` with checkable items.
2.  **Verify Plan:** Check in with the user before starting.
3.  **Track Progress:** Mark items as `[x]` as you go.
4.  **Explain Changes:** Provide a high-level summary at each step.
5.  **Document Results:** Add a "Review" section to `tasks/todo.md` after completion.

### Self-Improvement Loop (tasks/lessons.md)
- After ANY correction from the user: update `tasks/lessons.md` with the pattern.
- Write rules for yourself to prevent the same mistake.
- Review `tasks/lessons.md` at the start of every session.

---

## 2. Engineering Standards

### Test-Driven Development (TDD)
- **Red-Green-Refactor is non-negotiable.**
- 1. Create/Identify a failing test (RED).
- 2. Write minimal code to pass (GREEN).
- 3. Refactor and verify (REFACTOR).
- **Mandate:** Delete any code written before a test exists if it wasn't a trivial fix.

### Systematic Debugging & Bug Fixing
- **Autonomous Bug Fixing:** When given a bug report, fix it. Point at logs/errors/failing tests, then resolve.
- **Root Cause Analysis (RCA):** Provide an RCA before applying a fix.
- **Defense-in-Depth:** Every fix MUST include a new test case that prevents regression.

### Subagent Strategy (Strategic Orchestration)
- **Use subagents liberally** to keep the main context window lean.
- **High-Impact Candidates:** Batch refactoring, high-volume output commands, or speculative research.
- **One task per subagent** for focused execution.
- Review subagent output against the master plan.

---

## 3. Context & Tool Efficiency

### Turn Optimization
- **Parallelism:** Execute multiple independent tool calls (e.g., `grep_search`, `read_file`) in a single turn.
- **Surgical Reads:** Use `start_line` and `end_line` for large files.
- **Surgical Edits:** Use `replace` with enough context to ensure uniqueness. Never use omission placeholders (`...`).
- **Quiet Flags:** Always use silent/quiet flags (e.g., `npm install --silent`, `git --no-pager`) to reduce output noise.

### Context Management
- Avoid repetitive narration of tool use. Focus on **intent** and **technical rationale**.
- Keep the session history clean by offloading large/noisy outputs to subagents (e.g., `generalist`).

---

## 4. Tech Stack & Architecture (KRAI)

### 16-Stage Pipeline
- Orchestrated by `KRMasterPipeline` (`backend/pipeline/master_pipeline.py`).
- **Critical:** All processors must be registered unconditionally in `master_pipeline.py`.
- Use `BaseProcessor.safe_process()` — NEVER implement custom retry loops.

### Database (PostgreSQL + pgvector)
- **Always consult `DATABASE_SCHEMA.md` or `DB_QUICK_REFERENCE.md`** before writing queries.
- **Correct Column Names:**
    - `text_chunk` (NOT `chunk_text`) in `krai_intelligence.chunks`.
    - `metadata->>'enrichment_error'` and `metadata->>'tags'` in `krai_content.videos`.

### Laravel / Filament Dashboard
- Follow `laravel-admin/AGENTS.md` rules. Use `search-docs` (Boost) for version-specific Laravel documentation.
- Run `vendor/bin/pint --dirty` after modifying PHP files.

---

## 5. Verification & Elegance

### Verification Before Done
- **Proving Success:** Diffs, logs, and passing tests are required.
- **The "Staff Engineer" Test:** Ask yourself: "Would a staff engineer approve this?"
- Check for N+1 problems, type safety, and error handling.

### Demand Elegance
- For non-trivial changes: Pause and ask "is there a more elegant way?"
- If a fix feels hacky: Implement the elegant solution based on full context.
- Challenge your own work before presenting it.
