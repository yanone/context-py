from dataclasses import dataclass, fields, field
from typing import Union, Optional
import orjson
from collections import namedtuple
import datetime
import weakref


class IncompatibleMastersError(ValueError):
    pass


Color = namedtuple("Color", "r,g,b,a", defaults=[0, 0, 0, 0])
Position = namedtuple("Position", "x,y,angle", defaults=[0, 0, 0])
Number = Union[int, float]

# Standard dirty flag context names
DIRTY_FILE_SAVING = "file_saving"
DIRTY_CANVAS_RENDER = "canvas_render"
DIRTY_UNDO = "undo"
DIRTY_COMPILE = "compile"


class I18NDictionary(dict):
    @classmethod
    def with_default(cls, s):
        inst = cls()
        inst.set_default(s)
        return inst

    def copy_in(self, other):
        if isinstance(other, dict):
            for k, v in other.items():
                self[k] = v
        else:
            self.set_default(other)

    def default_or_dict(self):
        if len(self.values()) > 1:
            return self
        else:
            return self.get_default()

    def get_default(self):
        if "dflt" in self:
            return self["dflt"]
        elif len(list(self.values())):
            return list(self.values())[0]

    def set_default(self, value):
        if value:
            self["dflt"] = value

    def write(self, stream, indent):
        if len(self.keys()) > 1:
            stream.write(orjson.dumps(self))
        else:
            stream.write('"{0}"'.format(self.get_default()).encode())

    @property
    def as_fonttools_dict(self):
        rv = dict(self)
        if "dflt" in rv:
            if "en" not in rv:
                rv["en"] = rv["dflt"]
            del rv["dflt"]
        return rv


@dataclass
class BaseObject:
    # OK, what's going on here? And why do we split _FoobarFields from Foobar?
    # We want to achieve the following:
    #    * A ``_formatspecific`` field on *every* derived object...
    #    * ...which does not need to be added to the constructor arguments
    #    * ...but which (for convenience when instantiating from JSON) has an
    #      alias of ``_`` which *can* be added to the constructor arguments

    # dataclasses load up their fields by walking the inheritance tree, but
    # (just like Python function declarations) dataclasses don't support putting
    # defaultable fields after non-defaultable fields.

    # Because we want ``_formatspecific`` (and particularly ``_``) to be optional
    # on __init__ it needs to be defaultable. So it needs to appear after the
    # other fields in the inheritance hierarchy. So we inherit from a _...Fields
    # class first and then BaseObject second. Ugly but it works.

    # dataclasses also don't support field aliases. The ``_`` field is only
    # really used for initialization, so in ``__post_init__`` we move its
    # contents into the `_formatspecific` field where it really lives.

    # Field aliasing: Classes can define a _field_aliases dict mapping Python
    # field names to their serialized names in the file format. This allows
    # the Python API to use clear names while maintaining backward compatibility
    # with existing file formats.
    _field_aliases = {}

    _formatspecific: dict = field(
        default_factory=dict,
        repr=False,
        metadata={
            "skip_serialize": True,
            "description": """
Each object in Context has an optional attached dictionary to allow the storage
of format-specific information. Font creation software may store any additional
information that they wish to have preserved on import and export under a
namespaced (reverse-domain) key in this dictionary. For example, information
specific to the Glyphs software should be stored under the key `com.glyphsapp`.
The value stored under this key may be any data serializable in JSON; typically
it will be a `dict`.

Note that there is an important distinction between the Python object format
of this field and the Context-JSON representation. When stored to JSON, this key
is exported not as `_formatspecific` but as a simple underscore (`_`).
""",
        },
    )
    _: dict = field(default=None, repr=False, metadata={"skip_serialize": True})

    def __post_init__(self):
        if self._:
            self._formatspecific = self._
        # Initialize dirty tracking (not part of dataclass fields)
        # Only initialize if not already set
        if not hasattr(self, "_dirty_flags"):
            object.__setattr__(self, "_dirty_flags", None)
        if not hasattr(self, "_dirty_fields"):
            object.__setattr__(self, "_dirty_fields", None)
        if not hasattr(self, "_parent_ref"):
            object.__setattr__(self, "_parent_ref", None)

    @classmethod
    def _normalize_fields(cls, data_dict):
        """
        Convert serialized field names to Python field names.
        This allows the file format to use different names than the API.
        """
        if not isinstance(data_dict, dict):
            return data_dict

        # Create reverse mapping (serialized_name -> python_name)
        reverse_aliases = {v: k for k, v in cls._field_aliases.items()}

        normalized = {}
        for key, value in data_dict.items():
            # Use reverse alias if it exists, otherwise keep original
            python_name = reverse_aliases.get(key, key)
            normalized[python_name] = value

        return normalized

    _write_one_line = False
    _separate_items = {}

    def mark_dirty(self, context=DIRTY_FILE_SAVING, field_name=None, propagate=True):
        """
        Mark this object as dirty in the given context.

        Args:
            context: The context name (e.g., 'file_saving', 'canvas_render')
            field_name: Optional specific field that changed
            propagate: Whether to propagate dirty flag to parent
        """
        if self._dirty_flags is None:
            object.__setattr__(self, "_dirty_flags", {})
        self._dirty_flags[context] = True

        if field_name:
            if self._dirty_fields is None:
                object.__setattr__(self, "_dirty_fields", {})
            if context not in self._dirty_fields:
                self._dirty_fields[context] = set()
            self._dirty_fields[context].add(field_name)

        if propagate:
            parent = self._get_parent()
            if parent is not None:
                parent.mark_dirty(context, propagate=True)

    def mark_clean(self, context=DIRTY_FILE_SAVING, recursive=False):
        """
        Mark this object as clean in the given context.

        Args:
            context: The context name to mark clean
            recursive: Whether to recursively mark children clean
        """
        if self._dirty_flags:
            self._dirty_flags.pop(context, None)
            if not self._dirty_flags:  # Empty dict, set to None
                object.__setattr__(self, "_dirty_flags", None)

        if self._dirty_fields:
            self._dirty_fields.pop(context, None)
            if not self._dirty_fields:  # Empty dict, set to None
                object.__setattr__(self, "_dirty_fields", None)

        if recursive:
            self._mark_children_clean(context)

    def is_dirty(self, context=DIRTY_FILE_SAVING):
        """Check if this object is dirty in the given context."""
        if self._dirty_flags:
            return self._dirty_flags.get(context, False)
        return False

    def get_dirty_fields(self, context=DIRTY_FILE_SAVING):
        """Get the set of dirty fields for the given context."""
        if self._dirty_fields and context in self._dirty_fields:
            return self._dirty_fields[context].copy()
        return set()

    def _set_parent(self, parent):
        """Set parent reference using weakref to avoid circular references."""
        if parent is not None:
            ref = weakref.ref(parent)
            object.__setattr__(self, "_parent_ref", ref)
        else:
            object.__setattr__(self, "_parent_ref", None)

    def _get_parent(self):
        """Get parent object from weak reference."""
        if self._parent_ref is not None:
            return self._parent_ref()
        return None

    def _mark_children_clean(self, context):
        """
        Override in subclasses to recursively mark children clean.
        Default implementation does nothing.
        """
        pass

    def __setattr__(self, name, value):
        """Override setattr to automatically track changes."""
        # Skip internal fields and initialization
        if name.startswith("_") or not hasattr(self, "__dataclass_fields__"):
            object.__setattr__(self, name, value)
            return

        # Skip tracking if dirty flags not yet initialized
        if not hasattr(self, "_dirty_flags"):
            object.__setattr__(self, name, value)
            return

        # Only track if the field exists and value actually changed
        if name in self.__dataclass_fields__:
            old_value = getattr(self, name, None)
            if old_value != value:
                object.__setattr__(self, name, value)
                # Mark dirty for all standard contexts
                self.mark_dirty(DIRTY_FILE_SAVING, field_name=name, propagate=True)
                self.mark_dirty(DIRTY_CANVAS_RENDER, field_name=name, propagate=True)
            else:
                object.__setattr__(self, name, value)
        else:
            object.__setattr__(self, name, value)

    def _should_separate_when_serializing(self, key):
        if (
            key in self.__dataclass_fields__
            and "separate_items" in self.__dataclass_fields__[key].metadata
        ):
            return True
        return False

    def _write_value(self, stream, k, v, indent=0):
        if hasattr(v, "write"):
            v.write(stream, indent + 1)
        elif isinstance(v, tuple):
            stream.write(b"[")
            for ix, entry in enumerate(v):
                self._write_value(stream, k, entry, indent + 1)
                if ix < len(v) - 1:
                    stream.write(b", ")
            stream.write(b"]")
        elif isinstance(v, dict):
            stream.write(b"{")
            for ix, (k1, v1) in enumerate(v.items()):
                if self._should_separate_when_serializing(k):
                    stream.write(b"\n")
                    stream.write(b"  " * (indent + 2))
                if not isinstance(k1, str):
                    # XXX kerning keys are tuples
                    self._write_value(stream, k, "//".join(k1), indent + 1)
                else:
                    self._write_value(stream, k, k1, indent + 1)
                stream.write(b": ")
                self._write_value(stream, k, v1, indent + 1)
                if ix < len(v.items()) - 1:
                    stream.write(b", ")
            stream.write(b"}")
        elif isinstance(v, list):
            stream.write(b"[")
            for ix, item in enumerate(v):
                if self._should_separate_when_serializing(k):
                    stream.write(b"\n")
                    stream.write(b"  " * (indent + 2))
                self._write_value(stream, k, item, indent + 1)
                if ix < len(v) - 1:
                    stream.write(b", ")
            if self._should_separate_when_serializing(k):
                stream.write(b"\n")
                stream.write(b"  " * (indent + 1))
            stream.write(b"]")
        elif isinstance(v, datetime.datetime):
            # Format without microseconds to match loader expectation
            date_str = v.strftime("%Y-%m-%d %H:%M:%S")
            stream.write('"{0}"'.format(date_str).encode())
        else:
            stream.write(orjson.dumps(v))

    def write(self, stream, indent=0):
        if not self._write_one_line:
            stream.write(b"  " * indent)
        stream.write(b"{")
        towrite = []
        for f in fields(self):
            k = f.name
            if "skip_serialize" in f.metadata or "python_only" in f.metadata:
                continue
            v = getattr(self, k)
            default = f.default
            if (not v and "serialize_if_false" not in f.metadata) or (
                default and v == default
            ):
                continue
            # Use alias for serialization if defined
            serialized_name = self._field_aliases.get(k, k)
            towrite.append((serialized_name, v))

        for ix, (k, v) in enumerate(towrite):
            if not self._write_one_line:
                stream.write(b"\n")
                stream.write(b"  " * (indent + 1))

            stream.write('"{0}": '.format(k).encode())
            self._write_value(stream, k, v, indent)
            if ix != len(towrite) - 1:
                stream.write(b", ")

        if hasattr(self, "_formatspecific") and self._formatspecific:
            stream.write(b",")
            if not self._write_one_line:
                stream.write(b"\n")
                stream.write(b"  " * (indent + 1))
            stream.write(b'"_":')
            if self._write_one_line:
                stream.write(orjson.dumps(self._formatspecific))
            else:
                stream.write(b"\n")
                stream.write(
                    orjson.dumps(self._formatspecific, option=orjson.OPT_INDENT_2)
                )

        if not self._write_one_line:
            stream.write(b"\n")
        stream.write(b"}")
        if not self._write_one_line:
            stream.write(b"\n")
