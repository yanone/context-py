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

# Global flag to skip user_data tracking during serialization
_SKIP_USER_DATA_TRACKING = False


class TrackedDict(dict):
    """
    A dict subclass that notifies its owner when modified.
    Recursively converts nested dicts to TrackedDict to track deep changes.
    """

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Store owner as weak reference to avoid circular references
        self._owner_ref = weakref.ref(owner) if owner else None
        # Convert any nested dicts to TrackedDict
        self._convert_nested_dicts()

    def _convert_nested_dicts(self):
        """Convert any nested plain dicts to TrackedDict."""
        for key, value in list(self.items()):
            if isinstance(value, dict) and not isinstance(value, TrackedDict):
                # Create a nested TrackedDict with same owner
                nested = TrackedDict(
                    owner=self._owner_ref() if self._owner_ref else None
                )
                nested.update(value)
                # Use dict.__setitem__ to avoid triggering dirty marking during init
                dict.__setitem__(self, key, nested)
            elif isinstance(value, list):
                # Convert lists containing dicts
                new_list = []
                for item in value:
                    if isinstance(item, dict) and not isinstance(item, TrackedDict):
                        nested = TrackedDict(
                            owner=self._owner_ref() if self._owner_ref else None
                        )
                        nested.update(item)
                        new_list.append(nested)
                    else:
                        new_list.append(item)
                if any(
                    isinstance(item, TrackedDict) for item in new_list
                ):  # Only replace if we converted something
                    dict.__setitem__(self, key, new_list)

    def _mark_owner_dirty(self):
        """Mark the owner object as dirty when dict is modified."""
        if self._owner_ref:
            owner = self._owner_ref()
            # Only mark dirty if owner exists and tracking is enabled
            if (
                owner
                and hasattr(owner, "mark_dirty")
                and hasattr(owner, "_tracking_enabled")
                and owner._tracking_enabled
            ):
                owner.mark_dirty(
                    DIRTY_FILE_SAVING, field_name="user_data", propagate=True
                )
                owner.mark_dirty(
                    DIRTY_CANVAS_RENDER, field_name="user_data", propagate=True
                )

    def __setitem__(self, key, value):
        # Convert nested dicts to TrackedDict
        if isinstance(value, dict) and not isinstance(value, TrackedDict):
            nested = TrackedDict(owner=self._owner_ref() if self._owner_ref else None)
            nested.update(value)
            value = nested
        elif isinstance(value, list):
            # Convert lists containing dicts
            new_list = []
            converted = False
            for item in value:
                if isinstance(item, dict) and not isinstance(item, TrackedDict):
                    nested = TrackedDict(
                        owner=self._owner_ref() if self._owner_ref else None
                    )
                    nested.update(item)
                    new_list.append(nested)
                    converted = True
                else:
                    new_list.append(item)
            if converted:
                value = new_list

        super().__setitem__(key, value)
        self._mark_owner_dirty()

    def __delitem__(self, key):
        super().__delitem__(key)
        self._mark_owner_dirty()

    def clear(self):
        super().clear()
        self._mark_owner_dirty()

    def pop(self, *args, **kwargs):
        result = super().pop(*args, **kwargs)
        self._mark_owner_dirty()
        return result

    def popitem(self):
        result = super().popitem()
        self._mark_owner_dirty()
        return result

    def setdefault(self, key, default=None):
        if key not in self:
            self._mark_owner_dirty()
        return super().setdefault(key, default)

    def update(self, *args, **kwargs):
        # First do the update with converted values
        temp_dict = dict(*args, **kwargs)
        for key, value in temp_dict.items():
            self[key] = value  # This will use our __setitem__ which converts nested
        # Note: _mark_owner_dirty is called by __setitem__ for each item


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
        """Get the default value, or first value if no explicit default."""
        if "dflt" in self:
            return self["dflt"]
        elif len(list(self.values())):
            return list(self.values())[0]

    def set_default(self, value):
        """Set the default value."""
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
    #    * A ``user_data`` field on *every* derived object...
    #    * ...which does not need to be added to the constructor arguments
    #    * ...but which (for convenience when instantiating from JSON) has an
    #      alias of ``_`` which *can* be added to the constructor arguments

    # dataclasses load up their fields by walking the inheritance tree, but
    # (just like Python function declarations) dataclasses don't support putting
    # defaultable fields after non-defaultable fields.

    # Because we want ``user_data`` (and particularly ``_``) to be optional
    # on __init__ it needs to be defaultable. So it needs to appear after the
    # other fields in the inheritance hierarchy. So we inherit from a _...Fields
    # class first and then BaseObject second. Ugly but it works.

    # dataclasses also don't support field aliases. The ``_`` field is only
    # really used for initialization, so in ``__post_init__`` we move its
    # contents into the `user_data` field where it really lives.

    # Field aliasing: Classes can define a _field_aliases dict mapping Python
    # field names to their serialized names in the file format. This allows
    # the Python API to use clear names while maintaining backward compatibility
    # with existing file formats.
    _field_aliases = {}

    # Tracking control: When False, __setattr__ bypasses all dirty tracking
    # for fast loading. Call initialize_dirty_tracking() to enable.
    _tracking_enabled = False

    user_data: dict = field(
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
is exported not as `user_data` but as a simple underscore (`_`).
""",
        },
    )
    _: dict = field(default=None, repr=False, metadata={"skip_serialize": True})

    def __post_init__(self):
        # Fast initialization during loading - minimal overhead
        # Handle _ shorthand: copy to user_data if provided
        if self._ is not None:
            object.__setattr__(self, "user_data", self._)

        # Initialize tracking infrastructure to None (populated on tracking init)
        # Simplified: no hasattr checks needed, __post_init__ always runs once
        object.__setattr__(self, "_dirty_flags", None)
        object.__setattr__(self, "_dirty_fields", None)
        object.__setattr__(self, "_parent_ref", None)
        object.__setattr__(self, "_user_data_snapshot", None)
        object.__setattr__(self, "_skip_user_data_check", False)

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
        # Lazy initialization: Initialize tracking if not yet done
        # This happens when mark_clean is called recursively on children
        if self._dirty_flags is None:
            object.__setattr__(self, "_dirty_flags", {})
        if self._dirty_fields is None:
            object.__setattr__(self, "_dirty_fields", {})
        # Enable tracking (needed for user_data change detection)
        if hasattr(self, "_tracking_enabled") and not self._tracking_enabled:
            object.__setattr__(self, "_tracking_enabled", True)

        # Mark clean in this context
        if self._dirty_flags:
            self._dirty_flags.pop(context, None)
            # Keep as empty dict, don't set to None
            # (None means tracking not initialized, {} means clean)

        if self._dirty_fields:
            self._dirty_fields.pop(context, None)
            # Keep as empty dict, don't set to None

        # Don't snapshot user_data here - let it be lazy!
        # Snapshot will be created automatically when:
        # - user_data is first accessed (via tracked_getattribute)
        # - user_data is modified (via tracked_setattr)
        # This avoids expensive upfront snapshotting of 877k objects

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

    def _snapshot_user_data(self):
        """Create a snapshot of user_data for change detection."""
        if hasattr(self, "user_data") and self.user_data:
            # Serialize with sorted keys for consistent comparison
            # OPT_NON_STR_KEYS: Allow non-string dict keys
            snapshot = orjson.dumps(
                self.user_data,
                option=orjson.OPT_SORT_KEYS | orjson.OPT_NON_STR_KEYS,
            )
            object.__setattr__(self, "_user_data_snapshot", snapshot)
        else:
            object.__setattr__(self, "_user_data_snapshot", None)

    def _check_user_data_changed(self):
        """
        Check if user_data has changed since last snapshot.
        Returns True if changed, False otherwise.
        Marks object dirty if changes detected.
        """
        # Use object.__getattribute__ to avoid recursion
        try:
            user_data = object.__getattribute__(self, "user_data")
        except AttributeError:
            return False

        # Skip if user_data is empty (optimization)
        if not user_data:
            return False

        # Get current serialized state
        # OPT_NON_STR_KEYS: Allow non-string dict keys (converted to strings)
        current = orjson.dumps(
            user_data,
            option=orjson.OPT_SORT_KEYS | orjson.OPT_NON_STR_KEYS,
        )

        # Compare with snapshot
        try:
            old_snapshot = object.__getattribute__(self, "_user_data_snapshot")
        except AttributeError:
            old_snapshot = None

        # Lazy initialization: if no snapshot exists yet, create one now
        # This avoids creating snapshots during initialization for all objects
        if old_snapshot is None:
            object.__setattr__(self, "_user_data_snapshot", current)
            return False  # First access, not a change

        changed = current != old_snapshot

        # If changed and tracking is enabled, mark dirty and update snapshot
        if changed:
            try:
                tracking_enabled = (
                    object.__getattribute__(self, "_tracking_enabled")
                    and object.__getattribute__(self, "_dirty_flags") is not None
                )
            except AttributeError:
                tracking_enabled = False

            if tracking_enabled:
                mark_dirty = object.__getattribute__(self, "mark_dirty")
                mark_dirty(DIRTY_FILE_SAVING, field_name="user_data", propagate=True)
                mark_dirty(
                    DIRTY_CANVAS_RENDER,
                    field_name="user_data",
                    propagate=True,
                )
                # Update snapshot after marking dirty
                object.__setattr__(self, "_user_data_snapshot", current)

        return changed

    @classmethod
    def _enable_tracking_setattr(cls):
        """
        Enable dirty tracking by adding __setattr__ to the class.

        This is called once when initialize_dirty_tracking() is first invoked.
        By not defining __setattr__ in the class, we avoid overhead during
        loading when tracking is not needed.
        """
        # Check if already enabled (avoid redefining)
        if (
            hasattr(cls, "__setattr__")
            and cls.__setattr__.__name__ == "tracked_setattr"
        ):
            return

        def tracked_setattr(self, name, value):
            """Override setattr to automatically track changes."""
            # Fast path for internal fields
            if name.startswith("_") or not hasattr(self, "__dataclass_fields__"):
                object.__setattr__(self, name, value)
                return

            # Check if tracking is initialized (avoid errors during __init__)
            tracking_enabled = (
                hasattr(self, "_dirty_flags") and self._dirty_flags is not None
            )

            # Special handling for user_data field
            if name == "user_data":
                # Convert regular dict to TrackedDict
                if isinstance(value, dict) and not isinstance(value, TrackedDict):
                    tracked = TrackedDict(owner=self)
                    tracked.update(value)
                    value = tracked
                object.__setattr__(self, name, value)
                # Mark dirty and snapshot (only if tracking enabled)
                if tracking_enabled:
                    self.mark_dirty(DIRTY_FILE_SAVING, field_name=name, propagate=True)
                    self.mark_dirty(
                        DIRTY_CANVAS_RENDER, field_name=name, propagate=True
                    )
                    # Create snapshot for future nested change detection
                    self._snapshot_user_data()
                return

            # Only track if the field exists and value actually changed
            if name in self.__dataclass_fields__:
                old_value = getattr(self, name, None)
                if old_value != value:
                    object.__setattr__(self, name, value)
                    # Mark dirty for all standard contexts (only if tracking enabled)
                    if tracking_enabled:
                        self.mark_dirty(
                            DIRTY_FILE_SAVING, field_name=name, propagate=True
                        )
                        self.mark_dirty(
                            DIRTY_CANVAS_RENDER, field_name=name, propagate=True
                        )
                else:
                    object.__setattr__(self, name, value)
            else:
                object.__setattr__(self, name, value)

        # Add __setattr__ to the class (affects all instances)
        cls.__setattr__ = tracked_setattr

        def tracked_getattribute(self, name):
            """
            Override getattribute to check for nested user_data changes.
            When user_data is accessed, check if nested content changed.
            Also lazily converts regular dict to TrackedDict on first access.
            """
            # Get the attribute using default mechanism
            value = object.__getattribute__(self, name)

            # Early exit: Only process user_data
            if name != "user_data":
                return value

            # Skip tracking during serialization (performance optimization)
            import context.BaseObject

            if context.BaseObject._SKIP_USER_DATA_TRACKING:
                return value

            # Handle user_data access (only if not empty)
            if value:
                try:
                    skip_check = object.__getattribute__(self, "_skip_user_data_check")
                    if skip_check:
                        return value

                    tracking_enabled = (
                        object.__getattribute__(self, "_tracking_enabled")
                        and object.__getattribute__(self, "_dirty_flags") is not None
                    )

                    if tracking_enabled:
                        # Lazy conversion: convert to TrackedDict on first access
                        # Skip empty dicts to save memory and time
                        if (
                            isinstance(value, dict)
                            and not isinstance(value, TrackedDict)
                            and value  # Only convert non-empty dicts
                        ):
                            tracked = TrackedDict(owner=self)
                            tracked.update(value)
                            object.__setattr__(self, "user_data", tracked)
                            value = tracked

                        # Check for nested changes (only if non-empty)
                        if value:
                            _check = object.__getattribute__(
                                self, "_check_user_data_changed"
                            )
                            _check()
                except AttributeError:
                    # During initialization, these attrs might not exist
                    pass

            return value

        # Add __getattribute__ to the class
        cls.__getattribute__ = tracked_getattribute

    def _should_separate_when_serializing(self, key):
        # Cache the result to avoid repeated dictionary lookups
        cache_attr = "_separate_cache"
        if not hasattr(self, cache_attr):
            object.__setattr__(self, cache_attr, {})

        cache = object.__getattribute__(self, cache_attr)
        if key in cache:
            return cache[key]

        result = (
            key in self.__dataclass_fields__
            and "separate_items" in self.__dataclass_fields__[key].metadata
        )
        cache[key] = result
        return result

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
            # Allow non-string keys in case v is a dict
            stream.write(orjson.dumps(v, option=orjson.OPT_NON_STR_KEYS))

    def write(self, stream, indent=0):
        if not self._write_one_line:
            stream.write(b"  " * indent)
        stream.write(b"{")
        towrite = []
        # Cache fields() result at class level for performance
        cls = type(self)
        if not hasattr(cls, "_cached_fields"):
            cls._cached_fields = fields(self)
        for f in cls._cached_fields:
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

        if hasattr(self, "user_data") and self.user_data:
            stream.write(b",")
            if not self._write_one_line:
                stream.write(b"\n")
                stream.write(b"  " * (indent + 1))
            stream.write(b'"_":')
            if self._write_one_line:
                stream.write(
                    orjson.dumps(
                        self.user_data,
                        option=orjson.OPT_SORT_KEYS | orjson.OPT_NON_STR_KEYS,
                    )
                )
            else:
                stream.write(b"\n")
                stream.write(
                    orjson.dumps(
                        self.user_data,
                        option=orjson.OPT_INDENT_2
                        | orjson.OPT_SORT_KEYS
                        | orjson.OPT_NON_STR_KEYS,
                    )
                )

        if not self._write_one_line:
            stream.write(b"\n")
        stream.write(b"}")
        if not self._write_one_line:
            stream.write(b"\n")
