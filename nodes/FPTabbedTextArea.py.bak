import hashlib

from comfy_api.latest import ComfyExtension, io


class FPTabbedTextArea(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="FPTabbedTextArea",
            display_name="FP Tabbed Text Area",
            category="AK/Folded Prompts",
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
                    tooltip="Internal metadata (mode/active_tab/tab_order). Managed by JS.",
                ),
                io.String.Input(
                    "__fp_text__",
                    default="",
                    multiline=False,
                    tooltip="Internal: combined text output. Managed by JS.",
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
            hidden=[io.Hidden.unique_id],
            outputs=[
                io.String.Output(display_name="text"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, __fp_text__: str = "", **kwargs) -> str:
        return hashlib.sha256((__fp_text__ or "").encode()).hexdigest()

    @classmethod
    def execute(
        cls,
        node_data_json: str = "",
        __fp_text__: str = "",
        before_text: str = "",
        after_text: str = "",
    ) -> io.NodeOutput:
        unique_id = str(cls.hidden.unique_id) if cls.hidden else ""
        before = before_text or ""
        after  = after_text or ""
        main_text = "\n".join(p for p in [before, __fp_text__, after] if p)
        return io.NodeOutput(main_text)


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
