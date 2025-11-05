---
title: Anchor
---

[Font](Font.md) | [Axis](Axis.md) | [Instance](Instance.md) | [Master](Master.md) | [Names](Names.md) | [Features](Features.md) | [Glyph](Glyph.md) | [Layer](Layer.md) | [Guide](Guide.md) | [Shape](Shape.md) | **Anchor** | [Node](Node.md)

---

An anchor point in a glyph.

## Constructor

`Anchor(name=None, x=0, y=0)`

### Anchor.name

* Python type: `str`


*If not provided, defaults to* `None`.


### Anchor.x

* Python type: `int`


*If not provided, defaults to* `None`.


### Anchor.y

* Python type: `int`


*If not provided, defaults to* `None`.


## Inherited Properties

As a subclass of `BaseObject`, this class also has these properties:

### user_data

* Python type: `dict`

Optional dictionary for format-specific data. This is stored as `_` in the Context-JSON serialization. Use this to store custom metadata that should be preserved when reading and writing files.

Use keys such as `com.example.myCustomData` to avoid conflicts.

*If not provided, defaults to* `{}`.

