# Miglioramenti Visivi Partecipazione — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rendere visivamente chiare le scadenze conferma, lo stato delle gare (conclusa/in corso/futura), e mostrare errori specifici quando la modifica non è permessa.

**Architecture:** Solo modifiche lato template (Jinja2 + Alpine.js) e JS. Nessuna modifica backend: `today` è già passato ai template, la logica di calcolo va in Jinja, l'errore specifico si legge dalla response JSON.

**Tech Stack:** Jinja2 templates, Alpine.js, Tailwind CSS (CDN), vanilla JS

**Files da modificare:**
- `app/templates/base.html` — funzione `setStatus()`
- `app/templates/dashboard.html` — badge scadenza + stato dinamico card
- `app/templates/race_detail.html` — badge scadenza + stato dinamico header

---

### Task 1: Mostrare errore specifico in setStatus

**Files:**
- Modify: `app/templates/base.html:203-211`

- [ ] **Step 1: Modificare setStatus per leggere il body della response**

  In `app/templates/base.html`, riga 209, sostituire:
  ```javascript
  else { showToast('Errore', 'error'); }
  ```
  con:
  ```javascript
  else {
      try {
          const data = await r.json();
          showToast(data.error || data.detail || 'Errore', 'error');
      } catch {
          showToast('Errore', 'error');
      }
  }
  ```

- [ ] **Step 2: Verificare lint**

  Run: `.venv/bin/ruff check app/templates/`
  Skip — i template Jinja non sono analizzati da ruff.

- [ ] **Step 3: Fare un test manuale**

  Avviare il server con `.venv/bin/python run.py`, fare login, provare a cambiare status su una gara con `scadenza_conferma` passata. Il toast deve mostrare "Scadenza conferma superata" invece di "Errore".

---

### Task 2: Badge scadenza conferma colorato in dashboard.html

**Files:**
- Modify: `app/templates/dashboard.html:209-217`

**Logica badge scadenza (Jinja):**
- Se `race.scadenza_conferma` è definita:
  - Se `race.scadenza_conferma <= today`: rosso "Scaduta!"
  - Se `race.scadenza_conferma <= today + 7gg`: giallo "Scade tra N giorni"
  - Altrimenti: grigio "Conferma entro: data"

- [ ] **Step 1: Aggiungere calcolo giorni mancanti e badge colorato**

  In `app/templates/dashboard.html`, riga 209-217, sostituire:
  ```html
                      <div class="flex items-center justify-between">
                          {% if race.scadenza_conferma %}
                          <span class="inline-flex items-center text-xs text-gray-400 dark:text-slate-500">
                              {{ icon_alert(class="size-3 mr-0.5") }}
                              Conferma entro: {{ race.scadenza_conferma.strftime('%d/%m/%Y') }}
                          </span>
                          {% else %}
                          <span></span>
                          {% endif %}
  ```
  con:
  ```html
                      <div class="flex items-center justify-between">
                          {% if race.scadenza_conferma %}
                          {% set giorni_mancanti = (race.scadenza_conferma - today).days %}
                          {% if giorni_mancanti <= 0 %}
                          <span class="inline-flex items-center gap-1 text-xs font-semibold bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-700 px-2.5 py-1 rounded-lg">
                              {{ icon_alert(class="size-3") }}
                              Scaduta!
                              <span class="font-normal text-red-500 dark:text-red-400">Non puoi più modificare</span>
                          </span>
                          {% elif giorni_mancanti <= 7 %}
                          <span class="inline-flex items-center gap-1 text-xs font-semibold bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-700 px-2.5 py-1 rounded-lg">
                              <svg class="size-3" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                              Scade tra {{ giorni_mancanti }} giorno{% if giorni_mancanti != 1 %}g{% endif %}
                          </span>
                          {% else %}
                          <span class="inline-flex items-center gap-1 text-xs text-gray-500 dark:text-slate-400 bg-gray-50 dark:bg-slate-700/50 px-2.5 py-1 rounded-lg">
                              <svg class="size-3" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                              Conferma entro: {{ race.scadenza_conferma.strftime('%d/%m/%Y') }}
                          </span>
                          {% endif %}
                          {% else %}
                          <span></span>
                          {% endif %}
  ```

- [ ] **Step 2: Verificare con ruff** — I template non sono analizzati.

---

### Task 3: Badge scadenza conferma colorato in race_detail.html

**Files:**
- Modify: `app/templates/race_detail.html:56-62`

- [ ] **Step 1: Applicare stessa logica badge nell'header della gara**

  In `app/templates/race_detail.html`, riga 56-62, sostituire:
  ```html
          <div class="mt-4 flex flex-wrap items-center gap-3">
              {% if race.scadenza_conferma %}
              <span class="inline-flex items-center text-sm text-gray-500 dark:text-slate-400">
                  <svg class="size-4 mr-1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                  Conferma entro: {{ race.scadenza_conferma.strftime('%d/%m/%Y') }}
              </span>
              {% endif %}
  ```
  con:
  ```html
          <div class="mt-4 flex flex-wrap items-center gap-3">
              {% if race.scadenza_conferma %}
              {% set giorni_mancanti = (race.scadenza_conferma - today).days %}
              {% if giorni_mancanti <= 0 %}
              <span class="inline-flex items-center gap-1.5 text-sm font-semibold bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-700 px-3 py-1.5 rounded-xl">
                  <svg class="size-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                  Scaduta!
              </span>
              {% elif giorni_mancanti <= 7 %}
              <span class="inline-flex items-center gap-1.5 text-sm font-semibold bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-700 px-3 py-1.5 rounded-xl">
                  <svg class="size-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                  Scade tra {{ giorni_mancanti }} giorno{% if giorni_mancanti != 1 %}g{% endif %}
              </span>
              {% else %}
              <span class="inline-flex items-center gap-1.5 text-sm text-gray-500 dark:text-slate-400">
                  <svg class="size-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                  Conferma entro: {{ race.scadenza_conferma.strftime('%d/%m/%Y') }}
              </span>
              {% endif %}
              {% endif %}
  ```

---

### Task 4: Stato dinamico gare in dashboard.html

**Files:**
- Modify: `app/templates/dashboard.html:96-157`

Calcolare `stato_dinamico` per ogni gara e usarlo per:
1. Colore della barra verticale (oggi sempre rosso `bg-red-600`)
2. Badge "Futura" / "In corso" / "Conclusa" nella card
3. Opacità ridotta per gare concluse
4. Bordo evidenziato per gare in corso

- [ ] **Step 1: Aggiungere calcolo stato dinamico e variabili colore/opacità**

  In `app/templates/dashboard.html`, dopo la riga 100 (dopo `set end_date`), aggiungere:
  ```jinja
  {% if race.data_fine and race.data_fine < today %}
      {% set stato_dinamico = 'conclusa' %}
      {% set bar_color = 'bg-gray-400' %}
      {% set card_opacity = 'opacity-75' %}
  {% elif race.data_inizio and race.data_inizio <= today and (not race.data_fine or race.data_fine >= today) %}
      {% set stato_dinamico = 'in_corso' %}
      {% set bar_color = 'bg-orange-500' %}
      {% set card_opacity = '' %}
  {% elif race.data_inizio and race.data_inizio > today %}
      {% set stato_dinamico = 'futura' %}
      {% set bar_color = 'bg-green-500' %}
      {% set card_opacity = '' %}
  {% else %}
      {% set stato_dinamico = '' %}
      {% set bar_color = 'bg-red-600' %}
      {% set card_opacity = '' %}
  {% endif %}
  ```

- [ ] **Step 2: Applicare colore barra, opacità e badge stato**

  Modificare riga 102 (la card div):
  ```html
          <div class="bg-white dark:bg-slate-800 rounded-2xl border border-gray-200 dark:border-slate-700 shadow-sm card-hover {{ card_opacity }}{% if stato_dinamico == 'in_corso' %} border-orange-200 dark:border-orange-800{% endif %}" x-data="{ open: false }">
  ```

  Modificare riga 116 (la barra verticale):
  ```html
                  <div class="min-w-[3px] self-stretch {{ bar_color }} rounded-full"></div>
  ```

  Modificare riga 119-137 (aggiungere badge stato dopo `h3`):
  ```html
                      <h3 class="text-base font-bold text-gray-900 dark:text-white truncate">{{ race.descrizione }}</h3>
                      <div class="flex flex-wrap items-center gap-1.5 mt-1">
                          {% if stato_dinamico == 'conclusa' %}
                          <span class="inline-flex items-center text-[11px] font-semibold uppercase tracking-wider bg-gray-100 dark:bg-slate-700 text-gray-500 dark:text-slate-400 px-2 py-0.5 rounded-md">
                              Conclusa
                          </span>
                          {% elif stato_dinamico == 'in_corso' %}
                          <span class="inline-flex items-center text-[11px] font-semibold uppercase tracking-wider bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 px-2 py-0.5 rounded-md">
                              <span class="size-1.5 rounded-full bg-orange-500 mr-1 inline-block animate-pulse"></span>
                              In corso
                          </span>
                          {% elif stato_dinamico == 'futura' %}
                          <span class="inline-flex items-center text-[11px] font-semibold uppercase tracking-wider bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 px-2 py-0.5 rounded-md">
                              Futura
                          </span>
                          {% endif %}
                          <span class="inline-flex items-center text-xs text-gray-500 dark:text-slate-400">
                              {{ icon_calendar(class="size-3.5 mr-0.5") }}
                              {{ start_date }}{% if end_date and end_date != start_date %} — {{ end_date }}{% endif %}
                          </span>
  ```

- [ ] **Step 3: Aggiungere `animate-pulse` se non già presente in app.css**

  Verificare in `app/static/css/app.css` se c'è già una classe `animate-pulse`. Tailwind CDN include `animate-pulse` di default, quindi non serve aggiungere nulla.

---

### Task 5: Stato dinamico in race_detail.html

**Files:**
- Modify: `app/templates/race_detail.html:12-44`

Aggiungere badge stato dinamico nell'header accanto allo stato esistente.

- [ ] **Step 1: Aggiungere calcolo stato dinamico e badge**

  In `app/templates/race_detail.html`, dopo `race.stato` badge (riga 36-42), aggiungere badge stato dinamico:
  ```html
              {% if race.data_fine and race.data_fine < today %}
              <span class="inline-flex items-center px-3 py-1.5 rounded-xl text-xs font-bold bg-gray-100 dark:bg-slate-700 text-gray-500 dark:text-slate-400 border border-gray-200 dark:border-slate-600">
                  <svg class="size-3 mr-1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 12.5L11 15l4-4" stroke="currentColor"/><path d="M12 21a9 9 0 100-18 9 9 0 000 18z"/></svg>
                  Conclusa
              </span>
              {% elif race.data_inizio and race.data_inizio <= today and (not race.data_fine or race.data_fine >= today) %}
              <span class="inline-flex items-center px-3 py-1.5 rounded-xl text-xs font-bold bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 border border-orange-200 dark:border-orange-700">
                  <span class="size-1.5 rounded-full bg-orange-500 mr-1.5 inline-block animate-pulse"></span>
                  In corso
              </span>
              {% elif race.data_inizio and race.data_inizio > today %}
              <span class="inline-flex items-center px-3 py-1.5 rounded-xl text-xs font-bold bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 border border-green-200 dark:border-green-700">
                  <svg class="size-3 mr-1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l5 5L20 7" stroke="currentColor"/></svg>
                  Futura
              </span>
              {% endif %}
  ```
