import dataclasses
import re
import typing
import inspect

from graphviz import Digraph

import context
from context import *
from context.BaseObject import I18NDictionary
from context.Features import Features

tocfile = open("docs/_data/navigation.yml", "w")
tocfile.write("default:\n")

# List of all documentation classes in order
DOC_CLASSES = [
    "Font",
    "Axis",
    "Instance",
    "Master",
    "Names",
    "Features",
    "Glyph",
    "Layer",
    "Guide",
    "Shape",
    "Anchor",
    "Node",
]

# Properties to ignore in documentation
IGNORE_PROPERTIES = ["_"]


def generate_navigation(current_class):
    """Generate navigation links for the top of each doc file."""
    nav_parts = []
    for cls_name in DOC_CLASSES:
        if cls_name == current_class:
            # Current page - no link, just bold text
            nav_parts.append(f"**{cls_name}**")
        else:
            # Link to other pages
            nav_parts.append(f"[{cls_name}]({cls_name}.md)")
    return " | ".join(nav_parts)


def maybelink(t):
    # Handle string type annotations
    if isinstance(t, str):
        if t in [
            "Font",
            "Glyph",
            "Layer",
            "Master",
            "Shape",
            "Anchor",
            "Guide",
            "Node",
            "Features",
        ]:
            return "[`%s`](%s.md)" % (t, t)
        return t
    # Handle ForwardRef objects
    if hasattr(t, "__forward_arg__"):
        arg = t.__forward_arg__
        if arg in [
            "Font",
            "Glyph",
            "Layer",
            "Master",
            "Shape",
            "Anchor",
            "Guide",
            "Node",
            "Features",
        ]:
            return "[`%s`](%s.md)" % (arg, arg)
        return arg
    if "context" in str(t) and dataclasses.is_dataclass(t):
        return "[`%s`](%s.md)" % (t.__name__, t.__name__)
    if isinstance(t, typing._GenericAlias):
        if t._name == "Optional":
            return "Optional[%s]" % maybelink(t.__args__[0])
        elif t._name == "List":
            return "[%s]" % maybelink(t.__args__[0])
    if isinstance(t, tuple):
        return "(" + ", ".join([e.__name__ for e in t]) + ")"
    if hasattr(t, "__name__"):
        return t.__name__
    return str(t)


def describe_dataclass(cls):
    # Support both dataclass and BaseObject classes
    is_dataclass = dataclasses.is_dataclass(cls)
    is_baseobject = hasattr(cls, "_field_types") and isinstance(cls._field_types, dict)

    if not is_dataclass and not is_baseobject:
        return

    name = cls.__name__
    f = open("docs/%s.md" % name, "w")
    tocfile.write("  - title: %s\n    url: %s.md\n" % (name, name))

    # Write front matter
    f.write("---\ntitle: %s\n---\n\n" % name)

    # Write navigation header
    f.write(generate_navigation(name))
    f.write("\n\n---\n\n")

    # Write class description
    f.write(cls.__doc__)
    f.write("\n\n")
    if hasattr(cls, "_write_one_line") and cls._write_one_line:
        f.write(
            "* When writing to Context-JSON, this class must be serialized without newlines\n\n"
        )

    # Get fields from either dataclass or BaseObject
    if is_dataclass:
        fields_iter = dataclasses.fields(cls)
    else:
        # For BaseObject classes, write constructor signature
        from collections import namedtuple

        Field = namedtuple(
            "Field", ["name", "type", "default", "default_factory", "metadata"]
        )
        fields_iter = []

        # Generate constructor signature
        if hasattr(cls, "__init__"):
            import inspect

            sig = inspect.signature(cls.__init__)
            params = []
            for param_name, param in sig.parameters.items():
                if param_name in ("self", "_data", "kwargs"):
                    continue
                if param.default == inspect.Parameter.empty:
                    params.append(param_name)
                else:
                    default_repr = (
                        repr(param.default)
                        if param.default != inspect.Parameter.empty
                        else None
                    )
                    if default_repr:
                        params.append(f"{param_name}={default_repr}")
                    else:
                        params.append(param_name)

            if params:
                f.write(f"## Constructor\n\n")
                f.write(f"`{name}({', '.join(params)})`\n\n")

        for field_name, field_info in cls._field_types.items():
            field_type = field_info.get("data_type", str)
            is_required = field_info.get("required", False)
            default_value = dataclasses.MISSING if is_required else None
            fields_iter.append(
                Field(
                    name=field_name,
                    type=field_type,
                    default=default_value,
                    default_factory=dataclasses.MISSING,
                    metadata={},
                )
            )

    for k in fields_iter:
        # Skip properties in ignore list
        if k.name in IGNORE_PROPERTIES:
            continue
        if isinstance(k.type, list):
            stringytype = "[%s]" % ", ".join([maybelink(t) for t in k.type])
        elif isinstance(k.type, tuple):
            stringytype = "(%s)" % ", ".join([maybelink(t) for t in k.type])
        else:
            stringytype = maybelink(k.type)
        if not "`" in stringytype:
            stringytype = "`%s`" % stringytype
        f.write("## %s.%s\n\n" % (name, k.name))
        f.write("* Python type: %s\n\n" % stringytype)
        if "json_type" in k.metadata:
            f.write("* Context-JSON type: `%s`\n\n" % k.metadata["json_type"])
        if (
            k.default is dataclasses.MISSING
            and k.default_factory is dataclasses.MISSING
        ):
            f.write("* **Required field**\n\n")
        if "json_location" in k.metadata:
            f.write(
                "* When writing to Context-JSON, this structure is stored under the separate file `%s`.\n\n"
                % k.metadata["json_location"]
            )

        if "separate_items" in k.metadata:
            f.write(
                "* When writing to Context-JSON, each item in the list must be placed on a separate line.\n\n"
            )
        if "python_only" in k.metadata:
            f.write(
                "* This field only exists as an attribute of the the Python object and should not be written to Context-JSON.\n\n"
            )

        # Try to get docstring from property getter
        if is_baseobject and hasattr(cls, k.name):
            prop = getattr(cls, k.name)
            if isinstance(prop, property) and prop.fget and prop.fget.__doc__:
                docstring = prop.fget.__doc__.strip()
                f.write(f"{docstring}\n\n")

        if "description" in k.metadata:
            f.write(k.metadata["description"])
        if k.type == I18NDictionary:
            f.write(" *Localizable.*")
        f.write("\n")
        if k.default is not dataclasses.MISSING:
            f.write("*If not provided, defaults to* `%s`.\n" % str(k.default))
        f.write("\n\n")

    # Add inherited properties for BaseObject classes
    if is_baseobject:
        f.write("## Inherited Properties\n\n")
        f.write(
            "As a subclass of `BaseObject`, this class also has "
            "these properties:\n\n"
        )
        f.write("### user_data\n\n")
        f.write(
            "* Python type: `dict`\n\n"
            "Optional dictionary for format-specific data. "
            "This is stored as `_` in the Context-JSON serialization. "
            "Use this to store custom metadata that should be preserved "
            "when reading and writing files.\n\n"
        )
        f.write("*If not provided, defaults to* `{}`.\n\n")

    f.close()


describe_dataclass(Font)
describe_dataclass(Axis)
describe_dataclass(Instance)
describe_dataclass(Master)
describe_dataclass(Names)
describe_dataclass(Features)
describe_dataclass(Glyph)
describe_dataclass(Layer)
describe_dataclass(Guide)
describe_dataclass(Shape)
describe_dataclass(Anchor)
describe_dataclass(Node)


dot = Digraph(comment="Context Format", format="svg")
dot.attr(rankdir="LR")
dot.attr(overlap="false")
donetypes = {}


def add_type_node(cls):
    def chktype(t, port):
        if "context" in str(t) and dataclasses.is_dataclass(t):
            add_type_node(t)
            dot.edge(cls.__name__ + ":" + port, t.__name__)
        if isinstance(t, tuple):
            return "(" + ", ".join([e.__name__ for e in t]) + ")"
        return t.__name__

    if cls in donetypes:
        return
    if not dataclasses.is_dataclass(cls):
        return
    label = (
        """<<TABLE>
    <tr><td colspan="2" border="0"><b>%s</b></td></tr>
    """
        % cls.__name__
    )
    for k in dataclasses.fields(cls):
        if k.name == "_" or "python_only" in k.metadata:
            continue
        if isinstance(k.type, list):
            stringytype = "[%s]" % ", ".join([chktype(t, k.name) for t in k.type])
        elif isinstance(k.type, tuple):
            stringytype = "(%s)" % ", ".join([chktype(t, k.name) for t in k.type])
        else:
            stringytype = chktype(k.type, k.name)
        name = k.name
        if (
            k.default is dataclasses.MISSING
            and k.default_factory is dataclasses.MISSING
        ):
            name = "<b>%s</b>" % name
        label = label + '<tr><td>%s</td><td port="%s"><i>%s</i></td></tr>' % (
            name,
            k.name,
            stringytype,
        )

    label = label + "</TABLE>>"
    dot.node(
        cls.__name__,
        label,
        shape="none",
        fontname="Avenir",
        href="%s.md" % cls.__name__,
    )
    donetypes[cls] = True


add_type_node(Font)
add_type_node(Glyph)
dot.edge("Font:glyphs", "Glyph")
output = re.sub(r"(?s)^.*<svg", "<svg", dot.pipe().decode("utf-8"))
out = open("docs/index.md", "w")
out.write(
    """---
title: Context Format
toc: false
---


"""
)
out.write(output + "\n")
