# Quick Start

## Prerequisites

- Python 3.10+
- Claude Code

---

## Let Claude Install It for You (Recommended)

Open Claude Code in this directory and say:

> "Help me configure this skill by following setup/quickstart.md."

Claude will automatically complete steps 1, 3, 4, and 5 (write `.env`, install dependencies, register the MCP server, and install the skill). You only need to do two things yourself:

- **Register with third-party services to obtain API keys.** Claude cannot create accounts for you on external websites. During setup, Claude will ask whether you have each relevant key. If not, skip it, start with the free features, and add the key later.
- **Restart Claude Code in step 6.** Claude cannot restart the process in which it is running.

If you prefer a fully manual setup, continue with the steps below.

---

## Installation

### 1. Configure API Keys

```bash
cp config/.env.example config/.env
```

> **Instructions for Claude** (follow these when the user requests automatic setup; use both stages and do not skip directly to asking for keys):
>
> **Stage 1 — Ask which features the user wants before asking for keys:** Read [`setup/feature_list.md`](feature_list.md), display the list exactly as written, and ask, "Which of these features would you like to enable?"
>
> **Stage 2 — Ask for keys only for features the user mentioned:** Skip modalities the user did not mention and do not proactively ask them to configure those modalities. For each requested feature, use the default provider for that modality in [`setup/api_guide.md`](api_guide.md) and ask whether the user has the corresponding key. When the user provides a key, use the Edit tool to write it directly to the relevant `KEY_NAME=` line in `config/.env`; do not require the user to open the file. If the user says they do not have the key or want to skip it, move on without blocking the setup. After all relevant keys have been covered, or the user says to stop there, summarize which modalities are ready and which still require configuration.

For manual configuration, open `config/.env` in a text editor and enter the API keys for the services you need. Features whose keys are left blank will be skipped.

> Not sure which keys you need? See [`setup/api_guide.md`](api_guide.md). To start at zero cost, register just four free accounts: fal.ai, ElevenLabs, Hugging Face, and Tripo3D.

### 2. Set the Workspace

Choose a directory in which to save all generated files. Remember this path; you will need it in the next step.

```
~/Documents/OmniIO
```

Choose a **persistent directory**, not `/tmp`. The directory does not need to exist yet.

### 3. Install Dependencies

Creating a virtual environment first is recommended to keep the system Python clean:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r mcp/requirements.txt
playwright install chromium  # Required for web browsing; first time only
```

### 4. Register the MCP Server

Open a terminal in this directory and run the following command, replacing the placeholders with real paths:

```bash
claude mcp add omni-io \
  --scope user \
  -e OMNI_OUTPUT_DIR="/path/to/the/workspace/from-step-2" \
  -- /absolute/path/to/this/directory/.venv/bin/python \
  /absolute/path/to/this/directory/mcp/server.py
```

**Example** (if this directory is `/Users/alice/Omni-IO-Skills` and the workspace is `~/Documents/OmniIO`):

```bash
claude mcp add omni-io \
  --scope user \
  -e OMNI_OUTPUT_DIR="/Users/alice/Documents/OmniIO" \
  -- /Users/alice/Omni-IO-Skills/.venv/bin/python \
  /Users/alice/Omni-IO-Skills/mcp/server.py
```

After registration, verify the connection:

```bash
claude mcp list
# Expected: omni-io: ... ✔ Connected
```

> **Note:** Older documentation instructed users to edit the `mcpServers` field in `~/.claude/settings.json` manually. Claude Code v2+ no longer reads MCP configuration from that field; you must register it with `claude mcp add`.

> To obtain the absolute path of the current directory, run `pwd`.

### 5. Install the Skill

```bash
# Create the skills directory if it does not exist
mkdir -p ~/.claude/skills

# Recommended: symbolic link (skill-file changes take effect immediately, and there is only one config/.env)
ln -s "$(pwd)" ~/.claude/skills/omni-io

# Alternative: copy (afterward, edit config/.env in the original directory, not the skills directory)
# cp -r "$(pwd)" ~/.claude/skills/omni-io
```

### 6. Restart Claude Code

Quit and reopen Claude Code. The MCP server and skill will load automatically.

### 7. Start Using It

Describe your task directly, for example:

- "Generate a cyberpunk wallpaper and pair it with 15 seconds of atmospheric sound effects."
- "Create a 12-slide business presentation reviewing Q3 sales."
- "Use this image as a reference to generate a 3D model."

On first use, Claude will automatically check which features are ready and which still require keys.

---

## Where Are Generated Files Saved?

They are saved in the workspace directory specified in step 2 (`OMNI_OUTPUT_DIR`). The registry file, `registry.json`, is stored in the same directory and persists across sessions, so you can say, "Turn the image from last time into a video."

---

## Troubleshooting

**Error: "API key is not configured"**  
→ Enter the corresponding key in `config/.env` in the original directory, then restart Claude Code by quitting and reopening it.

**Changes to `config/.env` do not take effect**  
→ Restart Claude Code so the MCP server reloads the environment variables.

**I want to use a different generation model**  
→ Change the `provider` field for the relevant modality in `config/config.yaml`. See [`setup/api_guide.md`](api_guide.md).

**`pip install` reports a permission error or dependency conflict**  
→ Confirm that the virtual environment is active with `source .venv/bin/activate`, then run the installation again.

**MCP tools are unavailable in every new conversation**  
→ The server was probably registered using the old `mcpServers` field in `settings.json`, which Claude Code v2+ does not read. Repeat step 4 using `claude mcp add`, then run `claude mcp list` and confirm that it shows `✔ Connected`.

**The MCP server fails to start; how can I diagnose it?**  
→ Start it manually in a terminal to see the error. First `cd` into this directory, then run `source .venv/bin/activate && python mcp/server.py`.
