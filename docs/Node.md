---
title: Node
---

[Font](Font.md) | [Axis](Axis.md) | [Instance](Instance.md) | [Master](Master.md) | [Names](Names.md) | [Features](Features.md) | [Glyph](Glyph.md) | [Layer](Layer.md) | [Guide](Guide.md) | [Shape](Shape.md) | [Anchor](Anchor.md) | **Node**

---


    A node in a glyph outline path.
    

## Constructor

`Node(x=0, y=0, type='c')`

### Node.x

The x coordinate of the node.

* Python type: `int`

* **Required field**




### Node.y

The y coordinate of the node.

* Python type: `int`

* **Required field**




### Node.type

The node type (c/l/q/o with optional 's' suffix for smooth).

* Python type: `str`

* **Required field**

* Allowed values: `o`, `os`, `c`, `cs`, `l`, `ls`, `q`, `qs`




## Inherited Properties

As a subclass of `BaseObject`, this class also has these properties:

### user_data

* Python type: `dict`

Optional dictionary for format-specific data. This is stored as `_` in the Context-JSON serialization. Use this to store custom metadata that should be preserved when reading and writing files.

*If not provided, defaults to* `{}`.

