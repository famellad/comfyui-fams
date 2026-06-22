from .nodes.generators import *
from .nodes.img_proc import *
from .nodes.viewers import *
from .nodes.sampling import *

# This maps the internal class to a unique identifier for ComfyUI
NODE_CLASS_MAPPINGS = {
    "BooruTests": BooruTests,
    "MagickSelectiveBlur": MagickSelectiveBlur,
    "SimpleDepthOfField": SimpleDepthOfField,
    "QueuePreviewer": QueuePreviewer,
    "KSamplerComplex": KSamplerComplex,
}

# This dictates what the node is actually named when you see it in the UI
NODE_DISPLAY_NAME_MAPPINGS = {
    "BooruTests": "Booru Test List",
    "MagickSelectiveBlur": "Selective Blur",
    "SimpleDepthOfField": "Simple Depth of Field",
    "QueuePreviewer": "Queue Previewer",
    "KSamplerComplex": "KSampler (Complex)",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]