from context.Anchor import Anchor
from context.Axis import Axis
from context.BaseObject import (
    Color,
    I18NDictionary,
    Position,
    DIRTY_FILE_SAVING,
    DIRTY_CANVAS_RENDER,
    DIRTY_UNDO,
    DIRTY_COMPILE,
)
from context.Features import Features
from context.Font import Font
from context.Glyph import Glyph
from context.Guide import Guide
from context.Instance import Instance
from context.Layer import Layer
from context.Master import Master
from context.Names import Names
from context.Node import Node
from context.Shape import Shape, Transform
from context.ai_docs import (
    generate_all_docs,
    generate_class_docs,
    generate_minimal_docs,
)


__all__ = [
    "Font",
    "Axis",
    "Glyph",
    "Master",
    "Instance",
    "Guide",
    "Anchor",
    "Layer",
    "Shape",
    "Transform",
    "Node",
    "Names",
    "Color",
    "Position",
    "I18NDictionary",
    "Features",
    "load",
    "generate_all_docs",
    "generate_class_docs",
    "generate_minimal_docs",
    "DIRTY_FILE_SAVING",
    "DIRTY_CANVAS_RENDER",
    "DIRTY_UNDO",
    "DIRTY_COMPILE",
]


def load(filename):
    """Load a Context format font file.

    Note: This does NOT automatically initialize dirty tracking.
    Call font.initialize_dirty_tracking() explicitly after loading
    if you need change tracking functionality.
    """
    from context.convertors.nfsf import Context
    from context.convertors import Convert

    convertor = Convert(filename)
    font = Context.load(convertor)

    return font
