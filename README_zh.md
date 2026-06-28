# 🎬 Video Generator Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/downloads/)
[![中文文档](https://img.shields.io/badge/文档-中文-blue)](./README_zh.md)

> **对小白最友好的 AI 图片 & 视频生成技能包** —— 一行代码生成大片，多模型无缝切换。

---

## 🤔 为什么做这个？

你是不是也有这些痛点：

- 😵 想用 AI 生成图片/视频，但 OpenAI / Runway / Kling 的 API 各不相同，接入成本高
- 😵 小白不知道怎么写 Prompt，生成的图质量差
- 😵 想换模型，结果要改一大堆业务代码
- 😵 视频生成是异步的，轮询、超时、限流处理很麻烦

**Video Generator Skill 就是来解决这些问题的。**

---

## ✨ 核心优势

### 🔌 模型热插拔（零代码切换）

```
# 改一行配置，切换底层模型，业务代码完全不用动！
image_model: dalle      →  DALL-E 3
image_model: local-sd   →  本地 Stable Diffusion
image_model: runway     →  Runway
```

底层用了 **策略模式 + 工厂模式**，新增模型只需写一个 Provider 类并注册，核心代码零修改。

### 🧑‍💻 小白模式（内置 Prompt 优化）

小白模式会自动在 Prompt 后面追加画质增强词：

```
# 你输入的 Prompt
"一只猫在花园里"

# 小白模式自动追加（无需你做任何事）
"masterpiece, best quality, 8k, cinematic lighting, 
highly detailed, sharp focus..."
```

生成的图质量直接提升一个档次 ✨

### 🎥 视频生成全自动

- 异步任务自动轮询
- 速率限制智能等待（读取 `retry_after` 头）
- 超时自动取消
- 进度回调（可以做进度条）

---

## 🚀 极简上手指南

### 第一步：安装

```bash
# 方式一：pip 安装（推荐）
pip install video-generator-skill

# 方式二：克隆仓库（开发者）
git clone https://github.com/jie02zhang/video-generator.git
cd video-generator
pip install -e ".[dev]"
```

### 第二步：配置 API Key

```bash
# 方式一：环境变量（推荐）
export OPENAI_API_KEY="sk-你的key"
export RUNWAY_API_KEY="rw_你的key"

# 方式二：配置文件
# 编辑 config.yaml，填入你的 API Key
```

> 💡 **没有 API Key？** 用 `local-sd` 模式，完全离线运行！

### 第三步：生成！

```python
from scripts.facade.ai_studio_skill import create_skill

# 小白模式：一行搞定
skill = create_skill("beginner")
image = skill.generate_image("夕阳下的雪山")
print(f"图片保存在：{image}")
```

---

## 📖 使用示例

### 示例 1：小白极简生成

```python
skill = create_skill("beginner")

# 生成图片
image = skill.generate_image("一只可爱的猫咪")
# → 自动追加画质增强 Prompt，输出高质量图片

# 生成视频
video = skill.generate_video("猫咪在花园里散步")
# → 自动选择默认模型，异步生成，自动轮询
```

### 示例 2：专业模式（多模型切换）

```python
skill = create_skill("standard")

# 切换图片模型
skill.set_image_model("dalle")     # 用 DALL-E 3 生成图片
skill.set_image_model("local-sd")  # 切换到本地 SD（免费！）

# 切换视频模型
skill.set_video_model("runway")    # Runway Gen-3
skill.set_video_model("kling")     # Kling Video

# 自定义参数
video = skill.generate_video(
    prompt="无人机俯瞰城堡",
    duration=10,
    aspect_ratio="16:9"
)
```

### 示例 3：端到端视频生成（图片 + 旁白 + 合成）

```bash
# 从主题开始，全自动生成视频！
python scripts/generate_full_video.py \
  --topic "AI 自动化工作流" \
  --num-segments 5 \
  --output output/ai_video.mp4
```

---

## 🖼️ 效果展示

> ![示例图片](./docs/demo_image.png)
> *小白模式生成 —— 自动追加画质增强词*

> ![架构图](./docs/arch.png)
> *策略模式 + 工厂模式实现模型热插拔*

---

## 🧪 测试

```bash
# 运行所有测试（83 个测试，99%+ 覆盖率）
pytest tests/ -v

# 测试完全使用 Mock，不消耗真实 API 额度 🎉
```

---

## 💬 社区支持

- 🐛 遇到问题？[提交 Issue](https://github.com/jie02zhang/video-generator/issues)
- 💡 有想法？[参与讨论](https://github.com/jie02zhang/video-generator/discussions)

---

## 📄 开源协议

[MIT License](./LICENSE) © 2024 jie02zhang

---

⭐ **觉得好用？点个 Star 支持一下！**
