---
title: Font
---

**Font** | [Axis](Axis.md) | [Instance](Instance.md) | [Master](Master.md) | [Names](Names.md) | [Features](Features.md) | [Glyph](Glyph.md) | [Layer](Layer.md) | [Guide](Guide.md) | [Shape](Shape.md) | [Anchor](Anchor.md)

---

Represents a font, with one or more masters.
## Font.user_data

* Python type: `dict`


Each object in Context has an optional attached dictionary to allow the storage
of format-specific information. Font creation software may store any additional
information that they wish to have preserved on import and export under a
namespaced (reverse-domain) key in this dictionary. For example, information
specific to the Glyphs software should be stored under the key `com.glyphsapp`.
The value stored under this key may be any data serializable in JSON; typically
it will be a `dict`.

Note that there is an important distinction between the Python object format
of this field and the Context-JSON representation. When stored to JSON, this key
is exported not as `user_data` but as a simple underscore (`_`).



## Font.upm

* Python type: `int`

The font's units per em.
*If not provided, defaults to* `1000`.


## Font.version

* Python type: `Tuple`

* Context-JSON type: `[int,int]`

Font version number as a tuple of integers (major, minor).
*If not provided, defaults to* `(1, 0)`.


## Font.axes

* Python type: [[`Axis`](Axis.md)]

* When writing to Context-JSON, each item in the list must be placed on a separate line.

A list of axes, in the case of variable/multiple master font. May be empty.


## Font.instances

* Python type: [[`Instance`](Instance.md)]

* When writing to Context-JSON, each item in the list must be placed on a separate line.

A list of named/static instances.


## Font.masters

* Python type: [[`Master`](Master.md)]

* When writing to Context-JSON, each item in the list must be placed on a separate line.

A list of the font's masters.


## Font.glyphs

* Python type: `GlyphList`

* Context-JSON type: `[dict]`

* When writing to Context-JSON, this structure is stored under the separate file `glyphs.json`.

* When writing to Context-JSON, each item in the list must be placed on a separate line.

A list of all glyphs supported in the font.

The `GlyphList` structure in the Python object is a dictionary with array-like
properties (or you might think of it as an array with dictionary-like properties)
containing [`Glyph`](Glyph.md) objects. The `GlyphList` may be iterated
directly, and may be appended to, but may also be used to index a `Glyph` by
its name. This is generally what you want:

```Python

for g in font.glyphs:
    assert isinstance(g, Glyph)

font.glyphs.append(newglyph)

glyph_ampersand = font.glyphs["ampersand"]
```
            


## Font.note

* Python type: `str`

Any user-defined textual note about this font.
*If not provided, defaults to* `None`.


## Font.date

* Python type: `datetime`

* Context-JSON type: `str`

The font's date. When writing to Context-JSON, this
should be stored in the format `%Y-%m-%d %H:%M:%S`. *If not provided, defaults
to the current date/time*.


## Font.names

* Python type: [`Names`](Names.md)




## Font.custom_opentype_values

* Python type: `Dict`

Any values to be placed in OpenType tables on export to override defaults; these must be font-wide. Metrics which may vary by master should be placed in the `metrics` field of a Master.


## Font.filename

* Python type: `Optional[str]`

* This field only exists as an attribute of the the Python object and should not be written to Context-JSON.

The file path from which this font was loaded
or to which it should be saved. This is automatically set when loading
a font and used as the default path when saving.
*If not provided, defaults to* `None`.


## Font.features

* Python type: [`Features`](Features.md)

A representation of the font's OpenType features


## Font.first_kern_groups

* Python type: `Dict`

A dictionary of kerning groups, where the key is the group name and the value is a list of glyph names in the group.


## Font.second_kern_groups

* Python type: `Dict`

A dictionary of kerning groups, where the key is the group name and the value is a list of glyph names in the group.


