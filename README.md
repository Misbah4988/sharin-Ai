# Sharin AI — Browser Edition

Responsive browser-based version of Sharin with a lightweight Crystal Dark Glass theme.

## Features
- Responsive layout for desktop, tablet, and mobile browsers
- LiveKit Inference chat backend
- Browser speech input where supported and browser text-to-speech replies
- Weather lookup using OpenWeather (optional)
- Quick links and conversation text download
- Introduction always includes **Designed by Misbah Ur Rehman.**

## Important architecture note
GitHub stores the source code; GitHub Pages alone cannot run the Python backend or safely store API secrets. Deploy this project to a Python-capable host such as Render, and keep your API keys in that host's Environment settings. Do not place secrets in browser JavaScript or commit a real `.env` file.

## Deploy to GitHub + Render
1. Create a GitHub repository and upload all files in this folder.
2. Open Render and create a new **Web Service** connected to that repository.
3. Render should detect `render.yaml`; otherwise use:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. In the Render service's Environment settings, add:
   - `LIVEKIT_URL`
   - `LIVEKIT_API_KEY`
   - `LIVEKIT_API_SECRET`
   - `OPENWEATHER_API_KEY` (optional)
   - `DEFAULT_CITY` (optional; e.g. `Sargodha`)
5. Deploy. Open the HTTPS URL Render gives you on any device.

## Run locally
Requires Python 3.10+ (check the installed LiveKit Agents package's supported Python versions).

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

Set the environment variables in your shell, or copy `.env.example` to `.env` and fill in the values. Never commit `.env`.

```bash
uvicorn app:app --reload
```

Open http://127.0.0.1:8000

## Browser limitations
- Microphone access requires permission and generally works on HTTPS (or localhost).
- Voice input depends on browser support; Chrome/Edge support is generally best.
- Spoken replies use the browser's speech synthesis, so the available voice differs by device.
- Browsers cannot silently control Windows Notepad/Calculator or capture the entire desktop. The Download text action exports the chat instead.
- Weather is optional and requires an OpenWeather API key.
- LiveKit model access and model names must be enabled for your LiveKit account.
