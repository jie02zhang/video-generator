# 🎬 Video Generator Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/jie02zhang/video-generator?style=social)](https://github.com/jie02zhang/video-generator)

> **The most beginner-friendly AI image & video generation skill**, powered by a pluggable multi-model architecture.

Generate stunning images and videos with a single line of code. Seamlessly switch between DALL-E, Runway, Kling, and local Stable Diffusion — no code changes required.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧑‍💻 **Beginner Mode** | Zero-config image/video generation with auto-optimized prompts |
| 🔌 **Hot-Swappable Models** | Switch AI providers via YAML config — no code changes |
| 🏗️ **Design Patterns** | Strategy + Factory + Facade for maximum extensibility |
| 🎥 **Video Generation** | Async task polling, progress callbacks, rate-limit aware |
| 🖼️ **Image Animation** | Ken Burns, zoom, pan effects for static images |
| 📊 **Data Visualization** | Excel/CSV → animated chart videos |
| 🛡️ **Robust Error Handling** | Retry with exponential backoff, unified exception hierarchy |
| 🌐 **Multi-language TTS** | Built-in `edge-tts` support for 40+ languages |

---

## 🏗️ Architecture Highlights

```
┌─────────────────────────────────────────────┐
│           AIStudioSkill (Facade)            │
│        beginner / standard / expert         │
├─────────────────────────────────────────────┤
│              ProviderFactory                │
│  register("dalle")  →  DalleProvider       │
│  register("runway") →  RunwayProvider      │
│  register("kling")   →  KlingProvider       │
├─────────────────────────────────────────────┤
│            BaseProvider (Strategy)          │
│  generate() · wait_for_completion()         │
└─────────────────────────────────────────────┘
```

**Why this architecture?**

- **Hot-swappable**: Add a new model by creating a Provider class and registering it — core code untouched.
- **Testable**: Mock any provider via the `scripts/providers/mock_provider.py` for offline testing.
- **Scalable**: The Facade pattern hides complexity; users only interact with `generate_image()` / `generate_video()`.

---

## 🚀 Quick Start

### 1. Install

```bash
# Install from PyPI (when published)
pip install video-generator-skill

# Or clone for development
git clone https://github.com/jie02zhang/video-generator.git
cd video-generator
pip install -e ".[dev]"
```

### 2. Configure API Keys

```bash
# Create config.yaml or set environment variables
export OPENAI_API_KEY="sk-..."
export RUNWAY_API_KEY="rw_..."
export KLING_API_KEY="kl_..."
```

### 3. Generate!

```python
from scripts.facade.ai_studio_skill import create_skill

# Beginner mode: zero config
skill = create_skill("beginner")
image_path = skill.generate_image("a cat in a garden")
print(f"Image saved: {image_path}")

# Generate video
video_path = skill.generate_video("a cat walking in a garden")
print(f"Video saved: {video_path}")
```

---

## 📖 Usage

### Beginner Mode (Zero Config)

```python
from scripts.facade.ai_studio_skill import create_skill

skill = create_skill("beginner")

# That's it! Quality presets auto-applied.
image = skill.generate_image("sunset over mountains")
```

### Professional Mode (Multi-Model Switching)

```python
from scripts.facade.ai_studio_skill import create_skill

skill = create_skill("standard")

# Switch image model
skill.set_image_model("dalle")      # DALL-E 3
skill.set_image_model("local-sd")   # Local Stable Diffusion

# Switch video model
skill.set_video_model("runway")     # Runway Gen-3
skill.set_video_model("kling")      # Kling Video

# Generate with custom parameters
response = skill.generate_video(
    prompt="drone shot of a castle",
    duration=10,
    aspect_ratio="16:9"
)
```

### YAML Configuration

```yaml
# config.yaml
default_mode: standard

models:
  image:
    default: dalle
    providers:
      dalle:
        api_key_env: OPENAI_API_KEY
        model: dall-e-3
        default_size: 1024x1024
      local-sd:
        endpoint: http://localhost:7860

  video:
    default: runway
    providers:
      runway:
        api_key_env: RUNWAY_API_KEY
        model: gen-3-alpha
```

---

## 🧪 Testing

```bash
# Run all tests (83 tests, 99%+ coverage)
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=scripts --cov-report=html
```

All tests use Mock providers — **no real API calls, zero cost**.

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest tests/ -v`)
4. Commit (`git commit -m 'Add amazing feature'`)
5. Push (`git push origin feature/amazing-feature`)
6. Open a Pull Request

---

## 📚 Documentation

- [Usage Guide (English)](./docs/USAGE.md)
- [Usage Guide (中文)](./docs/USAGE_zh.md)
- [API Reference](./docs/API.md)
- [Prompt Engineering Guide](./PROMPT.md)

---

## 🙏 Acknowledgments

- [Stable Diffusion](https://stability.ai/) by Stability AI
- [edge-tts](https://github.com/rany2/edge-tts) for offline TTS
- [FFmpeg](https://ffmpeg.org/) for video processing

---

## 📄 License

[MIT License](./LICENSE) © 2024 jie02zhang

---

⭐ **Star this repo** if you find it useful!
