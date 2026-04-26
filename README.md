# 🤖 FletBot

> A consumer-ready AI assistant, utilizing Flet for lightweight execution on edge hardware.

**FletBot** is a beautiful, consumer-friendly AI assistant powered by **Gemma 4** on Google AI Studio's free tier. Built with [Flet](https://flet.dev) for cross-platform deployment (Android + Desktop).

## Features

- 💬 **Chat with Gemma 4** — Free, powerful AI via Google AI Studio
- 🔄 **Resilient** — Auto-fallback between DeepMind's Gemma 4 models
- 🎨 **Beautiful UI** — Material 3 design with dark/light theme
- 📱 **Cross-platform** — Android (APK) and Desktop (Windows/macOS/Linux)
- 💰 **Ad-supported** — AdMob integration for monetization
- 🧠 **Memory** — Persistent conversation history
- ⚡ **Streaming** — Real-time response rendering as the AI types
- 📝 **Markdown** — Rich AI responses with code highlighting and formatting

## Quick Start

```bash
# Install dependencies
pip install -e .

# Run on desktop
flet run src/main.py

# Build for Android
flet build apk
```

## Get Your Free API Key

1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Paste it into FletBot's login screen

Every free Google account gets:
- **Gemma 4**: Free high-speed AI via DeepMind and Google AI Studio


## Architecture

```
FletBot App
├── Auth (API Key / OAuth)
├── Chat UI (Material 3, Flet)
│   ├── Message List (streaming markdown)
│   ├── Input Bar (multiline, send)
│   └── AdMob Banner (mobile only)
├── Agent Core
│   ├── Runner (message → LLM → response)
│   └── Session Manager (local JSON storage)
└── Resilient Gemma Provider
    ├── Official Link: [deepmind.google/models/gemma/gemma-4/](https://deepmind.google/models/gemma/gemma-4)
    └── Strategy: Multi-model fallback with exponential backoff

```

## License

Copyright © 2025–2026 Kiri Research Labs. All rights reserved.
See [LICENSE](./LICENSE) for details.
