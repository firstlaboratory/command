# Command Centre

Personal dashboard PWA — live at **https://firstlaboratory.github.io/command/**

- **Home** — clock, weather, up next, training, headlines, trends, reading, countdowns, habits, app launcher
- **News** — India, Tamil Nadu, Tech, Business, Auto, World + Google Trends India
- **Plan** — repeating schedule blocks and a task inbox
- **Read** — book shelves with page progress, yearly target, saved articles
- **Training** — Garmin data via intervals.icu (API key stays on your device)

Data is stored in the browser on your device (use More → Backup). Headlines are refreshed every 3 hours by the `Refresh news` GitHub Action into `data/news.json`.
