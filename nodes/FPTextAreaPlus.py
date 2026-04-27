from comfy_api.latest import ComfyExtension, io


class FPTextAreaPlus(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="FPTextAreaPlus",
            display_name="FP Text Area Plus",
            category="AK/Folded Prompts",
            inputs=[
                io.String.Input(
                    "text",
                    default="",
                    multiline=True,
                ),
                io.String.Input(
                    "before_text",
                    default="",
                    multiline=True,
                    force_input=True,
                    optional=True,
                ),
                io.String.Input(
                    "after_text",
                    default="",
                    multiline=True,
                    force_input=True,
                    optional=True,
                ),
            ],
            outputs=[
                io.String.Output(display_name="text"),
            ],
        )

    @classmethod
    def execute(
        cls,
        text: str = "",
        before_text: str = "",
        after_text: str = "",
    ) -> io.NodeOutput:
        parts = [p for p in [before_text or "", text or "", after_text or ""] if p]
        return io.NodeOutput("\n".join(parts))


class FPTextAreaPlusExtension(ComfyExtension):
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [FPTextAreaPlus]


async def comfy_entrypoint() -> FPTextAreaPlusExtension:
    return FPTextAreaPlusExtension()


NODE_CLASS_MAPPINGS = {
    "FPTextAreaPlus": FPTextAreaPlus,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FPTextAreaPlus": "FP Text Area Plus",
}
