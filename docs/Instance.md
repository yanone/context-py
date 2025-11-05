---
title: Instance
---

[Font](Font.md) | [Axis](Axis.md) | **Instance** | [Master](Master.md) | [Names](Names.md) | [Features](Features.md) | [Glyph](Glyph.md) | [Layer](Layer.md) | [Guide](Guide.md) | [Shape](Shape.md) | [Anchor](Anchor.md) | [Node](Node.md)

---

An object representing a named or static instance.

* When writing to Context-JSON, this class must be serialized without newlines

## Constructor

`Instance(name=None, location=None, variable=False, customNames=None)`

## Inherited Properties

As a subclass of `BaseObject`, this class also has these properties:

### user_data

* Python type: `dict`

Optional dictionary for format-specific data. This is stored as `_` in the Context-JSON serialization. Use this to store custom metadata that should be preserved when reading and writing files.

*If not provided, defaults to* `{}`.

