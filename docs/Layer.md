---
title: Layer
---

[Font](Font.md) | [Axis](Axis.md) | [Instance](Instance.md) | [Master](Master.md) | [Names](Names.md) | [Features](Features.md) | [Glyph](Glyph.md) | **Layer** | [Guide](Guide.md) | [Shape](Shape.md) | [Anchor](Anchor.md) | [Node](Node.md)

---

A layer in a glyph with shapes, anchors, and guides.

## Constructor

`Layer(width=0, height=0, vertWidth=None, name=None, _master=None, id=None, guides=None, shapes=None, anchors=None, color=None, layerIndex=0, background=None, isBackground=False, location=None)`

### Layer.width

* Python type: `int`


*If not provided, defaults to* `None`.


### Layer.height

* Python type: `int`


*If not provided, defaults to* `None`.


### Layer.vertWidth

* Python type: `int`


*If not provided, defaults to* `None`.


### Layer.name

* Python type: `str`


*If not provided, defaults to* `None`.


## Inherited Properties

As a subclass of `BaseObject`, this class also has these properties:

### user_data

* Python type: `dict`

Optional dictionary for format-specific data. This is stored as `_` in the Context-JSON serialization. Use this to store custom metadata that should be preserved when reading and writing files.

*If not provided, defaults to* `{}`.

