# Keybinding Extra

A minimal ComfyUI custom node (empty node) that injects handy keyboard shortcuts into the ComfyUI frontend.

In ComfyUI Settings you can enable/disable shortcuts and customize their behavior.

## Features (v1)

This extension provides **two** keyboard shortcuts:

1. **Toggle line comment — `Ctrl + /`**
2. **Delete line — `Ctrl + Shift + L`**

---

### Toggle line comment — `Ctrl + /`

Works in all ComfyUI text editors/areas:

- Ace, CodeMirror, Plain textarea inputs

**Behavior**
- Press `Ctrl + /` to comment/uncomment the current line or selected lines.
- By default it uses `// ` (with a space).
- If a line already starts with `//` or `// `, the shortcut removes it.

---

### Delete line — `Ctrl + Shift + L`

Works in the same editors/areas:

- Ace, CodeMirror, Plain textarea inputs

**Behavior**
- Press `Ctrl + Shift + L` to delete the current line.
- If multiple lines are selected, deletes all selected lines.
- Deletion is integrated with editor undo (`Ctrl + Z`) where supported.

---

### Configurable comment prefix

In **ComfyUI → Settings → Keybinding Extra** you can set any prefix you want, for example:

- `//`
- `#`
- `--`
- `;`
- etc.

There is also an enable/disable toggle for the comment shortcut in the settings.

---

## Installation

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/akawana/ComfyUI-Keybinding-extra.git
