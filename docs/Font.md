---
title: Font
---

**Font** | [Axis](Axis.md) | [Instance](Instance.md) | [Master](Master.md) | [Names](Names.md) | [Features](Features.md) | [Glyph](Glyph.md) | [Layer](Layer.md) | [Guide](Guide.md) | [Shape](Shape.md) | [Anchor](Anchor.md) | [Node](Node.md)

---

Represents a font, with one or more masters.

## Constructor

`Font(upm=1000, version=(1, 0), axes=None, instances=None, masters=None, glyphs=None, note=None, date=None, names=None, custom_opentype_values=None, filename=None, features=None, first_kern_groups=None, second_kern_groups=None)`

## Inherited Properties

As a subclass of `BaseObject`, this class also has these properties:

### user_data

* Python type: `dict`

Optional dictionary for format-specific data. This is stored as `_` in the Context-JSON serialization. Use this to store custom metadata that should be preserved when reading and writing files.

*If not provided, defaults to* `{}`.

