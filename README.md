# Unpack

You're on the bus to campus, or walking to grab coffee, or just done staring at code for three hours. You want to keep learning but you're tired of reading. What if you could listen to how Netflix handles failovers, why Stripe chose idempotency keys, or how Discord scaled to millions of concurrent users, explained like a senior engineer talking to you over lunch?

Unpack converts technical blog posts into audio. Most content is first-person narration: one voice, one perspective, thinking out loud through the problem. When the content calls for it, that switches to a back-and-forth discussion between two engineers debating trade-offs or walking through a decision together. System design, infrastructure deep-dives, real production case studies. Built for CS students who want to learn from the industry without being glued to a screen.

## How It Works

Source articles go through a 7-step pipeline:

1. **Term Extraction** - identifies technical terms and generates pronunciations
2. **Deep Analysis** - breaks down article structure, concepts, and audio-friendliness
3. **Blueprint** - plans the script section by section (hook, foundation, core, anchor)
4. **Script Generation** - writes the full first-person narration
5. **Quality Gate** - checks for hallucination, omission, and tone violations
6. **TTS Preparation** - replaces technical terms with pronunciation-friendly forms
7. **Audio Generation** - produces the final MP3

Admin curates all content. No user-generated content.

## Tech Stack

| Concern  | Choice                            |
|----------|-----------------------------------|
| Language | Python 3.12+                      |
| Framework| Litestar                          |
| Database | PostgreSQL (SQLAlchemy async)      |
| LLM      | Groq                              |
| TTS      | edge-tts                          |
| Audio    | pydub + ffmpeg                    |

## Setup
```
uv sync
```
```
cp .env.example .env
```
Required environment variables:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/unpack
GROQ_API_KEY=your_key_here
AUDIO_STORAGE_PATH=./storage/audio
```
## Run
```
make dev
```
## Test
```
make test
```
## Lint & Format
```
make lint
make fmt
```