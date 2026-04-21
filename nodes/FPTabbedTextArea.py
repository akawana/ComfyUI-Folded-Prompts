import json

from comfy_api.latest import ComfyExtension, io

MAX_TAB_OUTPUTS = 9


class FPTabbedTextArea(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="FPTabbedTextArea",
            display_name="FP Tabbed Text Area",
            category="FP/text",
            description=(
                "A text node with multiple tabs. "
                "Mode is controlled via node Properties → mode.\n"
                "• Separate Tabs: active tab text → output 'text'\n"
                "• Chained Tabs: all tabs joined with newline → output 'text'\n"
                "• Separate Outputs: each tab → its own output tab1..tab9; "
                "'text' outputs all tabs chained."
            ),
            inputs=[
                io.String.Input(
                    "node_data_json",
                    default="",
                    multiline=False,
                    tooltip="Internal: stores tabs data. Managed by JS.",
                ),
                io.String.Input(
                    "before_text",
                    default="",
                    multiline=True,
                    force_input=True,
                    optional=True,
                    tooltip="Text prepended to the output.",
                ),
                io.String.Input(
                    "after_text",
                    default="",
                    multiline=True,
                    force_input=True,
                    optional=True,
                    tooltip="Text appended to the output.",
                ),
            ],
            outputs=[
                io.String.Output(display_name="text"),
                *[
                    io.String.Output(display_name=f"tab{i+1}")
                    for i in range(MAX_TAB_OUTPUTS)
                ],
            ],
        )

    @classmethod
    def execute(
        cls,
        node_data_json: str,
        before_text: str = "",
        after_text: str = "",
    ) -> io.NodeOutput:
        try:
            data = json.loads(node_data_json or "{}")
        except Exception:
            data = {}

        mode = str(data.get("mode", "separate_tabs"))
        active_tab = str(data.get("active_tab", ""))
        texts = data.get("texts", {})
        tab_order = data.get("tab_order", [])

        if not isinstance(texts, dict):
            texts = {}
        if not isinstance(tab_order, list) or not tab_order:
            tab_order = list(texts.keys())

        before = before_text or ""
        after = after_text or ""

        # ── main "text" output ───────────────────────────────────────────────
        if mode == "separate_tabs":
            tab_text = str(texts.get(active_tab, "")) if active_tab else ""
            main_text = before + "\n" + tab_text + "\n" + after
        else:
            # chained or separate_outputs — join all tabs
            parts = [str(texts.get(t, "")) for t in tab_order if t in texts]
            main_text = before + "\n".join(parts) + after

        # ── per-tab outputs (tab1..tab9) ─────────────────────────────────────
        tab_outputs = []
        for i in range(MAX_TAB_OUTPUTS):
            if i < len(tab_order) and mode == "separate_outputs":
                tab_name = tab_order[i]
                tab_outputs.append(before + "\n" + str(texts.get(tab_name, "")) + "\n" + after)
            else:
                tab_outputs.append("")

        return io.NodeOutput(main_text, *tab_outputs)


class FPTabbedTextAreaExtension(ComfyExtension):
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [FPTabbedTextArea]


async def comfy_entrypoint() -> FPTabbedTextAreaExtension:
    return FPTabbedTextAreaExtension()


NODE_CLASS_MAPPINGS = {
    "FPTabbedTextArea": FPTabbedTextArea,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FPTabbedTextArea": "FP Tabbed Text Area",
}