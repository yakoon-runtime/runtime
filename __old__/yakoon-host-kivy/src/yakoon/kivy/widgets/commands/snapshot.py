class MessageSnapshot:

    def __init__(self):
        self.nodes = []
        self.text = {}

    def apply_patch(self, patch):

        for op in patch.ops:

            kind = getattr(op, "op", None)

            if kind == "reset":
                self.nodes.clear()
                self.text.clear()

            elif kind == "append_structure":
                self.nodes.extend(op.nodes)

            elif kind == "append_text":

                block = self.text.setdefault(op.block_id, {})
                block.setdefault(op.key, "")
                block[op.key] += op.text
