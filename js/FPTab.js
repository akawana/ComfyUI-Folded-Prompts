import { app } from "../../scripts/app.js";

const FP_TAB_CLASS = "FPTab";
const FP_SOURCE_CLASS = "FPTabbedTextArea";
const STORE_KEY = "fp_tabbed_text_area";
const OWNER_WIDGET = "owner_id";
const TAB_WIDGET = "tab_name";
const TEXT_WIDGET = "__fp_tab_text__";
const EMPTY_OPT = "—";

// ── graph helpers ─────────────────────────────────────────────────────────────

function getAllSourceNodes() {
    const g = app?.graph;
    const nodes = g?._nodes || g?.nodes || [];
    return nodes.filter(n => n?.comfyClass === FP_SOURCE_CLASS);
}

function getSourceNodeLabel(node) {
    const title = node.title || node.properties?.title || "";
    return title ? `#${node.id}: ${title}` : `#${node.id}`;
}

function getStore(nodeId) {
    const g = app?.graph;
    return g?.extra?.[STORE_KEY]?.[String(nodeId)] || null;
}

function getTabsForSource(sourceId) {
    const store = getStore(sourceId);
    return store?.tab_order || [];
}

function getTabText(sourceId, tabName) {
    const store = getStore(sourceId);
    return store?.texts?.[tabName] ?? "";
}

function findRawId(labelOrId) {
    // value may be stored as raw id string or as label "#id: title"
    if (!labelOrId || labelOrId === EMPTY_OPT) return null;
    const m = String(labelOrId).match(/^#(\d+)/);
    if (m) return m[1];
    return String(labelOrId);
}

// ── widget helpers ────────────────────────────────────────────────────────────

function getWidgetValue(node, name) {
    return node.widgets?.find(w => w.name === name)?.value ?? "";
}

function setWidgetValue(node, name, value) {
    const w = node.widgets?.find(w => w.name === name);
    if (w) w.value = value;
}

function setComboOptions(node, name, options, keepValue) {
    const w = node.widgets?.find(w => w.name === name);
    if (!w) return;
    const prev = keepValue ? w.value : null;
    w.options = w.options || {};
    w.options.values = options;
    // keep previous value if still valid, else first option
    if (prev && options.includes(prev)) {
        w.value = prev;
    } else {
        w.value = options[0] ?? EMPTY_OPT;
    }
}

function collapseWidget(w) {
    if (!w) return;
    w.hidden = true;
    w.computeSize = () => [0, -4];
    if (w.element) w.element.style.cssText = "display:none;height:0;min-height:0;max-height:0;padding:0;margin:0;overflow:hidden;";
    if (w.inputEl) w.inputEl.style.cssText = "display:none;height:0;min-height:0;max-height:0;padding:0;margin:0;overflow:hidden;";
}

// ── core sync ─────────────────────────────────────────────────────────────────

function refreshOwnerList(node) {
    const sources = getAllSourceNodes();
    const options = sources.length
        ? sources.map(n => getSourceNodeLabel(n))
        : [EMPTY_OPT];

    setComboOptions(node, OWNER_WIDGET, options, true);
}

function refreshTabList(node) {
    const ownerLabel = getWidgetValue(node, OWNER_WIDGET);
    const rawId = findRawId(ownerLabel);
    const tabs = rawId ? getTabsForSource(rawId) : [];
    const options = tabs.length ? tabs : [EMPTY_OPT];
    setComboOptions(node, TAB_WIDGET, options, true);
}

function refreshText(node) {
    const ownerLabel = getWidgetValue(node, OWNER_WIDGET);
    const rawId = findRawId(ownerLabel);
    const tabName = getWidgetValue(node, TAB_WIDGET);
    if (!rawId || !tabName || tabName === EMPTY_OPT) {
        setWidgetValue(node, TEXT_WIDGET, "");
        return;
    }
    const text = getTabText(rawId, tabName);
    setWidgetValue(node, TEXT_WIDGET, text);
}

function syncFPTab(node) {
    refreshOwnerList(node);
    refreshTabList(node);
    refreshText(node);
}

function syncAllFPTabs() {
    const g = app?.graph;
    const nodes = g?._nodes || g?.nodes || [];
    for (const node of nodes) {
        if (node?.comfyClass === FP_TAB_CLASS) {
            syncFPTab(node);
        }
    }
}

// ── init node ─────────────────────────────────────────────────────────────────

function initFPTabNode(node) {
    // Hide text widget
    function hideText() {
        const w = node.widgets?.find(w => w.name === TEXT_WIDGET);
        collapseWidget(w);
        // пересчитать размер ноды
        const newSize = node.computeSize();
        node.setSize(newSize);
        node.setDirtyCanvas(true, true);
    }
    hideText();

    const origOnDrawBackground = node.onDrawBackground;
    node.onDrawBackground = function (ctx) {
        origOnDrawBackground?.apply(this, arguments);
        hideText();
    };

    // Catch V3 late widgets
    let attempts = 0;
    const iv = setInterval(() => {
        hideText();
        if (++attempts >= 10) clearInterval(iv);
    }, 100);

    // Patch owner_id widget callback to update tab list when changed
    const ownerW = node.widgets?.find(w => w.name === OWNER_WIDGET);
    if (ownerW) {
        const origCb = ownerW.callback;
        ownerW.callback = function (value) {
            origCb?.call(this, value);
            refreshTabList(node);
            refreshText(node);
        };
    }

    // Patch tab_name widget callback to update text when changed
    const tabW = node.widgets?.find(w => w.name === TAB_WIDGET);
    if (tabW) {
        const origCb = tabW.callback;
        tabW.callback = function (value) {
            origCb?.call(this, value);
            refreshText(node);
        };
    }

    // Initial sync
    queueMicrotask(() => syncFPTab(node));

    // mousemove on node — update on hover
    const origOnMouseMove = node.onMouseMove;
    node.onMouseMove = function (e, pos, canvas) {
        origOnMouseMove?.apply(this, arguments);
        syncFPTab(node);
    };
}

// ── extension ─────────────────────────────────────────────────────────────────

app.registerExtension({
    name: "FP.Tab",

    async nodeCreated(node) {
        if (node?.comfyClass !== FP_TAB_CLASS) return;
        queueMicrotask(() => initFPTabNode(node));
    },

    loadedGraphNode(node) {
        if (node?.comfyClass !== FP_TAB_CLASS) return;
        initFPTabNode(node);
    },

    setup() {
        window.addEventListener("mouseup", () => syncAllFPTabs(), true);

        window.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === "Delete") {
                syncAllFPTabs();
            }
        }, true);
    },
});
