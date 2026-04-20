import { app } from "../../scripts/app.js";

const NODE_CLASS = "FPTabbedTextArea";
const STORE_KEY = "fp_tabbed_text_area";
const DATA_WIDGET = "node_data_json";
const DEFAULT_TABS = "First";

// ── graph.extra storage ──────────────────────────────────────────────────────

function getNodeStore(nodeId) {
    const g = app?.graph;
    if (!g) return null;
    if (!g.extra) g.extra = {};
    if (!g.extra[STORE_KEY]) g.extra[STORE_KEY] = {};
    if (!g.extra[STORE_KEY][nodeId]) {
        g.extra[STORE_KEY][nodeId] = { active_tab: null, texts: {} };
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

// ── hide the data widget ─────────────────────────────────────────────────────

function hideDataWidget(node) {
    const w = node.widgets?.find(w => w.name === DATA_WIDGET);
    if (!w) return;
    w.type = "hidden";
    w.hidden = true;
    w.computeSize = () => [0, -4];
    if (w.inputEl) {
        w.inputEl.style.cssText = "display:none;height:0;min-height:0;max-height:0;padding:0;margin:0;";
    }
}

// ── sync data widget value ───────────────────────────────────────────────────

function syncWidget(node) {
    const store = getNodeStore(String(node.id));
    if (!store) return;
    const w = node.widgets?.find(w => w.name === DATA_WIDGET);
    if (w) w.value = JSON.stringify(store);
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
    removeTabbedWidget(node);

    const nodeId = String(node.id);
    const store = getNodeStore(nodeId);
    const tabs = parseTabs(node.properties?.tabs ?? DEFAULT_TABS);

    if (!store.active_tab || !tabs.includes(store.active_tab)) {
        store.active_tab = tabs[0];
    }

    const newTexts = {};
    for (const t of tabs) {
        newTexts[t] = store.texts[t] ?? "";
    }
    store.texts = newTexts;
    saveNodeStore(nodeId, store);
    syncWidget(node);

    // ── DOM ──────────────────────────────────────────────────────────────────

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
        syncWidget(node);
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

    textarea.value = store.texts[store.active_tab] ?? "";

    textarea.addEventListener("input", () => {
        store.texts[store.active_tab] = textarea.value;
        saveNodeStore(nodeId, store);
        syncWidget(node);
    });

    textarea.addEventListener("keydown", (e) => e.stopPropagation());
    textarea.addEventListener("keyup", (e) => e.stopPropagation());
    textarea.addEventListener("keypress", (e) => e.stopPropagation());

    container.appendChild(tabBar);
    container.appendChild(textarea);

    setActive(store.active_tab);

    node.addDOMWidget("__fp_tabs__", "div", container, {
        getValue() {
            return store.texts[store.active_tab] ?? "";
        },
        setValue(v) {
            store.texts[store.active_tab] = String(v ?? "");
            textarea.value = store.texts[store.active_tab];
            saveNodeStore(nodeId, store);
            syncWidget(node);
        },
    });
}

// ── shared init ───────────────────────────────────────────────────────────────

function initNode(node) {
    if (!node.properties) node.properties = {};
    if (node.properties.tabs === undefined) node.properties.tabs = DEFAULT_TABS;

    hideDataWidget(node);
    buildTabbedWidget(node);

    const origOnPropertyChanged = node.onPropertyChanged;
    node.onPropertyChanged = function (name, value) {
        origOnPropertyChanged?.apply(this, arguments);
        if (name === "tabs") {
            buildTabbedWidget(node);
        }
    };
}

// ── extension ────────────────────────────────────────────────────────────────

app.registerExtension({
    name: "FP.TabbedTextArea",

    async nodeCreated(node) {
        if (node?.comfyClass !== NODE_CLASS) return;
        // Set a flag — loadedGraphNode will cancel this if it fires first
        node.__fp_tabs_init_pending = true;
        queueMicrotask(() => {
            if (!node.__fp_tabs_init_pending) return;
            node.__fp_tabs_init_pending = false;
            initNode(node);
        });
    },

    loadedGraphNode(node) {
        if (node?.comfyClass !== NODE_CLASS) return;
        // graph.extra is already restored here, so we read correct data
        node.__fp_tabs_init_pending = false;
        initNode(node);
    },
});