# ⛵ NYC Harbor Sailing Conditions

A mobile-first PWA that shows real-time sailing conditions for NYC Harbor — designed to check while walking to the dock.

**[Live Demo →](https://yourusername.github.io/nyc-sailing/)** *(update with your URL)*

![Dark nautical theme](https://img.shields.io/badge/theme-dark_nautical-0a1420) ![No API key](https://img.shields.io/badge/API_key-none_required-48bb78) ![Zero build step](https://img.shields.io/badge/build-zero_config-4fd1c5)

---

## What It Shows

### At a Glance
Wind speed, temperature, and tide status in a quick-read banner strip.

### Wind — Robbins Reef (NOAA Station 8530973)
- Current sustained speed, gusts, and direction (cardinal + degrees)
- **B&G-style wind speed chart** — 2-hour history showing sustained (green), gusts (orange), rolling average (dashed), and 12-knot reference line
- **B&G-style wind direction chart** — TWD vs rolling average with shaded deviation area to spot shifts
- Toggle to view full NOAA station page in-app

### Tides — The Battery (NOAA Station 8518750)
- Current status: Flooding / Ebbing / Slack with color coding
- Visual progress bar between previous and next tide
- Countdown timer to next tide
- 6-event lookahead with heights
- Toggle tide chart image from tide-forecast.com

### Weather & Temperature
- Current temp in °C and °F with feels-like
- Weather description with emoji icon
- Thunderstorm risk indicator (CAPE-based: None / Low / Moderate / HIGH)
- Water temperature

### Wind Forecast — HRRR (3km resolution)
- 18-hour forecast from NOAA HRRR via Open-Meteo
- Columns: Time, Wind, Gust, Direction (cardinal), Direction (degrees), Temp, Rain
- Current hour highlighted
- Color-coded wind speeds

### Radar
- Interactive Windy radar embed (lazy-loaded on tap)
- Quick links to Windy app and AccuWeather

---

## Data Sources

| Data | Source | Resolution | Update Freq |
|------|--------|-----------|-------------|
| Wind (current) | [NOAA CO-OPS](https://tidesandcurrents.noaa.gov/stationhome.html?id=8530973) — Robbins Reef Light | 6-minute | 6 min |
| Tides | [NOAA CO-OPS](https://tidesandcurrents.noaa.gov/stationhome.html?id=8518750) — The Battery | High/Low events | Daily |
| Water temp | NOAA CO-OPS — The Battery | Point reading | 6 min |
| Forecast | [Open-Meteo](https://open-meteo.com/en/docs/gfs-api) — HRRR model | 3 km / 15-min | Hourly |
| Radar | [Windy](https://www.windy.com) embed | — | Real-time |

All APIs are free, require no API key, and support CORS for client-side calls.

---

## Deployment

### GitHub Pages (recommended)

1. Fork or clone this repo
2. Go to **Settings → Pages → Source**: select `main` branch
3. Your site will be live at `https://yourusername.github.io/repo-name/`

### Alternative: Netlify / Vercel

Drag and drop `index.html` + `manifest.json` — instant deploy, no config needed.

### Install as PWA

1. Open the deployed URL on your phone (Chrome or Safari)
2. Tap **"Add to Home Screen"**
3. Opens like a native app — no browser chrome, dark status bar

---

## Technical Notes

### Timezone Handling
NOAA returns timestamps in local time (EST/EDT) without timezone info. The app dynamically detects the current Eastern Time UTC offset using `Intl.DateTimeFormat` and appends it before parsing, preventing the 4–5 hour offset bug that affects naive `new Date()` parsing.

### HRRR vs GFS
The forecast uses Open-Meteo's `minutely_15` endpoint which sources directly from NOAA HRRR (3km resolution, hourly refresh). This is much more useful for local sailing conditions than GFS (22km resolution). HRRR coverage is limited to the continental US.

### B&G-Style Charts
The wind charts are Canvas-drawn to mimic the B&G Advanced WindPlot display found on Zeus/Vulcan chartplotters. The rolling average line lets you spot sustained trends vs momentary fluctuations — particularly useful for identifying wind shifts and building/dying breeze patterns.

### Auto-Refresh
Data refreshes every 10 minutes automatically. Tap the refresh button for immediate update.

---

## File Structure

```
├── index.html      # Complete app — single file, zero dependencies
├── manifest.json   # PWA manifest for "Add to Home Screen"
└── README.md
```

Everything runs client-side. No server, no build step, no bundler, no node_modules.

---

## Customization

To adapt for a different location, edit these values near the top of the `<script>` section in `index.html`:

```javascript
const ST = { BAT: '8518750', ROB: '8530973' };  // NOAA station IDs
const NYC = { lat: 40.6892, lon: -74.0445 };     // Coordinates for forecast
```

Find NOAA station IDs at [tidesandcurrents.noaa.gov](https://tidesandcurrents.noaa.gov/).

---

## License

MIT — use it, modify it, sail with it.

---

*For planning only — not for navigation.*
