---
title: Guide
---

[Font](Font.md) | [Axis](Axis.md) | [Instance](Instance.md) | [Master](Master.md) | [Names](Names.md) | [Features](Features.md) | [Glyph](Glyph.md) | [Layer](Layer.md) | **Guide** | [Shape](Shape.md) | [Anchor](Anchor.md) | [Node](Node.md)

---

A guide line in a glyph or master.

## Constructor

`Guide(position=None, name=None, color=None)`

### Guide.name

* Python type: `str`


*If not provided, defaults to* `None`.


### Guide.position

* Python type: `(dict, Position, list, tuple)`


*If not provided, defaults to* `None`.


### Guide.color

* Python type: `(dict, Color, list, tuple)`


*If not provided, defaults to* `None`.


## Inherited Properties

As a subclass of `BaseObject`, this class also has these properties:

### user_data

* Python type: `dict`

Optional dictionary for format-specific data. This is stored as `_` in the Context-JSON serialization. Use this to store custom metadata that should be preserved when reading and writing files.

*If not provided, defaults to* `{}`.

