# Omni-IO Progress Report

Date: 2026-07-16

---

## Background

Omni-IO is an omni-modal generation and understanding skill for Claude Code. It supports generating and understanding images, videos, music, sound effects, speech, 3D content, documents, and other modalities, with dependency-aware parallel task scheduling and cross-turn asset reuse. The goal of this work was to prepare the project for its upcoming open-source release on GitHub, with a focus on identifying security risks and reducing the onboarding effort for new users.

---

## Completed Changes

### 1. Security cleanup: leaked keys in `.env.example`

The review found six real API keys left in `config/.env.example`, which should be an empty template with no real values: `OPENAI_API_KEY`, `WAN_WORKSPACE_ID`, `HUGGINGFACE_API_KEY`, `CLOUDINARY_API_KEY`, `GEMINI_API_KEY`, and `QWEN_API_KEY`. All values have been cleared and rechecked to prevent accidental exposure when the repository is pushed to GitHub.

### 2. Redesigned onboarding flow

The original flow in `setup/quickstart.md` required new users to complete seven manual steps, including opening an editor and entering each key in `.env`. The redesigned flow works as follows:

- **Automatable steps**—installing dependencies, registering the MCP server, installing the skill via a symbolic link, and writing `.env`—are handled by Claude. The user can trigger the flow with a single request: "Help me configure this skill by following setup/quickstart.md."
- **The two steps that cannot be automated** are explicitly identified: registering accounts with third-party services to obtain keys (which requires identity verification on external websites) and restarting Claude Code (Claude cannot restart the process in which it is running).
- **Key collection** now happens in two stages instead of asking for keys modality by modality at the outset. First, Claude displays a fixed feature list from the new `setup/feature_list.md` and asks which features the user wants to enable. It then asks only for the keys associated with the requested features. When the user supplies a key, Claude writes it directly to `.env`; missing keys are skipped without blocking the rest of the setup. Features the user did not mention are not raised proactively.

The flow was tested with a realistic new-user conversation in which the user selected "image generation + video generation" and skipped every key. The result confirmed that the feature list appeared once, only the two relevant keys were requested, skipping did not block the flow, and the process ended with a clear status summary.

### 3. Default provider review

Every modality's default provider in `config/config.yaml` was reviewed. With the exception of image generation, all defaults use free options or options with a free allowance (`wan`, `elevenlabs`, `edge_tts`, `tripo`, `gemini`, `qwen`, `mistral`, and `local`). Image generation currently defaults to the paid `openai` provider, which conflicts with the documentation's "start at zero cost" statement. This has been confirmed as the repository maintainer's personal day-to-day preference because they have an OpenAI key. Before public release, the default should be changed back to `fal`, which offers a free allowance; this has been added to the to-do list.

---

## To Do / Next Steps

- **Pre-GitHub-push checklist** (saved to long-term memory so a reminder can be given at the appropriate time):
  1. Confirm that `config/.env` and `config/.env.example` contain no real keys.
  2. Change `generate.image.provider` in `config/config.yaml` back to `fal`.
- This flow simulation covered only the "skip everything" path. The full loop in which the user supplies a real or placeholder key and Claude writes it to `.env` has not yet been tested. Run this test once more before the public release.
- In the readiness/missing-configuration logic of `check_config()`, `understand.3d` (local, free 3D understanding) currently appears in neither the ready list nor the missing list. This is a minor omission that does not affect functionality, but the item will be absent from the initial setup status. It can be fixed when convenient.
