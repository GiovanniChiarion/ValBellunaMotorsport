# Calendar Filters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add professional client-side filtering to the calendar view — default non-concluded races, modal filter by status/name/date — gated by feature flags so superadmin betas first.

**Architecture:** Feature flag config dict (`app/features.py`) controls visibility. Backend passes flag to template. Alpine.js handles all filtering client-side: modal overlay with controls, race cards shown/hidden reactively. No new backend queries, no page reload on filter change.

**Tech Stack:** Alpine.js 3.x (existing), Jinja2, Flask

---

### Task 1: Feature flag system — create `app/features.py`

**Files:**
- Create: `app/features.py`
- Test: `tests/test_features.py`

- [ ] **Step 1: Write the failing tests**

```python
from app.features import feature_enabled

def test_feature_enabled_for_superadmin():
    assert feature_enabled("calendar_filters", "superadmin") is True

def test_feature_enabled_for_admin():
    assert feature_enabled("calendar_filters", "admin") is False

def test_feature_enabled_for_membro():
    assert feature_enabled("calendar_filters", "membro") is False

def test_feature_enabled_none_role():
    assert feature_enabled("calendar_filters", None) is False

def test_feature_enabled_unknown_feature():
    assert feature_enabled("nonexistent", "superadmin") is False

def test_feature_enabled_unknown_role():
    assert feature_enabled("calendar_filters", "hacker") is False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/python -m pytest tests/test_features.py -v
```
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Write minimal implementation**

```python
FEATURE_FLAGS: dict[str, dict[str, list[str]]] = {
    "calendar_filters": {
        "beta": ["superadmin"],
        "stable": [],
    },
}


def feature_enabled(feature: str, ruolo: str | None) -> bool:
    if not ruolo:
        return False
    flags = FEATURE_FLAGS.get(feature, {})
    return ruolo in flags.get("beta", []) or ruolo in flags.get("stable", [])
```

- [ ] **Step 4: Run test to verify it passes**

```bash
.venv/bin/python -m pytest tests/test_features.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

---

### Task 2: Backend — pass feature flag to template

**Files:**
- Modify: `app/blueprints/races.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_races.py`:

```python
def test_calendar_view_filter_enabled_for_superadmin(client, superadmin_token):
    resp = client.get("/races", headers={"Authorization": f"Bearer {superadmin_token}"})
    assert resp.status_code == 200
    assert b"filterMatches" in resp.data


def test_calendar_view_filter_disabled_for_admin(client, auth_headers):
    resp = client.get("/races", headers=auth_headers)
    assert resp.status_code == 200
    assert b"filterMatches" not in resp.data
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/python -m pytest tests/test_races.py::test_calendar_view_filter_enabled_for_superadmin tests/test_races.py::test_calendar_view_filter_disabled_for_admin -v
```

- [ ] **Step 3: Modify `calendar_view()`**

In `app/blueprints/races.py`:
- Add `from app.features import feature_enabled` at top
- Add `filters_enabled=feature_enabled("calendar_filters", g.current_user.ruolo)` to the `render_template` call

- [ ] **Step 4: Commit**

---

### Task 3: Template — Alpine filterState, button, modal, x-show

**Files:**
- Modify: `app/templates/dashboard.html`

- [ ] **Step 1: Add `filterState()` script** (after line 4)

```html
{% if filters_enabled %}
<script>
function filterState() {
    return {
        open: false,
        filterStatus: 'future',
        filterNome: '',
        filterDa: '',
        filterA: '',
        filterMatches(stato, inizio, fine, nome) {
            if (this.filterStatus === 'future' && stato === 'conclusa') return false;
            if (this.filterStatus === 'concluded' && stato !== 'conclusa') return false;
            if (this.filterNome && !nome.toLowerCase().includes(this.filterNome.toLowerCase())) return false;
            if (this.filterDa && inizio && inizio < this.filterDa) return false;
            if (this.filterA && inizio && inizio > this.filterA) return false;
            return true;
        },
        resetFilters() {
            this.filterStatus = 'future';
            this.filterNome = '';
            this.filterDa = '';
            this.filterA = '';
        },
    };
}
</script>
{% endif %}
```

- [ ] **Step 2: Merge filter state into year Alpine scope** (line 6)

Change from:
```html
<div x-data="{ year: {{ year }} }">
```
to:
```html
<div x-data="{ year: {{ year }}{% if filters_enabled %}, ...filterState(){% endif %} }">
```

- [ ] **Step 3: Add filter button** inline with year nav (after line 25, inside year nav div)

```html
            {% if filters_enabled %}
            <button @click="open = true"
                    class="inline-flex items-center px-3 py-2.5 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-700 rounded-xl text-sm font-medium shadow-sm transition-all duration-150"
                    title="Filtri">
                <svg class="size-4 mr-1.5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M7 12h10M10 18h4"/></svg>
                Filtri
            </button>
            {% endif %}
```

- [ ] **Step 4: Add `x-show` to race cards** (line 120)

Change from:
```html
        <div class="bg-white dark:bg-slate-800 ..." x-data="{ open: false }">
```
to:
```html
        <div {% if filters_enabled %}x-show="filterMatches('{{ stato_dinamico }}', '{{ race.data_inizio or '' }}', '{{ race.data_fine or '' }}', '{{ race.descrizione|e }}')"{% endif %}
             class="bg-white dark:bg-slate-800 ..." x-data="{ open: false }">
```

- [ ] **Step 5: Add filter modal** at the end of the outer div, before `</div>` line 287

```html
    {% if filters_enabled %}
    <!-- Filter modal -->
    <div x-show="open" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-2 sm:p-4" @click.self="open = false" x-cloak>
        <div class="bg-white dark:bg-slate-800 rounded-2xl p-5 sm:p-6 w-full max-w-md shadow-xl border border-gray-200 dark:border-slate-700 max-h-[90vh] overflow-y-auto" @click.stop>
            <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-4">Filtra calendario</h3>

            <div class="space-y-5">
                <div>
                    <label class="block text-sm font-semibold text-gray-700 dark:text-slate-300 mb-2">Stato</label>
                    <div class="flex gap-1.5">
                        <button @click="filterStatus = 'future'"
                                :class="filterStatus === 'future' ? 'bg-emerald-600 text-white shadow-sm' : 'bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-600'"
                                class="flex-1 min-h-[44px] px-3 py-2 rounded-xl text-sm font-semibold transition-all duration-150">
                            In corso / Future
                        </button>
                        <button @click="filterStatus = 'concluded'"
                                :class="filterStatus === 'concluded' ? 'bg-gray-600 text-white shadow-sm' : 'bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-600'"
                                class="flex-1 min-h-[44px] px-3 py-2 rounded-xl text-sm font-semibold transition-all duration-150">
                            Concluse
                        </button>
                        <button @click="filterStatus = 'all'"
                                :class="filterStatus === 'all' ? 'bg-blue-600 text-white shadow-sm' : 'bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-600'"
                                class="flex-1 min-h-[44px] px-3 py-2 rounded-xl text-sm font-semibold transition-all duration-150">
                            Tutte
                        </button>
                    </div>
                </div>

                <div>
                    <label class="block text-sm font-semibold text-gray-700 dark:text-slate-300 mb-1.5">Nome gara</label>
                    <input type="text" x-model="filterNome" placeholder="Cerca per nome..."
                           class="w-full min-h-[44px] px-4 py-2.5 bg-gray-50 dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-xl text-sm dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500">
                </div>

                <div class="flex gap-3">
                    <div class="flex-1">
                        <label class="block text-sm font-semibold text-gray-700 dark:text-slate-300 mb-1.5">Data da</label>
                        <input type="date" x-model="filterDa"
                               class="w-full min-h-[44px] px-4 py-2.5 bg-gray-50 dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-xl text-sm dark:text-white focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500">
                    </div>
                    <div class="flex-1">
                        <label class="block text-sm font-semibold text-gray-700 dark:text-slate-300 mb-1.5">Data a</label>
                        <input type="date" x-model="filterA"
                               class="w-full min-h-[44px] px-4 py-2.5 bg-gray-50 dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-xl text-sm dark:text-white focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500">
                    </div>
                </div>
            </div>

            <div class="flex gap-2 mt-6 pt-4 border-t border-gray-100 dark:border-slate-700">
                <button @click="open = false"
                        class="flex-1 min-h-[44px] px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-xl text-sm font-semibold shadow-sm transition-all duration-150">
                    Applica
                </button>
                <button @click="resetFilters()"
                        class="flex-1 min-h-[44px] px-4 py-2.5 bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-700 dark:text-slate-300 rounded-xl text-sm font-semibold transition-all duration-150">
                    Reset
                </button>
            </div>
        </div>
    </div>
    {% endif %}
```

- [ ] **Step 6: Run tests**

```bash
.venv/bin/python -m pytest tests/test_races.py::test_calendar_view_filter_enabled_for_superadmin tests/test_races.py::test_calendar_view_filter_disabled_for_admin -v
```
Expected: PASS

- [ ] **Step 7: Commit**

---

### Task 4: Verify full suite

- [ ] **Run full verification suite**

```bash
.venv/bin/ruff check app/ tests/
.venv/bin/ruff format --check app/ tests/
.venv/bin/pyright
.venv/bin/python -m pytest tests/ -v
```
