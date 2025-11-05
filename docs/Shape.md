---
title: Shape
---

[Font](Font.md) | [Axis](Axis.md) | [Instance](Instance.md) | [Master](Master.md) | [Names](Names.md) | [Features](Features.md) | [Glyph](Glyph.md) | [Layer](Layer.md) | [Guide](Guide.md) | **Shape** | [Anchor](Anchor.md) | [Node](Node.md)

---

A shape in a glyph layer - either a path or component reference.

* When writing to Context-JSON, this class must be serialized without newlines

## Constructor

`Shape(ref=None, transform=None, nodes=None, closed=True, direction=1)`

### Shape.ref

* Python type: `str`


*If not provided, defaults to* `None`.


### Shape.closed

* Python type: `bool`


*If not provided, defaults to* `None`.


### Shape.direction

* Python type: `int`

* Allowed values: `-1`, `1`


*If not provided, defaults to* `None`.


## Inherited Properties

As a subclass of `BaseObject`, this class also has these properties:

### user_data

* Python type: `dict`

Optional dictionary for format-specific data. This is stored as `_` in the Context-JSON serialization. Use this to store custom metadata that should be preserved when reading and writing files.

*If not provided, defaults to* `{}`.

