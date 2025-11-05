---
title: Master
---

[Font](Font.md) | [Axis](Axis.md) | [Instance](Instance.md) | **Master** | [Names](Names.md) | [Features](Features.md) | [Glyph](Glyph.md) | [Layer](Layer.md) | [Guide](Guide.md) | [Shape](Shape.md) | [Anchor](Anchor.md) | [Node](Node.md)

---

A font master.

## Constructor

`Master(name=None, id=None, location=None, sparse=False, guides=None, metrics=None, kerning=None, font=None)`

## Inherited Properties

As a subclass of `BaseObject`, this class also has these properties:

### user_data

* Python type: `dict`

Optional dictionary for format-specific data. This is stored as `_` in the Context-JSON serialization. Use this to store custom metadata that should be preserved when reading and writing files.

Use keys such as `com.example.myCustomData` to avoid conflicts.

*If not provided, defaults to* `{}`.

