from .base import BaseRenderer


class SpacerRenderer(BaseRenderer):

    def render(self):
        size = self.node.props.get("size", 1)
        return [""] * size
