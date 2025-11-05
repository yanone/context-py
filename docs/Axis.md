---
title: Axis
---

[Font](Font.md) | **Axis** | [Instance](Instance.md) | [Master](Master.md) | [Names](Names.md) | [Features](Features.md) | [Glyph](Glyph.md) | [Layer](Layer.md) | [Guide](Guide.md) | [Shape](Shape.md) | [Anchor](Anchor.md) | [Node](Node.md)

---

Represents an axis in a multiple master or variable font.

* When writing to Context-JSON, this class must be serialized without newlines

## Constructor

`Axis(name=None, tag=None, id=None, min=None, max=None, default=None, map=None, hidden=False)`

## Inherited Properties

As a subclass of `BaseObject`, this class also has these properties:

### user_data

* Python type: `dict`

Optional dictionary for format-specific data. This is stored as `_` in the Context-JSON serialization. Use this to store custom metadata that should be preserved when reading and writing files.

*If not provided, defaults to* `{}`.

