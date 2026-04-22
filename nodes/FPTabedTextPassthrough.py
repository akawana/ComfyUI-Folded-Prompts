import hashlib

from comfy_api.latest import ComfyExtension, io


class FPTabedTextPassthrough(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="FPTabedTextPassthrough",
            display_name="FP Tabed Text Passthrough",
            category="FP/text",
            description=(
                "Place this node between FP Tabbed Text Area tab outputs and downstream nodes. "
                "It passes the text through unchanged but uses fingerprint_inputs to cache "
                "its output independently — downstream execution is skipped when the text has not changed."
            ),
            inputs=[
                io.String.Input("text", default="", force_input=True),
            ],
            outputs=[
                io.String.Output(display_name="text"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, text: str = "") -> str:
        h = hashlib.sha256((text or "").encode()).hexdigest()
        print(f"[FPTabedTextPassthrough fingerprint_inputs] text={str(text)[:80]!r} => hash={h[:16]}...")
        return h

    @classmethod
    def execute(cls, text: str = "") -> io.NodeOutput:
        print(f"[FPTabedTextPassthrough execute] text={str(text)[:80]!r}")
        return io.NodeOutput(text)


class FPTabedTextPassthroughExtension(ComfyExtension):
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [FPTabedTextPassthrough]


async def comfy_entrypoint() -> FPTabedTextPassthroughExtension:
    return FPTabedTextPassthroughExtension()


NODE_CLASS_MAPPINGS = {
    "FPTabedTextPassthrough": FPTabedTextPassthrough,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FPTabedTextPassthrough": "FP Tabed Text Passthrough",
}
