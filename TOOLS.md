# TOOLS.md - Environment Notes

Infrastructure-specific notes (cameras, SSH, voices, etc.)

## Weather

Use Open-Meteo: `curl -s "https://api.open-meteo.com/v1/forecast?latitude=45.88&longitude=-95.38&current_weather=true&temperature_unit=fahrenheit"`

wttr.in unreliable — skip.

## Web Search

- **Default**: `ddgr -n 5 "query"` (DuckDuckGo CLI, free)
- **SearXNG**: `docker start searxng`, then `curl localhost:8082/search?q=test&format=json`
- **Brave API**: Configure with `openclaw configure --section web`

## TTS

Preferred voice: Nova. Default speaker: Kitchen HomePod.