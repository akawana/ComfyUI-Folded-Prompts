import hashlib

from comfy_execution.graph import ExecutionBlocker
from comfy_api.latest import ComfyExtension, io

MAX_TAB_OUTPUTS = 9


class FPTabbedTextArea(io.ComfyNode):

    _prev_tab_hashes: dict = {}  # { node_unique_id: { tab_index: hash } }
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
                *[
                    io.String.Input(
                        f"__fp_tab_{i}__",
                        default="",
                        multiline=False,
                        tooltip=f"Internal: tab{i+1} text. Managed by JS.",
                    )
                    for i in range(MAX_TAB_OUTPUTS)
                ],
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
                *[
                    io.String.Output(display_name=f"tab{i+1}")
                    for i in range(MAX_TAB_OUTPUTS)
                ],
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, __fp_text__: str = "", **kwargs) -> str:
        parts = [__fp_text__]
        for i in range(MAX_TAB_OUTPUTS):
            parts.append(kwargs.get(f"__fp_tab_{i}__", "") or "")
        return hashlib.sha256("\n".join(parts).encode()).hexdigest()

    @classmethod
    def execute(
        cls,
        node_data_json: str = "",
        __fp_text__: str = "",
        before_text: str = "",
        after_text: str = "",
        **kwargs,
    ) -> io.NodeOutput:
        unique_id = str(cls.hidden.unique_id) if cls.hidden else ""
        # print(f"[FPTabbedTextArea] execute: __fp_text__={__fp_text__!r:.40}")
        before = before_text or ""
        after  = after_text or ""

        main_text = "\n".join(p for p in [before, __fp_text__, after] if p)

        prev = cls._prev_tab_hashes.get(unique_id, {})
        curr = {}

        tab_outputs = []
        for i in range(MAX_TAB_OUTPUTS):
            raw = kwargs.get(f"__fp_tab_{i}__", "") or ""
            tab_hash = hashlib.md5(raw.encode()).hexdigest()
            curr[i] = tab_hash

            if raw:
                if tab_hash == prev.get(i):
                    # print(f"[FPTabbedTextArea] tab{i+1} unchanged → ExecutionBlocker")
                    tab_outputs.append(ExecutionBlocker(None))
                else:
                    # print(f"[FPTabbedTextArea] tab{i+1} changed → passing value")
                    tab_outputs.append("\n".join(p for p in [before, raw, after] if p))
            else:
                tab_outputs.append(ExecutionBlocker(None))

        cls._prev_tab_hashes[unique_id] = curr

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
