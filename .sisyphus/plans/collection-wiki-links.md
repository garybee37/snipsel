# Collection Wiki-Links (`[[Collection]]`)

## TL;DR

> **Quick Summary**: Implement wiki-link syntax `[[Collection Title]]` in snipsels to reference collections. Users type `[[` in the editor to trigger an autocomplete popup, select a collection, and a clickable link is rendered.
>
> **Deliverables**:
> - New `snipsel_collection_refs` join table + model
> - `extract_collection_refs()` parser in `utils_text.py`
> - Sync logic in `_sync_tags_mentions` for collection refs
> - Lightweight autocomplete API endpoint
> - `[[` triggered autocomplete popup in CollectionOutliner textarea
> - Clickable `[[...]]` links in rendered snipsel markdown
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: Task 1 → Task 3 → Task 5 → Task 6

---

## Context

### Original Request
User wants snipsels to reference existing collections, enabling nested/linked collection structures. The implementation should be user-friendly — no link copying or memorizing exact names. 

### Interview Summary
**Key Discussions**:
- Wiki-link syntax `[[Collection Title]]` chosen (Obsidian/Notion pattern)
- Inline autocomplete popup triggered by typing `[[`
- Consistent with existing `@mentions` and `#tags` patterns
- Storage by collection ID (not title) for robustness against renames
- Dead links show "Unknown" rather than auto-updating text on rename

**Research Findings**:
- Collection titles are NOT unique per user — storing by ID is essential
- `utils_text.py` already has `extract_tags()` and `extract_mentions()` using regex
- `_sync_tags_mentions()` in `routes_snipsels.py` handles syncing on save
- `CollectionOutliner.svelte` has `handleEditInput` and `handleKeydown` for the textarea
- `markdown-it` is used for rendering snipsel content
- Collections API at `/api/collections` already supports listing

### Metis Review
**Identified Gaps** (addressed):
- Duplicate collection titles → resolved: store by ID, display title
- Rename/delete behavior → resolved: link persists, shows "Unknown" if collection gone
- `[[` inside markdown formatting → handled: regex only matches outside code blocks
- Textarea caret position for popup → addressed in Task 5 implementation notes
- Autocomplete scoping → only own + shared collections, max 10 results

---

## Work Objectives

### Core Objective
Enable users to reference collections from within snipsel text using `[[Collection Title]]` syntax with inline autocomplete.

### Concrete Deliverables
- `backend/snipsel_api/models.py`: New `SnipselCollectionRef` model
- `backend/snipsel_api/utils_text.py`: New `extract_collection_refs()` function
- `backend/snipsel_api/routes_snipsels.py`: Sync logic for collection refs
- `backend/snipsel_api/routes_collections.py`: New `/api/collections/autocomplete` endpoint
- `frontend/src/routes/CollectionOutliner.svelte`: Autocomplete popup + rendered links
- `frontend/src/lib/api.ts`: New autocomplete API client method
- Database migration for `snipsel_collection_refs` table

### Definition of Done
- [ ] User can type `[[` in a snipsel editor and see a popup with collection suggestions
- [ ] Selecting a collection inserts `[[Collection Title]]` and stores the ref by ID
- [ ] Rendered snipsels show `[[...]]` as clickable links navigating to the collection
- [ ] Dead refs (deleted collections) show as gray "Unknown" links
- [ ] Collection refs are persisted in `snipsel_collection_refs` table

### Must Have
- Autocomplete triggered by `[[` with fuzzy title search
- Refs stored by collection_id (not title string)
- Clickable rendered links
- Autocomplete limited to user's own + shared collections
- Max 10 autocomplete suggestions

### Must NOT Have (Guardrails)
- No backlinks/reverse-reference views (future feature)
- No nested bracket support (`[[[...]]]`)
- No cross-user collection refs (only accessible collections)
- No contenteditable migration (keep textarea)
- No markdown-it plugin (use simple regex replacement for rendering)
- No reuse of the heavy `/api/search` endpoint for autocomplete
- No modification of existing `_extract_prefixed` function (new separate function)
- No editing of existing tests

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: YES (backend has Flask test client patterns)
- **Automated tests**: Tests-after (lightweight verification via API calls)
- **Framework**: Flask test client + `npm run check`

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Backend**: Use Bash (curl) — Send requests, assert status + response fields
- **Frontend**: Use Playwright (playwright skill) — Navigate, interact, assert DOM, screenshot

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — backend foundation):
├── Task 1: Model + Migration [quick]
├── Task 2: Parser function in utils_text.py [quick]
└── Task 3: Autocomplete API endpoint [quick]

Wave 2 (After Wave 1 — backend sync + frontend):
├── Task 4: Sync logic in _sync_tags_mentions [unspecified-high]
├── Task 5: Frontend autocomplete popup [deep]
└── Task 6: Frontend rendered links [unspecified-high]

Wave FINAL (After ALL tasks):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high)
└── Task F4: Scope fidelity check (deep)

Critical Path: Task 1 → Task 4 → Task 5 → Task 6
Parallel Speedup: ~50% faster than sequential
Max Concurrent: 3 (Wave 1)
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|-----------|--------|
| 1 | — | 4 |
| 2 | — | 4, 6 |
| 3 | — | 5 |
| 4 | 1, 2 | F1-F4 |
| 5 | 3 | F1-F4 |
| 6 | 2, 5 | F1-F4 |

### Agent Dispatch Summary

- **Wave 1**: 3 tasks — T1 → `quick`, T2 → `quick`, T3 → `quick`
- **Wave 2**: 3 tasks — T4 → `unspecified-high`, T5 → `deep`, T6 → `unspecified-high`
- **FINAL**: 4 tasks — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [ ] 1. New `SnipselCollectionRef` model + database migration

  **What to do**:
  - Add a new SQLAlchemy model `SnipselCollectionRef` to `backend/snipsel_api/models.py`
  - Fields: `snipsel_id` (FK to snipsels.id, PK), `collection_id` (FK to collections.id, PK), `created_at` (DateTime)
  - Add relationships to Snipsel and Collection
  - Generate Alembic migration: `flask --app snipsel_api.app db migrate -m "add snipsel_collection_refs table"`
  - Apply migration: `flask --app snipsel_api.app db upgrade`

  **Must NOT do**:
  - Do not modify existing models
  - Do not add any indexes beyond the composite PK

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3)
  - **Blocks**: Task 4
  - **Blocked By**: None

  **References**:

  **Pattern References**:
  - `backend/snipsel_api/models.py:200-208` — `SnipselTag` model as pattern (same composite PK join table structure)
  - `backend/snipsel_api/models.py:222-231` — `SnipselMention` model (same pattern)
  - `backend/snipsel_api/models.py:233-243` — `SnipselLink` model (similar FK pair)

  **API/Type References**:
  - `backend/snipsel_api/models.py:53-85` — `Collection` model (FK target)
  - `backend/snipsel_api/models.py:119-164` — `Snipsel` model (FK target)

  **External References**:
  - Alembic migration: run `flask --app snipsel_api.app db migrate` then `flask --app snipsel_api.app db upgrade`

  **Acceptance Criteria**:

  ```
  Scenario: Model exists and migration succeeds
    Tool: Bash
    Steps:
      1. Run: `source backend/.venv/bin/activate && flask --app snipsel_api.app db upgrade`
      2. Run: `sqlite3 backend/instance/snipsel.db ".schema snipsel_collection_refs"`
      3. Assert output contains: `snipsel_id`, `collection_id`, `created_at`
    Expected Result: Table created with correct columns
    Evidence: .sisyphus/evidence/task-1-migration.txt

  Scenario: Model can be imported
    Tool: Bash
    Steps:
      1. Run: `python -c "from snipsel_api.models import SnipselCollectionRef; print('OK')"`
    Expected Result: Prints "OK" without errors
    Evidence: .sisyphus/evidence/task-1-import.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): add SnipselCollectionRef model and migration`
  - Files: `backend/snipsel_api/models.py`, `backend/migrations/versions/*.py`

---

- [ ] 2. Parser function `extract_collection_refs` in `utils_text.py`

  **What to do**:
  - Add a new function `extract_collection_refs(text: str) -> set[str]` to `backend/snipsel_api/utils_text.py`
  - Parse `[[Collection Title]]` patterns from markdown text
  - Return a set of collection title strings (stripped, case-preserved for display)
  - Handle edge cases: empty brackets `[[]]`, brackets inside code blocks, multiple refs in same text
  - Do NOT modify the existing `_extract_prefixed` function — write a new separate function

  **Must NOT do**:
  - Do not modify `_extract_prefixed` or existing functions
  - Do not handle nested brackets `[[[...]]]`

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3)
  - **Blocks**: Tasks 4, 6
  - **Blocked By**: None

  **References**:

  **Pattern References**:
  - `backend/snipsel_api/utils_text.py:13-18` — `extract_tags` and `extract_mentions` (existing patterns to follow)
  - `backend/snipsel_api/utils_text.py:21-36` — `_extract_prefixed` internal helper (read-only reference for style)

  **Acceptance Criteria**:

  ```
  Scenario: Basic extraction
    Tool: Bash
    Steps:
      1. Run: python -c "
         from snipsel_api.utils_text import extract_collection_refs
         assert extract_collection_refs('Check [[My Notes]] and [[Work]]') == {'My Notes', 'Work'}
         assert extract_collection_refs('Empty [[]] should be ignored') == set()
         assert extract_collection_refs('No refs here') == set()
         assert extract_collection_refs('Single [[Test]]') == {'Test'}
         print('ALL PASS')
         "
    Expected Result: Prints "ALL PASS"
    Evidence: .sisyphus/evidence/task-2-parser.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): add extract_collection_refs parser for [[wiki-links]]`
  - Files: `backend/snipsel_api/utils_text.py`

---

- [ ] 3. Autocomplete API endpoint for collections

  **What to do**:
  - Add a new GET endpoint `/api/collections/autocomplete?q=<query>` in `backend/snipsel_api/routes_collections.py`
  - Query parameter `q` (required, min 1 char)
  - Search collections accessible to current user (own + shared) by title ILIKE
  - Return max 10 results, ordered by title
  - Response format: `{ "collections": [{ "id": "...", "title": "...", "icon": "..." }] }`
  - Must be lightweight — no joins beyond collection_shares for access check

  **Must NOT do**:
  - Do not reuse the heavy `/api/search` endpoint
  - Do not return more than 10 results
  - Do not include archived collections

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2)
  - **Blocks**: Task 5
  - **Blocked By**: None

  **References**:

  **Pattern References**:
  - `backend/snipsel_api/routes_collections.py:25-68` — `accessible_collection_ids` pattern in `list_tags` (reuse this access check pattern)
  - `backend/snipsel_api/routes_collections.py:319-328` — Collection search in `search()` endpoint (similar ILIKE query)

  **API/Type References**:
  - `backend/snipsel_api/routes_collections.py:584-599` — `_collection_json` helper (reference but don't use — return minimal fields only)

  **Acceptance Criteria**:

  ```
  Scenario: Autocomplete returns matching collections
    Tool: Bash (curl)
    Steps:
      1. curl -b cookies.txt "http://localhost:5000/api/collections/autocomplete?q=test"
      2. Assert HTTP 200
      3. Assert response has "collections" array
      4. Assert each item has "id", "title", "icon" fields
    Expected Result: JSON with matching collections, max 10
    Evidence: .sisyphus/evidence/task-3-autocomplete.txt

  Scenario: Empty query returns error or empty
    Tool: Bash (curl)
    Steps:
      1. curl -b cookies.txt "http://localhost:5000/api/collections/autocomplete?q="
      2. Assert HTTP 200 with empty collections array OR HTTP 400
    Expected Result: No crash, graceful handling
    Evidence: .sisyphus/evidence/task-3-empty-query.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): add collection autocomplete endpoint for wiki-links`
  - Files: `backend/snipsel_api/routes_collections.py`

---

- [ ] 4. Sync collection refs on snipsel save

  **What to do**:
  - Import `SnipselCollectionRef` and `extract_collection_refs` in `routes_snipsels.py`
  - In `_sync_tags_mentions()`, add logic to:
    1. Extract collection ref titles from snipsel text using `extract_collection_refs()`
    2. Look up collections by title (case-insensitive, user's own + shared)
    3. Delete existing `SnipselCollectionRef` rows for this snipsel
    4. Insert new `SnipselCollectionRef` rows for each matched collection
  - Handle: title not found (skip silently), duplicate titles (take first match)

  **Must NOT do**:
  - Do not send notifications for collection refs
  - Do not modify the snipsel content text itself

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 6)
  - **Blocks**: F1-F4
  - **Blocked By**: Tasks 1, 2

  **References**:

  **Pattern References**:
  - `backend/snipsel_api/routes_snipsels.py:486-547` — `_sync_tags_mentions` function (add collection ref sync at the end, following same delete-then-insert pattern)
  - `backend/snipsel_api/routes_snipsels.py:511-513` — SnipselTag delete + re-insert pattern (copy this pattern)

  **API/Type References**:
  - `backend/snipsel_api/models.py` — New `SnipselCollectionRef` model from Task 1
  - `backend/snipsel_api/utils_text.py` — New `extract_collection_refs` from Task 2

  **Acceptance Criteria**:

  ```
  Scenario: Saving a snipsel with [[ref]] creates collection ref record
    Tool: Bash
    Steps:
      1. Create a collection "Test Wiki Target"
      2. Create a snipsel with content "See [[Test Wiki Target]]"
      3. Query: sqlite3 instance/snipsel.db "SELECT * FROM snipsel_collection_refs"
      4. Assert row exists linking snipsel to collection
    Expected Result: Join table row created
    Evidence: .sisyphus/evidence/task-4-sync.txt

  Scenario: Removing [[ref]] from text deletes the ref record
    Tool: Bash
    Steps:
      1. Update the snipsel content to "No refs anymore"
      2. Query: sqlite3 instance/snipsel.db "SELECT * FROM snipsel_collection_refs WHERE snipsel_id=..."
      3. Assert no rows
    Expected Result: Join table cleaned up
    Evidence: .sisyphus/evidence/task-4-cleanup.txt
  ```

  **Commit**: YES
  - Message: `feat(backend): sync collection refs on snipsel save`
  - Files: `backend/snipsel_api/routes_snipsels.py`

---

- [ ] 5. Frontend autocomplete popup for `[[` trigger

  **What to do**:
  - Add `collections.autocomplete` method to `frontend/src/lib/api.ts`:
    `autocomplete: (q: string) => requestJson<{ collections: Array<{ id: string; title: string; icon: string }> }>(\`/api/collections/autocomplete?q=\${encodeURIComponent(q)}\`)`
  - In `CollectionOutliner.svelte`:
    - Detect when user types `[[` in the textarea
    - Track the query text after `[[` (everything between `[[` and cursor position)
    - Show a floating popup below the textarea with collection suggestions (fetched from autocomplete API)
    - Debounce API calls by 200ms
    - Arrow keys navigate suggestions, Enter/click selects
    - On selection: replace `[[query` with `[[Selected Title]]` and close popup
    - Escape or clicking outside closes the popup
    - Popup styled with the glass/pill design (rounded-xl, border, backdrop-blur-md, shadow)
    - Each suggestion shows icon + title

  **Must NOT do**:
  - Do not use contenteditable (keep textarea)
  - Do not change the textarea to an input field
  - Do not fetch more than 10 results

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 4, 6)
  - **Blocks**: Task 6, F1-F4
  - **Blocked By**: Task 3

  **References**:

  **Pattern References**:
  - `frontend/src/routes/CollectionOutliner.svelte:294-309` — `handleKeydown` (add `[[` detection logic here)
  - `frontend/src/routes/CollectionOutliner.svelte:311-349` — `handleEditInput` (add `[[` query tracking here)
  - `frontend/src/routes/CollectionOutliner.svelte:966-978` — textarea element (popup should be positioned relative to this)
  - `frontend/src/routes/CollectionOutliner.svelte:49-51` — template menu state pattern (follow for autocomplete state)

  **API/Type References**:
  - `frontend/src/lib/api.ts:155-175` — `collections` object in API client (add `autocomplete` method here)

  **External References**:
  - Textarea `selectionStart` API: used to determine cursor position and extract query after `[[`
  - `getBoundingClientRect()`: for positioning the popup near the textarea

  **Acceptance Criteria**:

  ```
  Scenario: Typing [[ shows autocomplete popup
    Tool: Playwright (playwright skill)
    Steps:
      1. Navigate to a collection page
      2. Click on a snipsel to start editing
      3. Type "Check [[te" in the textarea
      4. Assert: a popup/dropdown appears below the textarea
      5. Assert: popup contains collection suggestions with icons
      6. Screenshot
    Expected Result: Floating suggestion list visible with matching collections
    Evidence: .sisyphus/evidence/task-5-autocomplete-popup.png

  Scenario: Selecting a suggestion inserts [[Title]]
    Tool: Playwright (playwright skill)
    Steps:
      1. Continue from above, click on a suggestion
      2. Assert: textarea now contains "Check [[Selected Title]]"
      3. Assert: popup is dismissed
    Expected Result: Full wiki-link syntax inserted, popup closed
    Evidence: .sisyphus/evidence/task-5-selection.png

  Scenario: Escape dismisses popup
    Tool: Playwright (playwright skill)
    Steps:
      1. Type "[[" to trigger popup
      2. Press Escape
      3. Assert: popup is gone
      4. Assert: textarea still has "[[" text
    Expected Result: Popup dismissed without modifying text
    Evidence: .sisyphus/evidence/task-5-escape.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add [[ autocomplete popup for collection wiki-links`
  - Files: `frontend/src/routes/CollectionOutliner.svelte`, `frontend/src/lib/api.ts`

---

- [ ] 6. Render `[[Collection Title]]` as clickable links

  **What to do**:
  - In `CollectionOutliner.svelte`, where snipsel markdown content is rendered (the `{@html md.render(...)}` block):
    - After markdown rendering, post-process the HTML to replace `[[Collection Title]]` text with clickable links
    - Use a regex to find `\[\[([^\]]+)\]\]` patterns in the rendered HTML text nodes
    - For each match, check if the title matches a known collection ref (from the snipsel's collection_refs data)
    - If match found: render as `<a class="..." data-collection-id="...">📎 Collection Title</a>` styled as a pill/chip
    - If no match: render as `<span class="text-slate-400">[[Unknown]]</span>`
  - Add click handler on the rendered content div to intercept clicks on collection ref links
  - On click: navigate to the collection via `currentView.set({ type: 'collection', id: collectionId })`
  - Backend: Include `collection_refs` data in the snipsel list response so frontend knows which titles map to which IDs
    - In `routes_snipsels.py`, in the list endpoint: for each snipsel, include `collection_refs: [{ title: "...", collection_id: "..." }]`

  **Must NOT do**:
  - Do not write a markdown-it plugin
  - Do not modify the markdown-it instance configuration
  - Do not use innerHTML injection without sanitization

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 4, 5)
  - **Blocks**: F1-F4
  - **Blocked By**: Tasks 2, 5

  **References**:

  **Pattern References**:
  - `frontend/src/routes/CollectionOutliner.svelte:1020-1060` — Rendered markdown content area (the `{@html}` block where post-processing should happen)
  - `frontend/src/routes/CollectionOutliner.svelte:140-142` — `openDetail` navigation pattern (follow for collection navigation)
  - `backend/snipsel_api/routes_snipsels.py:596-603` — `_collection_item_json` (add `collection_refs` field here)

  **API/Type References**:
  - `frontend/src/lib/api.ts:106-112` — `CollectionItem` type (add `collection_refs` field)
  - `backend/snipsel_api/models.py` — `SnipselCollectionRef` for querying refs

  **Acceptance Criteria**:

  ```
  Scenario: [[ref]] renders as clickable link
    Tool: Playwright (playwright skill)
    Steps:
      1. Create a snipsel with "See [[My Collection]]" where "My Collection" exists
      2. Navigate to the collection containing this snipsel
      3. Assert: the text shows a styled link for "My Collection" (not raw [[...]])
      4. Click the link
      5. Assert: navigated to "My Collection" view
    Expected Result: Wiki-link rendered as clickable chip, navigation works
    Evidence: .sisyphus/evidence/task-6-rendered-link.png

  Scenario: Dead ref shows as gray Unknown
    Tool: Playwright (playwright skill)
    Steps:
      1. Create a snipsel with "See [[Nonexistent Collection]]"
      2. Assert: renders as gray "Unknown" text, not clickable
    Expected Result: Graceful degradation for missing collections
    Evidence: .sisyphus/evidence/task-6-dead-link.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): render [[wiki-links]] as clickable collection links`
  - Files: `frontend/src/routes/CollectionOutliner.svelte`, `frontend/src/lib/api.ts`, `backend/snipsel_api/routes_snipsels.py`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Rejection → fix → re-run.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists. For each "Must NOT Have": search codebase for forbidden patterns. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `npm run check` + `python -m py_compile` on all changed files. Review for: as any/@ts-ignore, empty catches, console.log in prod, unused imports. Check AI slop: excessive comments, over-abstraction.
  Output: `Build [PASS/FAIL] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` + `playwright` skill
  Start from clean state. Test the full flow: type `[[` → see popup → select → see rendered link → click → navigate. Test edge cases: empty query, escape, dead link. Save screenshots to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: verify implementation matches spec exactly. Check "Must NOT do" compliance. Detect unaccounted changes. Flag anything built beyond spec.
  Output: `Tasks [N/N compliant] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

| Task | Commit Message | Files |
|------|---------------|-------|
| 1 | `feat(backend): add SnipselCollectionRef model and migration` | models.py, migrations/ |
| 2 | `feat(backend): add extract_collection_refs parser for [[wiki-links]]` | utils_text.py |
| 3 | `feat(backend): add collection autocomplete endpoint for wiki-links` | routes_collections.py |
| 4 | `feat(backend): sync collection refs on snipsel save` | routes_snipsels.py |
| 5 | `feat(frontend): add [[ autocomplete popup for collection wiki-links` | CollectionOutliner.svelte, api.ts |
| 6 | `feat(frontend): render [[wiki-links]] as clickable collection links` | CollectionOutliner.svelte, api.ts, routes_snipsels.py |

---

## Success Criteria

### Verification Commands
```bash
# Backend syntax check
source backend/.venv/bin/activate && python -m py_compile snipsel_api/models.py && python -m py_compile snipsel_api/routes_snipsels.py && python -m py_compile snipsel_api/routes_collections.py && python -m py_compile snipsel_api/utils_text.py

# Frontend type check
cd frontend && npm run check

# DB migration
flask --app snipsel_api.app db upgrade
```

### Final Checklist
- [ ] `[[` trigger opens autocomplete popup
- [ ] Popup shows matching collections (icon + title)
- [ ] Selecting inserts `[[Title]]` in text
- [ ] Rendered snipsels show clickable links
- [ ] Dead refs show "Unknown" gracefully
- [ ] Collection refs stored in `snipsel_collection_refs` table
- [ ] All "Must NOT Have" guardrails respected
- [ ] All tests pass
