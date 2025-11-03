---
title: Layer
---

[Font](Font.md) | [Axis](Axis.md) | [Instance](Instance.md) | [Master](Master.md) | [Names](Names.md) | [Features](Features.md) | [Glyph](Glyph.md) | **Layer** | [Guide](Guide.md) | [Shape](Shape.md) | [Anchor](Anchor.md)

---

Layer(width: int = 0, height: int = 0, vertWidth: Optional[int] = None, name: str = None, _master: str = None, id: str = <factory>, guides: List[context.Guide.Guide] = <factory>, shapes: List[context.Shape.Shape] = <factory>, anchors: List[context.Anchor.Anchor] = <factory>, color: context.BaseObject.Color = None, layerIndex: int = 0, background: Optional[str] = None, isBackground: bool = False, location: List[float] = None, user_data: dict = <factory>, _: dict = None)
## Layer.width

* Python type: `int`


*If not provided, defaults to* `0`.


## Layer.height

* Python type: `int`


*If not provided, defaults to* `0`.


## Layer.vertWidth

* Python type: `Optional[int]`


*If not provided, defaults to* `None`.


## Layer.name

* Python type: `str`


*If not provided, defaults to* `None`.


## Layer._master

* Python type: `str`


*If not provided, defaults to* `None`.


## Layer.id

* Python type: `str`




## Layer.guides

* Python type: [[`Guide`](Guide.md)]




## Layer.shapes

* Python type: [[`Shape`](Shape.md)]

* When writing to Context-JSON, each item in the list must be placed on a separate line.




## Layer.anchors

* Python type: [[`Anchor`](Anchor.md)]




## Layer.color

* Python type: `Color`


*If not provided, defaults to* `None`.


## Layer.layerIndex

* Python type: `int`


*If not provided, defaults to* `0`.


## Layer.background

* Python type: `Optional[str]`


*If not provided, defaults to* `None`.


## Layer.isBackground

* Python type: `bool`


*If not provided, defaults to* `False`.


## Layer.location

* Python type: `[float]`


*If not provided, defaults to* `None`.


## Layer.user_data

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



