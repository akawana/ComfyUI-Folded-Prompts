import { app } from "../../scripts/app.js";

const CMD_ID                    = "keybinding_extra.toggle";
const SETTING_ID                = "keybinding_extra.comment_prefix";
const FALLBACK_KEY              = "keybinding_extra.comment_prefix";
const ENABLE_ID                 = "keybinding_extra.enabled";
const ENABLE_FALLBACK_KEY       = "keybinding_extra.enabled";
const DELETE_LINE_ENABLED_ID    = "keybinding_extra.delete_line_enabled";
const DELETE_LINE_FALLBACK_KEY  = "keybinding_extra.delete_line_enabled";
const EXTRACT_WORD_ENABLED_ID   = "keybinding_extra.extract_word_enabled";
const EXTRACT_WORD_FALLBACK_KEY = "keybinding_extra.extract_word_enabled";
const POWER_TAG_ENABLED_ID      = "keybinding_extra.power_tag_enabled";
const POWER_TAG_FALLBACK_KEY    = "keybinding_extra.power_tag_enabled";
const MOVE_TAG_ENABLED_ID       = "keybinding_extra.move_tag_enabled";
const MOVE_TAG_FALLBACK_KEY     = "keybinding_extra.move_tag_enabled";

/* ══════════════════════════════════════════════════════════════════════════════
   TAG PARSING
   A tag is any sequence of chars that is NOT a comma or newline.
   A powered tag looks like: (tag text: 1.05) — parens + colon + number.
   Comment prefix (e.g. "// ") at the start of a line is NOT part of any tag.
══════════════════════════════════════════════════════════════════════════════ */

// Split the "rest" part of a line (after comment prefix) into tags.
// Returns array of { raw, trimmed, start, end } relative to rest start.
function parseTagsInLine(rest) {
    const tags = [];
    const parts = rest.split(",");
    let pos = 0;
    for (const part of parts) {
        const trimmed = part.trim();
        const start = pos;
        const end   = pos + part.length;
        tags.push({ raw: part, trimmed, start, end });
        pos = end + 1; // +1 for comma
    }
    return tags;
}

// Rebuild from array of trimmed tag strings: always "t0, t1, t2, "
function rebuildLine(tagStrings) {
    if (tagStrings.length === 0) return "";
    return tagStrings.map(t => t.trim()).filter(t => t.length > 0).join(", ") + ", ";
}

// Strip comment prefix from a line, return { commentPrefix, rest }.
// commentPrefix is the leading comment marker + space (e.g. "// "),
// rest is everything after it. If no prefix found, commentPrefix = "".
function stripLineComment(line) {
    const { prefix, prefixSp } = computePrefix();
    const trimmed  = line.trimStart();
    const indent   = line.length - trimmed.length;
    const indentStr = line.slice(0, indent);
    if (trimmed.startsWith(prefixSp)) {
        return { commentPrefix: indentStr + prefixSp, rest: trimmed.slice(prefixSp.length) };
    }
    if (trimmed.startsWith(prefix)) {
        return { commentPrefix: indentStr + prefix, rest: trimmed.slice(prefix.length) };
    }
    return { commentPrefix: "", rest: line };
}

// Find which tag index the cursor column falls into (col relative to rest start).
function tagIndexAtCol(tags, col) {
    for (let i = 0; i < tags.length; i++) {
        if (col >= tags[i].start && col <= tags[i].end) return i;
    }
    return tags.length - 1;
}

// Given a full line string and cursor col (relative to line start),
// return { tagStr, tagIndex, tags, commentPrefix, offset }
// where offset = commentPrefix.length, tags are relative to rest.
function findTagAtCol(line, col) {
    const { commentPrefix, rest } = stripLineComment(line);
    const offset      = commentPrefix.length;
    const adjustedCol = Math.max(0, col - offset);
    const tags        = parseTagsInLine(rest);
    const idx         = tagIndexAtCol(tags, adjustedCol);
    if (idx < 0 || idx >= tags.length) return null;
    const tag = tags[idx];
    if (!tag.trimmed) return null;
    return { tagStr: tag.trimmed, tagIndex: idx, tags, commentPrefix, offset, adjustedCol };
}

// Powered tag regex: ( content : number ) with any spacing
const POWERED_RE = /^\(\s*(.+?)\s*:\s*(\d+(?:\.\d+)?)\s*\)$/;

function parsePowered(tag) {
    const m = tag.trim().match(POWERED_RE);
    if (!m) return null;
    return { inner: m[1].trim(), value: parseFloat(m[2]) };
}

function makePowered(inner, value) {
    const rounded = Math.round(value * 100) / 100;
    const str = rounded.toFixed(2).replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "");
    return `(${inner}: ${str})`;
}

/* ══════════════════════════════════════════════════════════════════════════════
   EDITOR DETECTION
══════════════════════════════════════════════════════════════════════════════ */

let _lastFocusedEditor = null;

function trackFocus() {
    window.addEventListener("focusin", () => {
        const cm = getActiveCodeMirror();
        if (cm) { _lastFocusedEditor = { type: "cm", ref: cm }; return; }
        const ta = getActiveTextarea();
        if (ta) { _lastFocusedEditor = { type: "ta", ref: ta }; }
    }, true);
}

function getActiveCodeMirror() {
    const active = document.activeElement;
    let el = active;
    while (el && el !== document.body) {
        if (el.classList && el.classList.contains("cm-editor")) return el.cmView || el;
        el = el.parentElement;
    }
    const cmEditors = document.querySelectorAll(".cm-editor");
    return cmEditors.length ? (cmEditors[0].cmView || cmEditors[0]) : null;
}

function getActiveTextarea() {
    const active = document.activeElement;
    if (!active) return null;
    if (active.tagName === "TEXTAREA" || active.tagName === "INPUT") return active;
    return null;
}

function getEditorForShortcut() {
    const cm = getActiveCodeMirror();
    if (cm) return { type: "cm", ref: cm };
    const ta = getActiveTextarea();
    if (ta) return { type: "ta", ref: ta };
    return _lastFocusedEditor;
}

/* ══════════════════════════════════════════════════════════════════════════════
   SETTINGS
══════════════════════════════════════════════════════════════════════════════ */

function sanitizePrefix(v) {
    if (v == null) return "//";
    const s = String(v).trim();
    return s.length ? s : "//";
}

function getCommentPrefix() {
    const api = app.ui?.settings;
    let v = null;
    if (api?.getSettingValue) { try { v = api.getSettingValue(SETTING_ID); } catch {} }
    if (!v) { try { v = localStorage.getItem(FALLBACK_KEY); } catch {} }
    return sanitizePrefix(v);
}

function computePrefix() {
    const prefix = getCommentPrefix();
    return { prefix, prefixSp: prefix + " " };
}

function getBoolSetting(id, fallbackKey, def = true) {
    const api = app.ui?.settings;
    if (api?.getSettingValue) {
        try {
            const v = api.getSettingValue(id);
            if (v !== undefined && v !== null) return !!v;
        } catch {}
    }
    try {
        const raw = localStorage.getItem(fallbackKey);
        if (raw !== null) return raw !== "false";
    } catch {}
    return def;
}

function isToggleEnabled()      { return getBoolSetting(ENABLE_ID,              ENABLE_FALLBACK_KEY); }
function isDeleteLineEnabled()  { return getBoolSetting(DELETE_LINE_ENABLED_ID, DELETE_LINE_FALLBACK_KEY); }
function isExtractWordEnabled() { return getBoolSetting(EXTRACT_WORD_ENABLED_ID,EXTRACT_WORD_FALLBACK_KEY); }
function isPowerTagEnabled()    { return getBoolSetting(POWER_TAG_ENABLED_ID,   POWER_TAG_FALLBACK_KEY); }
function isMoveTagEnabled()     { return getBoolSetting(MOVE_TAG_ENABLED_ID,    MOVE_TAG_FALLBACK_KEY); }

function registerPrefixSetting() {
    const api = app.ui?.settings;
    const def = "//";
    if (api?.addSetting) {
        api.addSetting({ id: SETTING_ID,             category: ["Keybinding Extra", "Comment (Ctrl+/)",                          "B"], name: "Line comment prefix:",                   type: "text",    defaultValue: def,  placeholder: "// or # or --", onChange: v => { try { localStorage.setItem(FALLBACK_KEY,              sanitizePrefix(v));       } catch {} } });
        api.addSetting({ id: ENABLE_ID,              category: ["Keybinding Extra", "Comment (Ctrl+/)",                          "A"], name: "Enable line comment:",                   type: "boolean", defaultValue: true, onChange: v => { try { localStorage.setItem(ENABLE_FALLBACK_KEY,        v ? "true" : "false"); } catch {} } });
        api.addSetting({ id: DELETE_LINE_ENABLED_ID, category: ["Keybinding Extra", "Delete Line (Ctrl+Shift+L)",                "A"], name: "Enable delete current line:",            type: "boolean", defaultValue: true, onChange: v => { try { localStorage.setItem(DELETE_LINE_FALLBACK_KEY,  v ? "true" : "false"); } catch {} } });
        api.addSetting({ id: EXTRACT_WORD_ENABLED_ID,category: ["Keybinding Extra", "Extract & Comment Tag (Ctrl+Shift+/)",      "A"], name: "Enable extract tag to commented line:", type: "boolean", defaultValue: true, onChange: v => { try { localStorage.setItem(EXTRACT_WORD_FALLBACK_KEY, v ? "true" : "false"); } catch {} } });
        api.addSetting({ id: POWER_TAG_ENABLED_ID,   category: ["Keybinding Extra", "Power Tag (Ctrl+Up / Ctrl+Down / Ctrl+Backspace)", "A"], name: "Enable power tag shortcuts:",    type: "boolean", defaultValue: true, onChange: v => { try { localStorage.setItem(POWER_TAG_FALLBACK_KEY,   v ? "true" : "false"); } catch {} } });
        api.addSetting({ id: MOVE_TAG_ENABLED_ID,    category: ["Keybinding Extra", "Move Tag (Ctrl+Alt+Left / Ctrl+Alt+Right)", "A"], name: "Enable move tag shortcuts:",            type: "boolean", defaultValue: true, onChange: v => { try { localStorage.setItem(MOVE_TAG_FALLBACK_KEY,    v ? "true" : "false"); } catch {} } });
    } else {
        if (!localStorage.getItem(FALLBACK_KEY))             localStorage.setItem(FALLBACK_KEY,              def);
        if (!localStorage.getItem(ENABLE_FALLBACK_KEY))      localStorage.setItem(ENABLE_FALLBACK_KEY,       "true");
        if (!localStorage.getItem(DELETE_LINE_FALLBACK_KEY)) localStorage.setItem(DELETE_LINE_FALLBACK_KEY,  "true");
        if (!localStorage.getItem(EXTRACT_WORD_FALLBACK_KEY))localStorage.setItem(EXTRACT_WORD_FALLBACK_KEY, "true");
        if (!localStorage.getItem(POWER_TAG_FALLBACK_KEY))   localStorage.setItem(POWER_TAG_FALLBACK_KEY,    "true");
        if (!localStorage.getItem(MOVE_TAG_FALLBACK_KEY))    localStorage.setItem(MOVE_TAG_FALLBACK_KEY,     "true");
    }
}

/* ══════════════════════════════════════════════════════════════════════════════
   CODEMIRROR HELPERS
══════════════════════════════════════════════════════════════════════════════ */

function cmView(cmRoot) {
    return cmRoot.cmView || cmRoot.view || cmRoot;
}

function cmGetCursorLine(cmRoot) {
    const view = cmView(cmRoot);
    if (!view?.state) return null;
    const head = view.state.selection.main.head;
    const line = view.state.doc.lineAt(head);
    const col  = head - line.from;
    return { view, line, col, head };
}

function cmReplaceLine(view, line, newText, newCursorCol) {
    const col = Math.min(newCursorCol, newText.length);
    view.dispatch({
        changes:   { from: line.from, to: line.to, insert: newText },
        selection: { anchor: line.from + col },
        userEvent: "input"
    });
}

/* ══════════════════════════════════════════════════════════════════════════════
   TEXTAREA HELPERS
══════════════════════════════════════════════════════════════════════════════ */

function taGetCursorLine(ta) {
    const val  = ta.value;
    const pos  = ta.selectionStart;
    const ls   = val.lastIndexOf("\n", pos - 1) + 1;
    const le   = val.indexOf("\n", pos);
    const end  = le === -1 ? val.length : le;
    const line = val.substring(ls, end);
    const col  = pos - ls;
    return { val, ls, end, line, col };
}

function taReplaceLine(ta, ls, end, newText, newCursorCol) {
    const val    = ta.value;
    const col    = Math.min(newCursorCol, newText.length);
    const before = val.slice(0, ls);
    const after  = val.slice(end);
    ta.value = before + newText + after;
    ta.selectionStart = ta.selectionEnd = ls + col;
    ta.dispatchEvent(new Event("input", { bubbles: true }));
}

/* ══════════════════════════════════════════════════════════════════════════════
   TOGGLE LINE COMMENT  (Ctrl+/)
══════════════════════════════════════════════════════════════════════════════ */

function runToggleOnFocusedEditor() {
    const cm = getActiveCodeMirror();
    if (cm) { toggleCodeMirrorComments(cm); return; }
    const ta = getActiveTextarea();
    if (ta) { toggleTextareaComments(ta); }
}

function toggleCodeMirrorComments(cmRoot) {
    const view = cmView(cmRoot);
    if (!view?.state?.dispatch) return;
    const { prefix, prefixSp } = computePrefix();
    const state = view.state;
    const sel   = state.selection.main;
    const doc   = state.doc;
    let fromLine = doc.lineAt(sel.from).number;
    let toLine   = doc.lineAt(sel.to).number;
    if (sel.to > sel.from && doc.lineAt(sel.to).from === sel.to) toLine--;
    const changes = [];
    for (let n = fromLine; n <= toLine; n++) {
        const line    = doc.line(n);
        const text    = line.text;
        const trimmed = text.trimStart();
        const indent  = text.length - trimmed.length;
        if (trimmed.startsWith(prefixSp)) {
            const idx = text.indexOf(prefixSp, indent);
            if (idx !== -1) changes.push({ from: line.from + idx, to: line.from + idx + prefixSp.length, insert: "" });
        } else if (trimmed.startsWith(prefix)) {
            const idx = text.indexOf(prefix, indent);
            if (idx !== -1) changes.push({ from: line.from + idx, to: line.from + idx + prefix.length, insert: "" });
        } else {
            changes.push({ from: line.from + indent, to: line.from + indent, insert: prefixSp });
        }
    }
    if (changes.length) view.dispatch({ changes });
}

function toggleTextareaComments(ta) {
    const { prefix, prefixSp } = computePrefix();
    const value = ta.value;
    const start = ta.selectionStart;
    const end   = ta.selectionEnd;
    const lines = value.split("\n");
    let pos = 0, startLine = 0, endLine = lines.length - 1;
    for (let i = 0; i < lines.length; i++) {
        const ll = lines[i].length + 1;
        if (start >= pos && start < pos + ll) startLine = i;
        if (end   >= pos && end   < pos + ll) { endLine = i; break; }
        pos += ll;
    }
    for (let i = startLine; i <= endLine; i++) {
        const line    = lines[i];
        const trimmed = line.trimStart();
        const indent  = line.length - trimmed.length;
        if (trimmed.startsWith(prefixSp)) {
            const idx = line.indexOf(prefixSp, indent);
            if (idx !== -1) lines[i] = line.slice(0, idx) + line.slice(idx + prefixSp.length);
        } else if (trimmed.startsWith(prefix)) {
            const idx = line.indexOf(prefix, indent);
            if (idx !== -1) lines[i] = line.slice(0, idx) + line.slice(idx + prefix.length);
        } else {
            lines[i] = line.slice(0, indent) + prefixSp + line.slice(indent);
        }
    }
    ta.value = lines.join("\n");
    ta.selectionStart = start;
    ta.selectionEnd   = end;
    ta.dispatchEvent(new Event("input", { bubbles: true }));
}

/* ══════════════════════════════════════════════════════════════════════════════
   DELETE LINE  (Ctrl+Shift+L)
══════════════════════════════════════════════════════════════════════════════ */

function deleteCurrentLine() {
    const cm = getActiveCodeMirror();
    if (cm) { deleteCurrentLineCodeMirror(cm); return; }
    const ta = getActiveTextarea();
    if (ta) { deleteCurrentLineTextarea(ta); }
}

function deleteCurrentLineCodeMirror(cmRoot) {
    const view   = cmView(cmRoot);
    if (!view?.state?.dispatch) return;
    const cursor = view.state.selection.main.head;
    const line   = view.state.doc.lineAt(cursor);
    view.dispatch({
        changes:   { from: line.from, to: Math.min(line.to + 1, view.state.doc.length) },
        selection: { anchor: line.from },
        userEvent: "delete"
    });
}

function deleteCurrentLineTextarea(ta) {
    const { ls, end } = taGetCursorLine(ta);
    const val     = ta.value;
    const lineEnd = end < val.length ? end + 1 : end;
    ta.setSelectionRange(ls, lineEnd);
    document.execCommand("delete");
    ta.dispatchEvent(new Event("input", { bubbles: true }));
}

/* ══════════════════════════════════════════════════════════════════════════════
   EXTRACT TAG TO COMMENTED LINE  (Ctrl+Shift+/)
══════════════════════════════════════════════════════════════════════════════ */

function extractTagToComment() {
    const cm = getActiveCodeMirror();
    if (cm) { extractTagCodeMirror(cm); return; }
    const ta = getActiveTextarea();
    if (ta) { extractTagTextarea(ta); }
}

function extractTagCodeMirror(cmRoot) {
    const { prefixSp } = computePrefix();
    const info = cmGetCursorLine(cmRoot);
    if (!info) return;
    const { view, line, col } = info;
    const found = findTagAtCol(line.text, col);
    if (!found) return;
    const { tagStr, tagIndex, tags, commentPrefix } = found;
    const remaining = tags.filter((_, i) => i !== tagIndex).map(t => t.trimmed).filter(Boolean);
    const newLine   = commentPrefix + rebuildLine(remaining);
    const commented = prefixSp + tagStr;
    view.dispatch({
        changes: [
            { from: line.from, to: line.to, insert: newLine },
            { from: line.from + newLine.length, to: line.from + newLine.length, insert: "\n" + commented }
        ],
        selection: { anchor: line.from + newLine.length + 1 + commented.length },
        userEvent: "input"
    });
}

function extractTagTextarea(ta) {
    const { prefixSp } = computePrefix();
    const { ls, end, line, col } = taGetCursorLine(ta);
    const found = findTagAtCol(line, col);
    if (!found) return;
    const { tagStr, tagIndex, tags, commentPrefix } = found;
    const remaining = tags.filter((_, i) => i !== tagIndex).map(t => t.trimmed).filter(Boolean);
    const newLine   = commentPrefix + rebuildLine(remaining);
    const commented = prefixSp + tagStr;
    const newText   = newLine + "\n" + commented;
    const newCursor = newLine.length + 1 + commented.length;
    taReplaceLine(ta, ls, end, newText, newCursor);
}

/* ══════════════════════════════════════════════════════════════════════════════
   POWER TAG  (Ctrl+ArrowUp / Ctrl+ArrowDown / Ctrl+Backspace)
   PowerUp:  no brackets → wrap with 1.05;  has brackets → value += 0.05
   PowerDn:  no brackets → wrap with 1.0;   has brackets → value -= 0.05
   Strip:    remove brackets + colon + number
══════════════════════════════════════════════════════════════════════════════ */

function powerTagUp()    { applyPowerTag(+0.05, 1.05); }
function powerTagDown()  { applyPowerTag(-0.05, 1.0);  }
function powerTagStrip() { applyPowerTag(null,  null);  }

function applyPowerTag(delta, initValue) {
    const e = getEditorForShortcut();
    if (!e) return;
    if (e.type === "cm") powerTagCodeMirror(e.ref, delta, initValue);
    else                 powerTagTextarea(e.ref, delta, initValue);
}

function transformPowerTag(tagStr, delta, initValue) {
    if (delta === null) {
        const p = parsePowered(tagStr);
        if (!p) return null;
        return p.inner;
    }
    const p = parsePowered(tagStr);
    if (p) {
        const newVal = Math.max(0, Math.round((p.value + delta) * 100) / 100);
        return makePowered(p.inner, newVal);
    }
    return makePowered(tagStr, initValue);
}

function powerTagCodeMirror(cmRoot, delta, initValue) {
    const info = cmGetCursorLine(cmRoot);
    if (!info) return;
    const { view, line, col } = info;
    const found = findTagAtCol(line.text, col);
    if (!found) return;
    const { tagStr, tagIndex, tags, commentPrefix } = found;
    const newTagStr = transformPowerTag(tagStr, delta, initValue);
    if (newTagStr === null) return;
    const newTags = tags.map((t, i) => i === tagIndex ? newTagStr : t.trimmed);
    const newLine = commentPrefix + rebuildLine(newTags);
    cmReplaceLine(view, line, newLine, col);
}

function powerTagTextarea(ta, delta, initValue) {
    const { ls, end, line, col } = taGetCursorLine(ta);
    const found = findTagAtCol(line, col);
    if (!found) return;
    const { tagStr, tagIndex, tags, commentPrefix } = found;
    const newTagStr = transformPowerTag(tagStr, delta, initValue);
    if (newTagStr === null) return;
    const newTags = tags.map((t, i) => i === tagIndex ? newTagStr : t.trimmed);
    const newLine = commentPrefix + rebuildLine(newTags);
    taReplaceLine(ta, ls, end, newLine, col);
}

/* ══════════════════════════════════════════════════════════════════════════════
   MOVE TAG  (Ctrl+Alt+ArrowRight / Ctrl+Alt+ArrowLeft)
══════════════════════════════════════════════════════════════════════════════ */

function moveTagRight() { applyMoveTag(+1); }
function moveTagLeft()  { applyMoveTag(-1); }

function applyMoveTag(dir) {
    const cm = getActiveCodeMirror();
    if (cm) { moveTagCodeMirror(cm, dir); return; }
    const ta = getActiveTextarea();
    if (ta) { moveTagTextarea(ta, dir); }
}

function doMoveTag(line, col, dir) {
    const { commentPrefix, rest } = stripLineComment(line);
    const offset      = commentPrefix.length;
    const adjustedCol = Math.max(0, col - offset);
    const tags        = parseTagsInLine(rest);
    const idx         = tagIndexAtCol(tags, adjustedCol);
    if (idx < 0) return null;
    const newIdx = idx + dir;
    if (newIdx < 0 || newIdx >= tags.length) return null;

    // cursor offset within the current tag
    const tagRawStart   = tags[idx].start;
    const tagTrimOffset = tags[idx].raw.indexOf(tags[idx].trimmed);
    const cursorInTag   = Math.max(0, adjustedCol - tagRawStart - tagTrimOffset);

    // swap tags
    const strs = tags.map(t => t.trimmed);
    [strs[idx], strs[newIdx]] = [strs[newIdx], strs[idx]];
    const newRest = rebuildLine(strs);
    const newLine = commentPrefix + newRest;

    // find new cursor: newIdx is where the moved tag now sits
    let newTagStart = 0;
    for (let i = 0; i < newIdx; i++) {
        newTagStart += strs[i].length + 2; // ", "
    }
    const newCursor = offset + newTagStart + Math.min(cursorInTag, strs[newIdx].length);

    return { newLine, newCursor };
}

function moveTagCodeMirror(cmRoot, dir) {
    const info = cmGetCursorLine(cmRoot);
    if (!info) return;
    const { view, line, col } = info;
    const result = doMoveTag(line.text, col, dir);
    if (result === null) return;
    cmReplaceLine(view, line, result.newLine, result.newCursor);
}

function moveTagTextarea(ta, dir) {
    const { ls, end, line, col } = taGetCursorLine(ta);
    const result = doMoveTag(line, col, dir);
    if (result === null) return;
    taReplaceLine(ta, ls, end, result.newLine, result.newCursor);
}

/* ══════════════════════════════════════════════════════════════════════════════
   EXTENSION REGISTRATION
══════════════════════════════════════════════════════════════════════════════ */

app.registerExtension({
    name: "Keybinding Extra",

    commands: [
        { id: CMD_ID, label: "Toggle Line Comment", function: () => runToggleOnFocusedEditor() }
    ],

    setup() {
        console.log("[Keybinding Extra] Extension loaded.");
        registerPrefixSetting();
        trackFocus();

        const isMac = () => navigator.platform.toUpperCase().includes("MAC");
        const mod   = (e) => isMac() ? e.metaKey : e.ctrlKey;

        // Ctrl+/  — toggle comment
        window.addEventListener("keydown", (e) => {
            if (!isToggleEnabled()) return;
            if (!mod(e) || e.shiftKey || e.altKey) return;
            if (e.key === "/" || e.code === "Slash") {
                e.preventDefault(); e.stopPropagation();
                runToggleOnFocusedEditor();
            }
        }, true);

        // Ctrl+Shift+L  — delete line
        window.addEventListener("keydown", (e) => {
            if (!isDeleteLineEnabled()) return;
            if (!mod(e) || !e.shiftKey || e.altKey) return;
            if (e.code === "KeyL") {
                e.preventDefault(); e.stopPropagation();
                deleteCurrentLine();
            }
        }, true);

        // Ctrl+Shift+/  — extract tag to comment
        window.addEventListener("keydown", (e) => {
            if (!isExtractWordEnabled()) return;
            if (!mod(e) || !e.shiftKey || e.altKey) return;
            if (e.key === "/" || e.code === "Slash") {
                e.preventDefault(); e.stopPropagation();
                extractTagToComment();
            }
        }, true);

        // Ctrl+ArrowUp  — power tag up
        window.addEventListener("keydown", (e) => {
            if (!isPowerTagEnabled()) return;
            if (!mod(e) || e.shiftKey || e.altKey) return;
            if (e.code === "ArrowUp") {
                e.preventDefault(); e.stopPropagation();
                powerTagUp();
            }
        }, true);

        // Ctrl+ArrowDown  — power tag down
        window.addEventListener("keydown", (e) => {
            if (!isPowerTagEnabled()) return;
            if (!mod(e) || e.shiftKey || e.altKey) return;
            if (e.code === "ArrowDown") {
                e.preventDefault(); e.stopPropagation();
                powerTagDown();
            }
        }, true);

        // Ctrl+Backspace  — strip power from tag
        window.addEventListener("keydown", (e) => {
            if (!isPowerTagEnabled()) return;
            if (!mod(e) || e.shiftKey || e.altKey) return;
            if (e.code === "Backspace") {
                e.preventDefault(); e.stopPropagation();
                powerTagStrip();
            }
        }, true);

        // Ctrl+Alt+ArrowRight  — move tag right
        window.addEventListener("keydown", (e) => {
            if (!isMoveTagEnabled()) return;
            if (!mod(e) || !e.altKey || e.shiftKey) return;
            if (e.code === "ArrowRight") {
                e.preventDefault(); e.stopPropagation();
                moveTagRight();
            }
        }, true);

        // Ctrl+Alt+ArrowLeft  — move tag left
        window.addEventListener("keydown", (e) => {
            if (!isMoveTagEnabled()) return;
            if (!mod(e) || !e.altKey || e.shiftKey) return;
            if (e.code === "ArrowLeft") {
                e.preventDefault(); e.stopPropagation();
                moveTagLeft();
            }
        }, true);
    }
});