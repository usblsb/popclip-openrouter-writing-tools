# OpenRouter Writing Tools — PopClip extension

7 AI-powered writing actions for [PopClip](https://www.popclip.app/), all routed through [OpenRouter](https://openrouter.ai/) with **one single API key**. Models are limited to **OpenAI** and **Google Gemini** for predictable quality.

![macOS](https://img.shields.io/badge/macOS-12%2B-blue) ![PopClip](https://img.shields.io/badge/PopClip-4069%2B-orange) ![License](https://img.shields.io/badge/License-MIT-green) ![OpenRouter](https://img.shields.io/badge/Powered_by-OpenRouter-purple)

## What it does

Select any text in any app, click one of the 7 actions in PopClip, and the selection is replaced in place with the AI result.

| # | Action | Icon | What it does | Model | Temp | Tokens |
|---|---|---|---|---|---|---|
| 1 | **Correct** | ✓ | Fix typos, grammar, punctuation. Does not rewrite. | `openai/gpt-4o-mini` | 0.1 | 800 |
| 2 | **Translate** | 🌐 | Translate. **Auto mode** by default: Spanish ↔ English (any other language → English). Configurable. | `google/gemini-2.5-flash` | 0.2 | 2000 |
| 3 | **Summarize** | ☰ | Long text → short paragraph or bullet points | `openai/gpt-4o-mini` | 0.3 | 800 |
| 4 | **Improve email/message** | ✉ | Clean, clarify, drop filler words and repeated ideas | `google/gemini-2.5-pro` | 0.4 | 2000 |
| 5 | **Improve content** | 📄 | Merge multiple pasted fragments into a coherent document, highlighting key points with `**bold**` | `openai/gpt-4o` | 0.5 | 4000 |
| 6 | **Format HTML** | `</>` | Wrap text in semantic HTML using only `<h2>`, `<h3>`, `<h4>`, `<p>`, `<ol>`, `<ul>`, `<li>`, `<strong>`, `<u>` | `openai/gpt-4o` | 0.2 | 8000 |
| 7 | **Format Markdown** | M | Convert text to Markdown using only `##`, `###`, `####`, paragraphs, `1.`/`-` lists, `**bold**`, and `<u>` for underline | `openai/gpt-4o` | 0.2 | 8000 |

The 7 actions are always visible in the PopClip popover when you have text selected.

### Translate "auto" mode (default)

| Selected text | Output |
|---|---|
| `Hola, ¿como estas?` (Spanish) | `Hello, how are you?` (English) |
| `Hello, how are you?` (English) | `Hola, ¿como estas?` (Spanish) |
| `Bonjour le monde` (French) | `Hello world` (English) |
| `Guten Tag` (German) | `Hello` (English) |

To force a fixed target language (e.g. always translate to German), open **PopClip → Preferences → Extensions → OpenRouter Writing Tools** and set **Target language** to `german`, `french`, `italian`, `portuguese`, `japanese`, etc. To restore auto mode, set it back to `auto`.

## Requirements

- macOS 12 or later
- [PopClip](https://www.popclip.app/) 4069 or later
- An [OpenRouter](https://openrouter.ai/) account with an API key (starts with `sk-or-v1-...`). Free models are available — paid models charge against your OpenRouter credit.
- `python3` (ships with macOS, no extra install required)

## Installation

### Option A — Clone the repo

```bash
git clone https://github.com/usblsb/popclip-openrouter-writing-tools.git
cd popclip-openrouter-writing-tools
open OpenRouterWritingTools.popclipext
```

PopClip will pick up the folder and prompt you to install.

### Option B — Download

1. Download the latest `OpenRouterWritingTools.popclipext.zip` from [Releases](../../releases) and unzip.
2. Double-click the unzipped folder.
3. PopClip will ask to install — confirm.

### Configure

Open **PopClip → Preferences → Extensions → OpenRouter Writing Tools** and:

1. Paste your **OpenRouter API Key** (get one at https://openrouter.ai/keys — required).
2. (Optional) Set the **Response language**. Default is `auto` (keep input language). Use `spanish`, `english`, etc. to force a specific language for tasks that don't already have one.
3. (Optional) Set the **Target language** for Translate. Default is `auto` (Spanish ↔ English).

## Usage

1. Select any text in any macOS app.
2. The PopClip popover appears with the 7 buttons.
3. Click an action → it sends the text to OpenRouter, gets the result, and **replaces the selection** with the AI output.

If something fails (no API key, network error, OpenRouter quota exceeded, model rate limit, etc.) PopClip shows a failure indicator and the selection is **not** modified.

## How it works

The extension is a single PopClip shell action defined in [`OpenRouterWritingTools.popclipext/Config.json`](OpenRouterWritingTools.popclipext/Config.json). Each of the 7 actions runs the same Python script with a different task name as the first argument:

- [`jl_writingtools.py`](OpenRouterWritingTools.popclipext/jl_writingtools.py) reads `$POPCLIP_TEXT` (the selection), `$POPCLIP_OPTION_*` (your settings) and `sys.argv[1]` (the action name).
- It picks the right system prompt, model, temperature and `max_tokens` for that task.
- It POSTs to `https://openrouter.ai/api/v1/chat/completions` (OpenAI-compatible). The `HTTP-Referer` and `X-Title` headers identify the extension on OpenRouter's dashboard.
- The model's text response is written to stdout, which PopClip pastes via `after: paste-result`.

Zero external dependencies — uses only the Python standard library (`urllib`, `json`, `os`, `sys`).

## Customising

If you want to change the model, temperature, max_tokens or system prompt of any task, edit [`jl_writingtools.py`](OpenRouterWritingTools.popclipext/jl_writingtools.py) directly:

- `TASKS` dict (around line 165): per-task model + temperature + max_tokens
- `SYSTEM_PROMPTS` dict (around line 30): per-task system prompt

After editing, reinstall the extension (or toggle it off/on in PopClip) to pick up the changes.

## Privacy

By default, OpenRouter may forward your prompts to providers that train on user data. To disable this, go to your [OpenRouter privacy settings](https://openrouter.ai/settings/privacy) and enable the **"do not train"** option. This is enforced at the OpenRouter side; the extension itself sends nothing besides what you select.

The extension does **not** log, cache, or send your text anywhere except to OpenRouter.

> **Note on the API key**: in this version the OpenRouter API key is stored as a plain string inside PopClip's preferences plist (not in macOS Keychain). A previous attempt to use `type: "secret"` (Keychain-backed) caused PopClip to never display the action buttons because the value wasn't being read back correctly. A future version may revisit this with a workaround.

## Limitations & known issues

- **Click always pastes**, regardless of modifier keys. A future version may add `Shift+click → copy without pasting`.
- **No streaming**. The extension waits for the full response before pasting (typical: 1-5 seconds depending on task and text length).
- **No per-action toggles** in this version. All 7 actions are always visible in the PopClip popover. To hide actions you don't use, disable them globally via PopClip → Preferences → Appearance → Actions order. A future version may bring back per-action toggles via a JS-module extension that generates actions dynamically.
- **Model availability**: OpenRouter's catalog changes; if a model name disappears, edit `jl_writingtools.py` and replace it. Check current models at https://openrouter.ai/models.

## License

MIT — see [LICENSE](LICENSE).

## Credits

- **Idea, product direction & UX decisions** — [Juan Luis Martel](https://github.com/usblsb).
- **Built with love using [Claude Code](https://claude.com/claude-code)** powered by **Claude Opus 4.7 (1M context)** — Anthropic's CLI for Claude. Claude wrote the shell action, the Python OpenRouter client, the per-task system prompts, and the PopClip configuration under Juan's supervision and review.
- **Powered by** [OpenRouter](https://openrouter.ai/) (model routing) and [PopClip](https://www.popclip.app/) (text-selection automation).
