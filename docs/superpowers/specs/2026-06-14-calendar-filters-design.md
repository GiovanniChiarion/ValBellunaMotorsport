# Calendar Filters — Design Spec

## Summary

Add professional filtering to the calendar view: default only non-concluded races, with a modal filter to show all/concluded/future races, search by name, and filter by date range. Feature-gated by a config dict so superadmin is beta tester first, then rolls out granularly to admin/membro.

## Feature Flag System

New file `app/features.py`:

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

To release to admin: `"beta": ["superadmin", "admin"]`.
To release to all: `"stable": ["superadmin", "admin", "membro"]`.
Zero refactor required.

## Backend Changes

**`app/blueprints/races.py` — `calendar_view()`** (minimal):

- No new query logic — all filtering is client-side.
- Pass `feature_enabled("calendar_filters", g.current_user.ruolo)` to the template context so the template decides whether to show/hide the filter UI and apply default visibility.

### Template: `app/templates/dashboard.html`

#### Filter trigger button

Visible only when `feature_enabled`. Positioned inline with year navigation (e.g., right of year dropdown). Small icon + text.

#### Modal (Alpine.js)

Full-screen on mobile, centered overlay on desktop.

**Filter controls inside modal:**

| Control | Type | Values |
|---------|------|--------|
| Stato | 3 toggle buttons | «In corso / Future» | «Concluse» | «Tutte» |
| Nome | Text input | Free text, case-insensitive `includes` |
| Data da | Date input | Start of range |
| Data a | Date input | End of range |

**Bottom bar (fixed on mobile):**
- «Applica» — closes modal
- «Reset» — clears all filters to defaults, closes modal

#### Race card filtering

Each race card wrapped in `<div x-show="filterMatches(...)">`:

```html
<div x-show="filterMatches(
  '{{ stato_dinamico }}',
  '{{ race.data_inizio or '' }}',
  '{{ race.data_fine or '' }}',
  '{{ race.descrizione|e }}'
)">
```

`stato_dinamico` is already computed in the template (conclusa / in_corso / futura). No new backend logic.

#### Alpine.js Component

Inline script in template:

```javascript
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
  }
}
```

### Users WITHOUT the feature

- No filter button shown
- No Alpine filter component on the page
- All races shown (current behavior, unchanged)

### Users WITH the feature

- Filter button visible
- Default: only non-concluded races shown (`filterStatus = 'future'`)
- Modal to override, filters are client-side instant

### Mobile UX

- Modal: `fixed inset-0 z-50`, backdrop semi-transparent
- Touch targets: `min-h-[44px]`
- Bottom bar fixed with Applica/Reset
- Scrollable content inside modal

### Tests

File: `tests/test_features.py`

| Test | Assertion |
|------|-----------|
| `test_feature_enabled` | superadmin → true, admin/membro → false (beta config) |
| `test_feature_enabled_none_role` | None → false |
| `test_feature_enabled_unknown_role` | random string → false |

File: `tests/test_races.py` (new tests)

| Test | Assertion |
|------|-----------|
| `test_calendar_view_filter_shown_for_superadmin` | filter button/modal present |
| `test_calendar_view_filter_hidden_for_membro` | no filter elements |
| `test_calendar_view_all_races_rendered` | all races still in HTML (client-side filtering) |

### Rollout Plan

1. Superadmin (now) — beta testing
2. Admin — move to beta list
3. Membro — move to beta or stable list

Each step requires only editing the dict in `app/features.py`.
