# ⛵ NYC Harbor Sailing Conditions

A mobile-first PWA for real-time sailing conditions in NYC Harbor — designed to check while walking to the dock.

**[Live Demo →](https://yourusername.github.io/nyc-sailing/)** *(update with your URL)*

![Dark nautical theme](https://img.shields.io/badge/theme-dark_nautical-0a1420) ![No API key](https://img.shields.io/badge/API_key-none_required-48bb78) ![Zero build step](https://img.shields.io/badge/build-zero_config-4fd1c5)

---

## What It Shows

### At a Glance
Wind speed, temperature, and tide status in a quick-read banner strip.

### Wind — Robbins Reef (NOAA Station 8530973)
- Current sustained speed, gusts, and direction (cardinal + degrees)
- **2-hour horizontal wind speed chart** — sustained (green), gusts (orange), rolling average (dashed), 12-knot reference line
- **2-hour horizontal wind direction chart** — TWD vs rolling average with shaded deviation
- Toggle to view full NOAA station page in-app

### B&G WindPlot — 30 Minutes
Inspired by the B&G Advanced WindPlot display on Zeus/Vulcan chartplotters:
- **Vertical time axis** — current time at top, 30 minutes ago at bottom
- **TWD panel** (left) — wind direction with rolling average and shaded deviation from mean
- **TWS panel** (right) — wind speed with gusts overlay and rolling average
- Time markers at NOW, -10m, -20m, -30m
- Reveals wind shift patterns and trends at a glance

### Barometric Pressure — Robbins Reef
- Current pressure in mbar
- Trend indicator (Rising/Falling/Steady with rate)
- **3-hour and 6-hour pressure change** with color coding
- **6-hour pressure chart** from NOAA 6-minute data
- Essential for forecasting approaching weather systems

### Tides — The Battery (NOAA Station 8518750)
- Current status: Flooding / Ebbing / Slack with color coding
- Visual progress bar between previous and next tide
- Countdown timer to next tide
- 6-event lookahead with heights
- Toggle tide chart image

### Weather & Temperature
- Current temp in °C and °F with feels-like
- Weather description with emoji icon
- Thunderstorm risk indicator (CAPE-based)
- Water temperature

### Wind Forecast — HRRR (3km resolution)
- 18-hour forecast from NOAA HRRR via Open-Meteo
- Columns: Time, Wind, Gust, Dir (cardinal), Dir (degrees), Temp, Rain
- Current hour highlighted with color-coded wind speeds

### Radar
- Interactive Windy radar embed (lazy-loaded on tap)
- Quick links to Windy and AccuWeather

---

## Data Sources

| Data | Source | Resolution | Update |
|------|--------|-----------|--------|
| Wind (current + history) | [NOAA CO-OPS](https://tidesandcurrents.noaa.gov/stationhome.html?id=8530973) — Robbins Reef | 6-minute | 6 min |
| Barometric pressure | NOAA CO-OPS — Robbins Reef | 6-minute | 6 min |
| Tides | [NOAA CO-OPS](https://tidesandcurrents.noaa.gov/stationhome.html?id=8518750) — The Battery | High/Low events | Daily |
| Water temp | NOAA CO-OPS — The Battery | Point reading | 6 min |
| Forecast | [Open-Meteo](https://open-meteo.com/en/docs/gfs-api) — HRRR model | 3 km / 15-min | Hourly |
| Radar | [Windy](https://www.windy.com) embed | — | Real-time |

All APIs are free, require no API key, and support CORS.

---

## Deployment

### GitHub Pages (recommended)

1. Fork or clone this repo
2. **Settings → Pages → Source**: select `main` branch
3. Live at `https://yourusername.github.io/repo-name/`

### Install as PWA

1. Open the URL on your phone (Chrome or Safari)
2. Tap **"Add to Home Screen"**
3. Opens like a native app — no browser chrome

---

## Technical Notes

### High-DPI Canvas Rendering
All charts use `devicePixelRatio`-aware canvas setup for crisp rendering on Retina/high-DPI mobile screens. The canvas backing store is scaled to match the physical pixel density.

### B&G-Style Vertical Wind Plots
The vertical plots mirror the B&G Advanced WindPlot paradigm where time flows top-to-bottom. A rolling average line provides the reference — deviation from the average is shown as a shaded area, making wind shifts immediately visible. This is particularly useful for spotting oscillating vs. permanent shifts.

### Timezone Handling
NOAA returns timestamps in local time without timezone info. The app dynamically detects the current Eastern Time UTC offset using `Intl.DateTimeFormat` and appends it before parsing.

### HRRR vs GFS
The forecast uses Open-Meteo's `minutely_15` endpoint sourced from NOAA HRRR (3km, hourly refresh) rather than GFS (22km). HRRR is far more useful for local harbor conditions.

---

## File Structure

```
├── index.html      # Complete app — single file, zero dependencies
├── manifest.json   # PWA manifest for home screen install
└── README.md
```

No server, no build step, no node_modules.

---

## Customization

Edit these values near the top of `<script>` in `index.html`:

```javascript
const ST = { BAT: '8518750', ROB: '8530973' };  // NOAA station IDs
const NYC = { lat: 40.6892, lon: -74.0445 };     // Forecast coordinates
```

Find NOAA station IDs at [tidesandcurrents.noaa.gov](https://tidesandcurrents.noaa.gov/).

---

## License

MIT — use it, modify it, sail with it.

*For planning only — not for navigation.*
