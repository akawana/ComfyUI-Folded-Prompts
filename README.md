# Keybinding Extra

A minimal ComfyUI custom node (empty node) that injects handy keyboard shortcuts into the ComfyUI frontend.

In ComfyUI Settings you can enable/disable shortcuts and customize their behavior.

## Features (v1)

### Toggle line comment — `Ctrl + /`
Works in all ComfyUI text editors/areas:

- Ace editor
- CodeMirror editor
- Plain textarea inputs

**Behavior**
- Press `Ctrl + /` to comment/uncomment the current line or selected lines.
- By default it uses `// ` (with a space).
- If a line already starts with `//` or `// `, the shortcut removes it.

### Configurable comment prefix
In **ComfyUI → Settings → Keybinding Extra** you can set any prefix you want, for example:

- `//`
- `#`
- `--`
- `;`
- etc.

There is also an inline toggle in the same row to fully enable/disable this shortcut.

---

## Installation

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/akawana/ComfyUI-Keybinding-extra.git
