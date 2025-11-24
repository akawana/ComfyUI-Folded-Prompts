import { app } from "../../scripts/app.js";

const CMD_ID = "keybinding_extra.toggle";
const SETTING_ID = "keybinding_extra.comment_prefix";
const FALLBACK_KEY = "keybinding_extra.comment_prefix";

const ENABLE_ID = "keybinding_extra.enabled";
const ENABLE_FALLBACK_KEY = "keybinding_extra.enabled";

app.registerExtension({
    name: "Keybinding Extra",

    commands: [
        {
            id: CMD_ID,
            label: "Toggle Line Comment",
            function: () => runToggleOnFocusedEditor()
        }
    ],

    setup() {
        registerPrefixSetting();

        window.addEventListener(
            "keydown",
            (e) => {
                if (!isToggleEnabled()) return;

                const isMac = navigator.platform.toUpperCase().includes("MAC");
                const pressed = isMac ? e.metaKey : e.ctrlKey;
                if (!pressed) return;

                if (e.key !== "/" && e.code !== "Slash") return;

                e.preventDefault();
                e.stopPropagation();

                runToggleOnFocusedEditor();
            },
            true
        );

        console.log("[Keybinding Extra] Loaded.");
    }
});

/* ------------------------------ SETTINGS ------------------------------ */

function registerPrefixSetting() {
    const settingsApi = app.ui?.settings;
    const defaultPrefix = "//";

    if (settingsApi && typeof settingsApi.addSetting === "function") {

        settingsApi.addSetting({
            id: SETTING_ID,
            category: ["Keybinding Extra", "Comment Settings", "B"],
            name: "(Ctrl+/) Line comment prefix:",
            type: "text",
            defaultValue: defaultPrefix,
            placeholder: "// or # or --",
            onChange: (v) => {
                const cleaned = sanitizePrefix(v);
                try { localStorage.setItem(FALLBACK_KEY, cleaned); } catch {}
            }
        });
        settingsApi.addSetting({
            id: ENABLE_ID,
            category: ["Keybinding Extra", "Comment Settings", "A"],
            name: "Enable line comment:",
            type: "boolean",
            defaultValue: true,
            onChange: (value) => {
                setToggleEnabled(value);
            }
        });

    } else {
        if (!getCommentPrefix()) {
            try { localStorage.setItem(FALLBACK_KEY, defaultPrefix); } catch {}
        }
        if (localStorage.getItem(ENABLE_FALLBACK_KEY) == null) {
            try { localStorage.setItem(ENABLE_FALLBACK_KEY, "true"); } catch {}
        }
    }
}

function sanitizePrefix(v) {
    if (v == null) return "//";
    const s = String(v).trim();
    return s.length ? s : "//";
}

function getCommentPrefix() {
    const settingsApi = app.ui?.settings;
    let v = null;

    if (settingsApi && typeof settingsApi.getSettingValue === "function") {
        try { v = settingsApi.getSettingValue(SETTING_ID); } catch { v = null; }
    }

    if (!v) {
        try { v = localStorage.getItem(FALLBACK_KEY); } catch {}
    }

    return sanitizePrefix(v);
}

function isToggleEnabled() {
    const settingsApi = app.ui?.settings;

    if (settingsApi && typeof settingsApi.getSettingValue === "function") {
        try {
            const val = settingsApi.getSettingValue(ENABLE_ID);
            if (val !== undefined && val !== null) {
                return !!val;
            }
        } catch (e) {
        }
    }
    try {
        const v = localStorage.getItem(ENABLE_FALLBACK_KEY);
        return String(v) !== "false";
    } catch {
        return true;
    }
}

function setToggleEnabled(v) {
    const str = v ? "true" : "false";
    try { localStorage.setItem(ENABLE_FALLBACK_KEY, str); } catch {}
}


/* ------------------------- ACTIVE EDITOR DETECTION ------------------------ */

function runToggleOnFocusedEditor() {
    const ace = getActiveAceEditor();
    if (ace) {
        toggleAceComments(ace);
        return;
    }

    const cm = getActiveCodeMirror();
    if (cm) {
        toggleCodeMirrorComments(cm);
        return;
    }

    const ta = getActiveTextarea();
    if (ta) {
        toggleTextareaComments(ta);
        return;
    }
}

function getActiveAceEditor() {
    const active = document.activeElement;
    let el = active;

    while (el && el !== document.body) {
        if (el.classList && el.classList.contains("ace_editor")) {
            return el.env && el.env.editor ? el.env.editor : null;
        }
        el = el.parentElement;
    }

    const editors = document.querySelectorAll(".ace_editor");
    for (const ed of editors) {
        if (ed.env && ed.env.editor) return ed.env.editor;
    }
    return null;
}

function getActiveCodeMirror() {
    const active = document.activeElement;
    let el = active;

    while (el && el !== document.body) {
        if (el.classList && el.classList.contains("cm-editor")) {
            return el.cmView || el;
        }
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

/* ------------------------------ TOGGLE HELPERS ------------------------------ */

function computePrefix() {
    const prefix = getCommentPrefix();
    const prefixSp = prefix + " ";
    return { prefix, prefixSp };
}

/* ------------------------------ ACE ------------------------------ */

function toggleAceComments(editor) {
    const session = editor.session;
    const range = editor.getSelectionRange();
    const { prefix, prefixSp } = computePrefix();

    let startRow = range.start.row;
    let endRow = range.end.row;

    if (range.end.column === 0 && endRow > startRow) endRow -= 1;

    for (let row = startRow; row <= endRow; row++) {
        const line = session.getLine(row);
        const trimmed = line.trimStart();
        const indent = line.length - trimmed.length;

        if (trimmed.startsWith(prefixSp)) {
            const idx = line.indexOf(prefixSp, indent);
            if (idx !== -1) {
                session.replace(
                    { start: { row, column: idx }, end: { row, column: idx + prefixSp.length } },
                    ""
                );
            }
        } else if (trimmed.startsWith(prefix)) {
            const idx = line.indexOf(prefix, indent);
            if (idx !== -1) {
                session.replace(
                    { start: { row, column: idx }, end: { row, column: idx + prefix.length } },
                    ""
                );
            }
        } else {
            session.insert({ row, column: indent }, prefixSp);
        }
    }
}

/* -------------------------- CODEMIRROR --------------------------- */

function toggleCodeMirrorComments(cmRoot) {
    const view = cmRoot.cmView || cmRoot.view || cmRoot;
    if (!view || !view.state || !view.dispatch) return;

    const { prefix, prefixSp } = computePrefix();

    const state = view.state;
    const sel = state.selection.main;

    const doc = state.doc;
    let fromLine = doc.lineAt(sel.from).number;
    let toLine = doc.lineAt(sel.to).number;

    if (sel.to > sel.from && doc.lineAt(sel.to).from === sel.to) {
        toLine -= 1;
    }

    const changes = [];

    for (let n = fromLine; n <= toLine; n++) {
        const line = doc.line(n);
        const text = line.text;
        const trimmed = text.trimStart();
        const indent = text.length - trimmed.length;

        if (trimmed.startsWith(prefixSp)) {
            const idx = text.indexOf(prefixSp, indent);
            if (idx !== -1) {
                changes.push({
                    from: line.from + idx,
                    to: line.from + idx + prefixSp.length,
                    insert: ""
                });
            }
        } else if (trimmed.startsWith(prefix)) {
            const idx = text.indexOf(prefix, indent);
            if (idx !== -1) {
                changes.push({
                    from: line.from + idx,
                    to: line.from + idx + prefix.length,
                    insert: ""
                });
            }
        } else {
            changes.push({
                from: line.from + indent,
                to: line.from + indent,
                insert: prefixSp
            });
        }
    }

    if (changes.length) view.dispatch({ changes });
}

/* ----------------------------- TEXTAREA ---------------------------- */

function toggleTextareaComments(ta) {
    const { prefix, prefixSp } = computePrefix();

    const value = ta.value;
    const start = ta.selectionStart;
    const end = ta.selectionEnd;

    const lines = value.split("\n");

    let pos = 0;
    let startLine = 0;
    let endLine = lines.length - 1;

    for (let i = 0; i < lines.length; i++) {
        const lineLen = lines[i].length + 1;
        if (start >= pos && start < pos + lineLen) startLine = i;
        if (end >= pos && end < pos + lineLen) { endLine = i; break; }
        pos += lineLen;
    }

    for (let i = startLine; i <= endLine; i++) {
        const line = lines[i];
        const trimmed = line.trimStart();
        const indent = line.length - trimmed.length;

        if (trimmed.startsWith(prefixSp)) {
            const idx = line.indexOf(prefixSp, indent);
            if (idx !== -1) {
                lines[i] = line.slice(0, idx) + line.slice(idx + prefixSp.length);
            }
        } else if (trimmed.startsWith(prefix)) {
            const idx = line.indexOf(prefix, indent);
            if (idx !== -1) {
                lines[i] = line.slice(0, idx) + line.slice(idx + prefix.length);
            }
        } else {
            lines[i] = line.slice(0, indent) + prefixSp + line.slice(indent);
        }
    }

    ta.value = lines.join("\n");
    ta.selectionStart = start;
    ta.selectionEnd = end;
    ta.dispatchEvent(new Event("input", { bubbles: true }));
}
