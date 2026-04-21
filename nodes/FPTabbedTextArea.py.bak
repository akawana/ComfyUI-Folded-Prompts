import json

from comfy_api.latest import ComfyExtension, io


class FPTabbedTextArea(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="FPTabbedTextArea",
            display_name="FP Tabbed Text Area",
            category="FP/text",
            description=(
                "A text node with multiple tabs. Each tab has its own text area. "
                "The active tab's text is combined with before_text and after_text "
                "and sent to the output. "
                "Configure tabs via node Properties → tabs (comma-separated names)."
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
                    tooltip="Text prepended to the active tab text.",
                ),
                io.String.Input(
                    "after_text",
                    default="",
                    multiline=True,
                    force_input=True,
                    optional=True,
                    tooltip="Text appended to the active tab text.",
                ),
            ],
            outputs=[
                io.String.Output(display_name="text"),
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

        active_tab = str(data.get("active_tab", ""))
        texts = data.get("texts", {})

        tab_text = ""
        if active_tab and isinstance(texts, dict):
            tab_text = str(texts.get(active_tab, ""))

        result = (before_text or "") + tab_text + (after_text or "")

        return io.NodeOutput(result)


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