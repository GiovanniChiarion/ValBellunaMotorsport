# Miglioramenti Visivi Partecipazione

## Panoramica

Tre modifiche all'interfaccia di partecipazione per rendere lo stato delle gare e le scadenze immediatamente chiari.

## 1. Scadenza Conferma Visibile

### Dove
- `app/templates/dashboard.html` — pannello espanso card (riga 210-214)
- `app/templates/race_detail.html` — header gara (riga 56-62)

### Comportamento
- Se `scadenza_conferma > today + 7gg`: badge info normale (testo scuro su sfondo chiaro)
- Se `today < scadenza_conferma <= today + 7gg`: badge giallo/arancione "Scade tra N giorni"
- Se `scadenza_conferma <= today`: badge rosso "Scaduta!" con messaggio "Non puoi più modificare"

### Stili
- Normale: `bg-gray-100 text-gray-700`
- In scadenza: `bg-amber-100 text-amber-800 border-amber-200`, icona orologio
- Scaduta: `bg-red-100 text-red-800 border-red-200`, icona alert

## 2. Stato Dinamico Gare (Conclusa/In Corso/Futura)

### Logica di calcolo (Jinja nel template)
```
if race.data_fine and race.data_fine < today → "Conclusa"
elif race.data_inizio and race.data_inizio <= today and (not race.data_fine or race.data_fine >= today) → "In corso"
elif race.data_inizio and race.data_inizio > today → "Futura"
else → nessun badge aggiuntivo
```

### Dove
- `app/templates/dashboard.html` — nella card principale di ogni gara (intorno a riga 118-137)

### Modifiche visive per card
- Barra verticale colorata (oggi sempre `bg-red-600`) cambia colore:
  - Futura: `bg-green-500`
  - In corso: `bg-orange-500`
  - Conclusa: `bg-gray-400`
- Badge testo "Futura" / "In corso" / "Conclusa" vicino a data e tipo gara
- Card conclusa: `opacity-75` o `bg-gray-50` per ridurre enfasi visiva
- Card in corso: bordo `border-orange-300` opzionale, pallino animato CSS

### template race_detail.html
- Stesso badge stato dinamico nell'header, accanto a `race.stato`

## 3. Messaggio Errore Specifico

### Dove
- `app/templates/base.html` — funzione `setStatus()` (riga 203-211)

### Modifica
Leggere il body della response fallita e mostrare il messaggio specifico invece di "Errore" generico:

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

## File da modificare
1. `app/templates/dashboard.html` — deadline badge + stato dinamico card
2. `app/templates/race_detail.html` — deadline badge + stato dinamico header
3. `app/templates/base.html` — errore specifico in setStatus
