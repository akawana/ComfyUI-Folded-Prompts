import { app } from "../../scripts/app.js";

const NODE_CLASS = "FPTabbedTextArea";
const STORE_KEY = "fp_tabbed_text_area";
const META_WIDGET = "node_data_json";   // stores mode/active_tab/tab_order — NO texts
const TEXT_WIDGET = "__fp_text__";      // output "text"
const TAB_WIDGET_PFX = "__fp_tab_";        // __fp_tab_0__ .. __fp_tab_8__
const DEFAULT_TABS = "First";
const DEFAULT_MODE = "separate_tabs";
const MAX_TAB_OUTPUTS = 9;

// ── graph.extra storage (UI state: texts + active_tab) ───────────────────────

function getNodeStore(nodeId) {
    const g = app?.graph;
    if (!g) return null;
    if (!g.extra) g.extra = {};
    if (!g.extra[STORE_KEY]) g.extra[STORE_KEY] = {};
    if (!g.extra[STORE_KEY][nodeId]) {
        g.extra[STORE_KEY][nodeId] = { active_tab: null, texts: {}, tab_order: [], mode: DEFAULT_MODE };
    }
    return g.extra[STORE_KEY][nodeId];
}

function saveNodeStore(nodeId, data) {
    const g = app?.graph;
    if (!g) return;
    if (!g.extra) g.extra = {};
    if (!g.extra[STORE_KEY]) g.extra[STORE_KEY] = {};
    g.extra[STORE_KEY][nodeId] = data;
}

// ── tab list from properties ─────────────────────────────────────────────────

function parseTabs(raw) {
    const str = String(raw ?? DEFAULT_TABS);
    const seen = new Set();
    const result = [];
    for (const t of str.split(",")) {
        const name = t.trim();
        if (!name || seen.has(name)) continue;
        seen.add(name);
        result.push(name);
    }
    if (result.length === 0) result.push("First");
    return result;
}

// ── compute combined texts (what Python will receive) ────────────────────────

function computeTextOutput(store, before, after) {
    const mode = store.mode || DEFAULT_MODE;
    const tab_order = store.tab_order || [];
    const texts = store.texts || {};

    const joinBA = (text) => {
        const parts = [];
        if (before) parts.push(before);
        if (text) parts.push(text);
        if (after) parts.push(after);
        return parts.join("\n");
    };

    if (mode === "separate_tabs") {
        const tab_text = texts[store.active_tab] ?? "";
        return joinBA(tab_text);
    } else {
        const joined = tab_order.map(t => texts[t] ?? "").join("\n");
        return joinBA(joined);
    }
}

function computeTabOutput(store, tabIndex, before, after) {
    const tab_order = store.tab_order || [];
    const texts = store.texts || {};
    const mode = store.mode || DEFAULT_MODE;
    if (mode !== "separate_outputs") return "";
    const name = tab_order[tabIndex];
    if (!name) return "";
    const text = texts[name] ?? "";
    const parts = [];
    if (before) parts.push(before);
    if (text) parts.push(text);
    if (after) parts.push(after);
    return parts.join("\n");
}

// ── sync all hidden widgets from store ───────────────────────────────────────

function syncAllWidgets(node) {
    const store = getNodeStore(String(node.id));
    if (!store) return;

    // meta widget: mode + active_tab + tab_order (NO texts)
    const metaW = node.widgets?.find(w => w.name === META_WIDGET);
    if (metaW) {
        metaW.value = JSON.stringify({
            mode: store.mode,
            active_tab: store.active_tab,
            tab_order: store.tab_order,
        });
    }

    // __fp_text__ widget
    const textW = node.widgets?.find(w => w.name === TEXT_WIDGET);
    if (textW) textW.value = computeTextOutput(store, "", "");

    // __fp_tab_N__ widgets
    for (let i = 0; i < MAX_TAB_OUTPUTS; i++) {
        const w = node.widgets?.find(w => w.name === `${TAB_WIDGET_PFX}${i}__`);
        if (w) w.value = computeTabOutput(store, i, "", "");
    }
}



function applyOutputVisibility(node, mode, tabCount) {
    if (!node.outputs) return;

    // output 0 = "text" — always present, never touch
    // outputs 1..N = tab1..tab9 — add/remove as needed

    const currentTabOutputCount = node.outputs.length - 1;
    const wantCount = mode === "separate_outputs" ? Math.min(tabCount, MAX_TAB_OUTPUTS) : 0;

    if (currentTabOutputCount === wantCount) {
        node.setDirtyCanvas(true, true);
        return;
    }

    // remove extras from the end
    for (let i = currentTabOutputCount - 1; i >= wantCount; i--) {
        const outIdx = i + 1;
        const out = node.outputs[outIdx];
        if (out?.links?.length) {
            [...out.links].forEach(linkId => {
                try { app.graph.removeLink(linkId); } catch (_) { }
            });
        }
        node.removeOutput(outIdx);
    }

    // add missing
    for (let i = currentTabOutputCount; i < wantCount; i++) {
        node.addOutput(`tab${i + 1}`, "STRING");
    }

    node.setDirtyCanvas(true, true);
}

// ── ensure hidden data widgets exist ─────────────────────────────────────────

function collapseWidget(w) {
    if (!w) return;
    w.hidden = true;
    w.computeSize = () => [0, -4];
    w.serializeValue = async () => w.value;
    if (w.element) {
        w.element.style.cssText = "display:none;height:0;min-height:0;max-height:0;padding:0;margin:0;overflow:hidden;";
    }
    if (w.inputEl) {
        w.inputEl.style.cssText = "display:none;height:0;min-height:0;max-height:0;padding:0;margin:0;overflow:hidden;";
    }
}

function getInternalWidgetNames() {
    return [
        META_WIDGET,
        TEXT_WIDGET,
        ...Array.from({ length: MAX_TAB_OUTPUTS }, (_, i) => `${TAB_WIDGET_PFX}${i}__`),
    ];
}

function ensureHiddenWidgets(node) {
    const hideAll = () => {
        for (const name of getInternalWidgetNames()) {
            const w = node.widgets?.find(w => w.name === name);
            collapseWidget(w);
        }
    };

    hideAll();

    // V3 may create widgets late — patch both draw hooks and use a short interval
    const origOnDrawBackground = node.onDrawBackground;
    node.onDrawBackground = function (ctx) {
        origOnDrawBackground?.apply(this, arguments);
        hideAll();
    };

    const origOnDrawForeground = node.onDrawForeground;
    node.onDrawForeground = function (ctx) {
        origOnDrawForeground?.apply(this, arguments);
        hideAll();
    };

    // One-time interval to catch V3 widgets that appear after first render
    let attempts = 0;
    const iv = setInterval(() => {
        hideAll();
        attempts++;
        if (attempts >= 10) clearInterval(iv);
    }, 100);
}

// ── remove existing DOM widget ───────────────────────────────────────────────

function removeTabbedWidget(node) {
    if (!node.widgets) return;
    const idx = node.widgets.findIndex(w => w.name === "__fp_tabs__");
    if (idx === -1) return;
    const w = node.widgets[idx];
    if (w.element && w.element.parentNode) {
        w.element.parentNode.removeChild(w.element);
    }
    node.widgets.splice(idx, 1);
}

// ── build the DOM widget ─────────────────────────────────────────────────────

function buildTabbedWidget(node) {
    const nodeId = String(node.id);
    const store = getNodeStore(nodeId);
    const tabs = parseTabs(node.properties?.tabs ?? DEFAULT_TABS);
    const mode = store.mode || DEFAULT_MODE;

    if (!store.active_tab || !tabs.includes(store.active_tab)) {
        store.active_tab = tabs[0];
    }

    const newTexts = {};
    for (const t of tabs) {
        newTexts[t] = store.texts[t] ?? "";
    }
    store.texts = newTexts;
    store.tab_order = tabs;
    saveNodeStore(nodeId, store);
    syncAllWidgets(node);

    applyOutputVisibility(node, mode, tabs.length);

    // If widget already exists, just rebuild tabs in-place
    const existing = node.widgets?.find(w => w.name === "__fp_tabs__");
    if (existing && existing.__fp_tabBar && existing.__fp_textarea) {
        _populateTabs(existing.__fp_tabBar, existing.__fp_textarea, tabs, store, nodeId, node);
        return;
    }

    // First time — create DOM
    removeTabbedWidget(node);

    const container = document.createElement("div");
    container.style.cssText = "display:flex;flex-direction:column;width:100%;height:100%;gap:0;background:rgba(0,0,0,0.25);border-radius:8px;padding:6px;box-sizing:border-box;";

    const tabBar = document.createElement("div");
    tabBar.style.cssText = "display:flex;gap:3px;flex-wrap:wrap;padding:4px 4px 6px 4px;background:rgba(0,0,0,0.15);border-radius:6px 6px 0 0;margin:-6px -6px 4px -6px;width:calc(100% + 12px);box-sizing:border-box;";

    const textarea = document.createElement("textarea");
    textarea.style.cssText = [
        "width:100%;",
        "min-height:60px;",
        "flex:1;",
        "resize:none;",
        "box-sizing:border-box;",
        "padding:8px;",
        "border-radius:8px;",
        "border:1px solid rgba(255,255,255,0.14);",
        "background:rgba(0,0,0,0.3);",
        "color:inherit;",
        "font-family:inherit;",
        "font-size:12px;",
        "outline:none;",
    ].join("");

    textarea.addEventListener("input", () => {
        store.texts[store.active_tab] = textarea.value;
        saveNodeStore(nodeId, store);
        syncAllWidgets(node);
    });

    textarea.addEventListener("keydown", (e) => e.stopPropagation());
    textarea.addEventListener("keyup", (e) => e.stopPropagation());
    textarea.addEventListener("keypress", (e) => e.stopPropagation());

    container.appendChild(tabBar);
    container.appendChild(textarea);

    _populateTabs(tabBar, textarea, tabs, store, nodeId, node);

    const domWidget = node.addDOMWidget("__fp_tabs__", "div", container, {
        getValue() { return store.texts[store.active_tab] ?? ""; },
        setValue(v) {
            store.texts[store.active_tab] = String(v ?? "");
            textarea.value = store.texts[store.active_tab];
            saveNodeStore(nodeId, store);
            syncAllWidgets(node);
        },
    });

    if (domWidget) {
        domWidget.__fp_tabBar = tabBar;
        domWidget.__fp_textarea = textarea;
    }
}

function _populateTabs(tabBar, textarea, tabs, store, nodeId, node) {
    tabBar.innerHTML = "";
    const tabBtns = {};

    function setActive(name) {
        store.active_tab = name;
        textarea.value = store.texts[name] ?? "";

        for (const [n, btn] of Object.entries(tabBtns)) {
            const isActive = n === name;
            btn.style.background = isActive ? "rgba(255,255,255,0.18)" : "rgba(255,255,255,0.06)";
            btn.style.borderColor = isActive ? "rgba(255,255,255,0.35)" : "rgba(255,255,255,0.14)";
            btn.style.fontWeight = isActive ? "600" : "400";
        }

        saveNodeStore(nodeId, store);
        syncAllWidgets(node);
    }

    for (const name of tabs) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.textContent = name;
        btn.style.cssText = [
            "padding:3px 10px;",
            "border-radius:6px;",
            "border:1px solid rgba(255,255,255,0.14);",
            "background:rgba(255,255,255,0.06);",
            "color:inherit;",
            "cursor:pointer;",
            "font-size:11px;",
            "white-space:nowrap;",
        ].join("");

        btn.addEventListener("mousedown", (e) => {
            e.preventDefault();
            e.stopPropagation();
            setActive(name);
            btn.blur();
        });

        tabBtns[name] = btn;
        tabBar.appendChild(btn);
    }

    setActive(store.active_tab);
}

// ── shared init ───────────────────────────────────────────────────────────────

function initNode(node) {
    if (!node.properties) node.properties = {};
    if (node.properties.tabs === undefined) node.properties.tabs = DEFAULT_TABS;
    if (node.properties.mode === undefined) node.properties.mode = DEFAULT_MODE;

    const store = getNodeStore(String(node.id));
    if (store) {
        store.mode = node.properties.mode || DEFAULT_MODE;
        saveNodeStore(String(node.id), store);
    }

    ensureHiddenWidgets(node);
    buildTabbedWidget(node);

    const origOnPropertyChanged = node.onPropertyChanged;
    node.onPropertyChanged = function (name, value) {
        origOnPropertyChanged?.apply(this, arguments);
        if (name === "tabs") {
            buildTabbedWidget(node);
        }
        if (name === "mode") {
            const s = getNodeStore(String(node.id));
            if (s) {
                s.mode = value || DEFAULT_MODE;
                saveNodeStore(String(node.id), s);
                syncAllWidgets(node);
                const tabs = parseTabs(node.properties?.tabs ?? DEFAULT_TABS);
                applyOutputVisibility(node, s.mode, tabs.length);
            }
        }
    };
}

// ── extension ────────────────────────────────────────────────────────────────

app.registerExtension({
    name: "FP.TabbedTextArea",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_CLASS) return;

        const origOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            origOnNodeCreated?.apply(this, arguments);
            this.addProperty("mode", DEFAULT_MODE, "enum", {
                values: ["separate_tabs", "chained_tabs", "separate_outputs"],
            });
            this.addProperty("tabs", DEFAULT_TABS, "string");
        };
    },

    async nodeCreated(node) {
        if (node?.comfyClass !== NODE_CLASS) return;
        node.__fp_tabs_init_pending = true;
        queueMicrotask(() => {
            if (!node.__fp_tabs_init_pending) return;
            node.__fp_tabs_init_pending = false;
            initNode(node);
        });
    },

    loadedGraphNode(node) {
        if (node?.comfyClass !== NODE_CLASS) return;
        node.__fp_tabs_init_pending = false;
        initNode(node);
    },
});
