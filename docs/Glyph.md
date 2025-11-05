---
title: Glyph
---

[Font](Font.md) | [Axis](Axis.md) | [Instance](Instance.md) | [Master](Master.md) | [Names](Names.md) | [Features](Features.md) | **Glyph** | [Layer](Layer.md) | [Guide](Guide.md) | [Shape](Shape.md) | [Anchor](Anchor.md) | [Node](Node.md)

---

A glyph in a font.

* When writing to Context-JSON, this class must be serialized without newlines

## Constructor

`Glyph(name=None, production_name=None, category='base', codepoints=None, layers=None, exported=True, direction='LTR')`

## Inherited Properties

As a subclass of `BaseObject`, this class also has these properties:

### user_data

* Python type: `dict`

Optional dictionary for format-specific data. This is stored as `_` in the Context-JSON serialization. Use this to store custom metadata that should be preserved when reading and writing files.

Use keys such as `com.example.myCustomData` to avoid conflicts.

*If not provided, defaults to* `{}`.

