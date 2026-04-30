from comfy_api.latest import ComfyExtension, io


class FPTab(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="FPTab",
            display_name="FP Tab",
            category="AK/Folded Prompts",
            description=(
                "Reads text from a specific tab of a FP Tabbed Text Area node. "
                "Select the source node and tab from the dropdowns. "
                "JS updates the dropdowns automatically."
            ),
            inputs=[
                io.Combo.Input(
                    "owner_id",
                    options=["—"],
                    default="—",
                    tooltip="Select the FP Tabbed Text Area node to read from.",
                ),
                io.Combo.Input(
                    "tab_name",
                    options=["—"],
                    default="—",
                    tooltip="Select the tab to read from.",
                ),
                io.String.Input(
                    "__fp_tab_text__",
                    default="",
                    multiline=False,
                    tooltip="Internal: tab text. Managed by JS.",
                ),
            ],
            outputs=[
                io.String.Output(display_name="text"),
            ],
        )
    
    @classmethod
    def validate_inputs(cls, owner_id="", tab_name="", **kwargs):
        return True

    @classmethod
    def fingerprint_inputs(cls, __fp_tab_text__: str = "", **kwargs) -> str:
        return __fp_tab_text__ or ""

    @classmethod
    def execute(
        cls,
        owner_id: str = "",
        tab_name: str = "",
        __fp_tab_text__: str = "",
    ) -> io.NodeOutput:
        return io.NodeOutput(__fp_tab_text__ or "")


class FPTabExtension(ComfyExtension):
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [FPTab]


async def comfy_entrypoint() -> FPTabExtension:
    return FPTabExtension()


NODE_CLASS_MAPPINGS = {
    "FPTab": FPTab,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FPTab": "FP Tab",
}
