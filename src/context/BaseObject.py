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
            if isinstance(value, dict) and not isinstance(
                value, (TrackedDict, I18NDictionary)
            ):
                # Create a nested TrackedDict with same owner
                nested = TrackedDict(
                    owner=self._owner_ref() if self._owner_ref else None
                )
                nested.update(value)
                # Use dict.__setitem__ to avoid triggering dirty marking during init
                dict.__setitem__(self, key, nested)
            elif isinstance(value, list):
                # Convert lists containing dicts (but not I18NDictionary)
                new_list = []
                for item in value:
                    if isinstance(item, dict) and not isinstance(
                        item, (TrackedDict, I18NDictionary)
                    ):
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
        # Convert nested dicts to TrackedDict (but not I18NDictionary)
        if isinstance(value, dict) and not isinstance(
            value, (TrackedDict, I18NDictionary)
        ):
            nested = TrackedDict(owner=self._owner_ref() if self._owner_ref else None)
            nested.update(value)
            value = nested
        elif isinstance(value, list):
            # Convert lists containing dicts (but not I18NDictionary)
            new_list = []
            converted = False
            for item in value:
                if isinstance(item, dict) and not isinstance(
                    item, (TrackedDict, I18NDictionary)
                ):
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


class TrackedList(list):
    """
    A list subclass that syncs modifications back to owner's _data.

    When the list is modified (append, remove, etc.), it converts
    objects to dicts and updates the owner's _data[field_name].
    This allows natural list operations while maintaining dict storage.
    """

    def __init__(self, owner, field_name, item_class, *args, **kwargs):
        """
        Initialize TrackedList.

        Args:
            owner: The parent object (e.g., Layer, Shape)
            field_name: The field name in owner._data (e.g., "shapes")
            item_class: The class to convert dicts to (e.g., Shape)
        """
        super().__init__(*args, **kwargs)
        self._owner_ref = weakref.ref(owner) if owner else None
        self._field_name = field_name
        self._item_class = item_class

    def _set_parent(self, item):
        """Set parent reference and enable tracking on an item."""
        owner = self._owner_ref() if self._owner_ref else None
        if owner:
            # Set parent reference if supported
            if hasattr(item, "_set_parent"):
                item._set_parent(owner)
            # Enable tracking if owner has it enabled
            if (
                hasattr(owner, "_tracking_enabled")
                and owner._tracking_enabled
                and hasattr(item, "_tracking_enabled")
            ):
                object.__setattr__(item, "_tracking_enabled", True)
                # Initialize dirty flags if not already set
                if item._dirty_flags is None:
                    object.__setattr__(item, "_dirty_flags", {})
                if item._dirty_fields is None:
                    object.__setattr__(item, "_dirty_fields", {})

    def _sync_to_data(self, mark_dirty=True):
        """Convert all objects to dicts and update owner._data.

        Args:
            mark_dirty: Whether to mark owner dirty after sync.
                       Set to False when initializing cache.
        """
        owner = self._owner_ref() if self._owner_ref else None
        if owner:
            # SHARED REFS: Store references to item._data (not copies!)
            # This means modifying item._data auto-updates parent._data
            dict_list = [
                item._data if hasattr(item, "_data") else item for item in self
            ]
            owner._data[self._field_name] = dict_list

            # Mark owner dirty if tracking enabled and requested
            if (
                mark_dirty
                and hasattr(owner, "_tracking_enabled")
                and owner._tracking_enabled
            ):
                owner.mark_dirty()

    def append(self, item):
        self._set_parent(item)
        super().append(item)
        self._sync_to_data()

    def extend(self, items, mark_dirty=True):
        """Extend list with items.

        Args:
            items: Items to add
            mark_dirty: Whether to mark owner dirty. Set False when caching.
        """
        for item in items:
            self._set_parent(item)
        super().extend(items)
        self._sync_to_data(mark_dirty=mark_dirty)

    def insert(self, index, item):
        self._set_parent(item)
        super().insert(index, item)
        self._sync_to_data()

    def remove(self, item):
        super().remove(item)
        self._sync_to_data()

    def pop(self, index=-1):
        result = super().pop(index)
        self._sync_to_data()
        return result

    def clear(self):
        super().clear()
        self._sync_to_data()

    def __setitem__(self, index, item):
        self._set_parent(item)
        super().__setitem__(index, item)
        self._sync_to_data()

    def __delitem__(self, index):
        super().__delitem__(index)
        self._sync_to_data()

    def __iadd__(self, other):
        for item in other:
            self._set_parent(item)
        result = super().__iadd__(other)
        self._sync_to_data()
        return result

    def __imul__(self, other):
        result = super().__imul__(other)
        self._sync_to_data()
        return result


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


class BaseObject:
    """
    Base class for all font objects with dict-backed storage.

    All data is stored in self._data dict as serializable dicts/lists/primitives.
    Properties convert dicts to objects on read, objects to dicts on write.

    This makes serialization instant: to_dict() just returns _data unchanged.

    IMPORTANT: List properties return NEW objects each time accessed.
    To modify lists, use assignment pattern:
        items = obj.items
        items.append(new_item)
        obj.items = items
    """

    # Field aliasing: Classes can define a _field_aliases dict mapping Python
    # field names to their serialized names in the file format.
    _field_aliases = {}

    # Tracking control: When False, __setattr__ bypasses all dirty tracking
    # for fast loading. Call initialize_dirty_tracking() to enable.
    _tracking_enabled = False

    def __init__(self, _data=None, _validate=True, **kwargs):
        """
        Initialize with dict-backed storage.

        Args:
            _data: Dictionary containing all object data (primary storage)
            _validate: If False, skip required field validation (for loading)
            **kwargs: Individual field values (will be stored in _data)
        """
        # Initialize _data dict - this is the ONLY data storage
        if _data is not None:
            object.__setattr__(self, "_data", _data)
            data_to_validate = _data
        else:
            # Build _data from kwargs
            object.__setattr__(self, "_data", kwargs)
            data_to_validate = kwargs

        # Validate required fields if _field_types is defined and validation enabled
        if _validate and hasattr(self.__class__, "_field_types"):
            for field_name, field_info in self.__class__._field_types.items():
                is_required = isinstance(field_info, dict) and field_info.get(
                    "required", False
                )
                if is_required:
                    value = data_to_validate.get(field_name)
                    if value is None:
                        raise ValueError(
                            f"{self.__class__.__name__}.{field_name} is a "
                            f"required field and cannot be None"
                        )
                    # For string fields, also check for empty strings
                    if field_info.get("data_type") == str and value == "":
                        raise ValueError(
                            f"{self.__class__.__name__}.{field_name} is a "
                            f"required field and cannot be empty"
                        )

        # Initialize tracking infrastructure
        object.__setattr__(self, "_tracking_enabled", False)
        object.__setattr__(self, "_dirty_flags", None)
        object.__setattr__(self, "_dirty_fields", None)
        object.__setattr__(self, "_parent_ref", None)
        object.__setattr__(self, "_user_data_snapshot", None)
        object.__setattr__(self, "_skip_user_data_check", False)

    @property
    def user_data(self):
        """
        Optional dictionary for format-specific data.
        Stored as "_" in JSON serialization.
        """
        # Use object.__getattribute__ to avoid triggering tracked_getattribute
        _data = object.__getattribute__(self, "_data")
        return _data.get("_", {})

    @user_data.setter
    def user_data(self, value):
        self._data["_"] = value
        if hasattr(self, "mark_dirty") and self._tracking_enabled:
            self.mark_dirty()

    @property
    def _(self):
        """Alias for user_data."""
        return self.user_data

    @_.setter
    def _(self, value):
        """Alias for user_data."""
        self.user_data = value

    # Type checking for setters
    _field_types = {}

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

    def _set_field(self, field_name, value, expected_type=None):
        """
        Helper method for setters with type checking.

        Args:
            field_name: Name of the field to set
            value: Value to set
            expected_type: Expected type(s) for validation. Can be:
                - A single type: int, str, etc.
                - A tuple of types: (int, float)
                - A dict with "data_type" and optional "allowed_values"
                - None to skip type checking

        Raises:
            ValueError: If value doesn't match expected type or allowed values
        """
        # Use class-level type definition if not provided
        validation_rules = expected_type
        if validation_rules is None and hasattr(self, "_field_types"):
            validation_rules = self._field_types.get(field_name)

        # Perform validation
        if validation_rules is not None:
            # Handle nested dict format with data_type and allowed_values
            if isinstance(validation_rules, dict):
                # Check if field is required
                is_required = validation_rules.get("required", False)
                if is_required:
                    if value is None:
                        raise ValueError(
                            f"{self.__class__.__name__}.{field_name} is a "
                            f"required field and cannot be None"
                        )
                    # For string fields, also check for empty strings
                    if validation_rules.get("data_type") == str and value == "":
                        raise ValueError(
                            f"{self.__class__.__name__}.{field_name} is a "
                            f"required field and cannot be empty"
                        )

                data_type = validation_rules.get("data_type")
                allowed_values = validation_rules.get("allowed_values")

                # Check data type
                if data_type is not None:
                    if not isinstance(value, data_type):
                        # Format type name(s) for error message
                        if isinstance(data_type, tuple):
                            type_names = " or ".join(t.__name__ for t in data_type)
                        else:
                            type_names = data_type.__name__
                        raise ValueError(
                            f"{self.__class__.__name__}.{field_name} must be "
                            f"{type_names}, got {type(value).__name__}"
                        )

                # Check allowed values
                if allowed_values is not None:
                    if value not in allowed_values:
                        raise ValueError(
                            f"{self.__class__.__name__}.{field_name} must be "
                            f"one of {allowed_values}, got {value!r}"
                        )
            else:
                # Legacy format: direct type or tuple of types
                if not isinstance(value, validation_rules):
                    # Format type name(s) for error message
                    if isinstance(validation_rules, tuple):
                        type_names = " or ".join(t.__name__ for t in validation_rules)
                    else:
                        type_names = validation_rules.__name__
                    raise ValueError(
                        f"{self.__class__.__name__}.{field_name} must be "
                        f"{type_names}, got {type(value).__name__}"
                    )

        # Convert Python field name to file format name if aliased
        # Use object.__getattribute__ to bypass tracked_getattribute
        field_aliases = object.__getattribute__(self, "_field_aliases")
        storage_name = field_aliases.get(field_name, field_name)

        # Set the value and mark dirty with field name for tracking
        _data = object.__getattribute__(self, "_data")
        _data[storage_name] = value

        tracking_enabled = object.__getattribute__(self, "_tracking_enabled")
        if tracking_enabled:
            # Propagate to immediate parent only (mark_dirty limits cascade)
            self.mark_dirty(field_name=field_name, propagate=True)

    _write_one_line = False
    _separate_items = {}

    def mark_dirty(self, context=None, field_name=None, propagate=True):
        """
        Mark this object as dirty in the given context(s).

        Args:
            context: The context name or None for all standard contexts
            field_name: Optional specific field that changed
            propagate: Whether to propagate dirty flag to parent
        """
        # Use object.__getattribute__ to bypass tracked_getattribute
        dirty_flags = object.__getattribute__(self, "_dirty_flags")
        if dirty_flags is None:
            dirty_flags = {}
            object.__setattr__(self, "_dirty_flags", dirty_flags)

        # If no context specified, mark for all standard contexts
        if context is None:
            contexts = [DIRTY_FILE_SAVING, DIRTY_CANVAS_RENDER]
        else:
            contexts = [context]

        for ctx in contexts:
            # Check if already dirty in this context before propagating
            was_already_dirty = dirty_flags.get(ctx, False)

            dirty_flags[ctx] = True

            if field_name:
                dirty_fields = object.__getattribute__(self, "_dirty_fields")
                if dirty_fields is None:
                    dirty_fields = {}
                    object.__setattr__(self, "_dirty_fields", dirty_fields)
                if ctx not in dirty_fields:
                    dirty_fields[ctx] = set()
                dirty_fields[ctx].add(field_name)

            # Only propagate if we weren't already dirty (prevents redundant calls)
            # This makes mark_dirty idempotent for performance
            if propagate and not was_already_dirty:
                parent = self._get_parent()
                if parent is not None:
                    parent.mark_dirty(ctx, propagate=True)

    def mark_clean(self, context=DIRTY_FILE_SAVING, recursive=False, build_cache=False):
        """
        Mark this object as clean in the given context.

        Args:
            context: The context name to mark clean
            recursive: Whether to recursively mark children clean
            build_cache: Whether to build dict cache proactively
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

        # Proactively build dict cache when marking clean
        # This makes subsequent to_dict() calls instant
        if build_cache and context == DIRTY_FILE_SAVING:
            # Temporarily disable tracking during cache build for speed
            old_skip = _SKIP_USER_DATA_TRACKING
            globals()["_SKIP_USER_DATA_TRACKING"] = True
            try:
                # Build cache without tracking overhead
                cache_dict = self._to_dict_no_cache()
                object.__setattr__(self, "_dict_cache", cache_dict)
            finally:
                globals()["_SKIP_USER_DATA_TRACKING"] = old_skip

        if recursive:
            self._mark_children_clean(context, build_cache=build_cache)

    def is_dirty(self, context=DIRTY_FILE_SAVING):
        """Check if this object is dirty in the given context."""
        # Use object.__getattribute__ to bypass tracked_getattribute
        dirty_flags = object.__getattribute__(self, "_dirty_flags")
        if dirty_flags:
            return dirty_flags.get(context, False)
        return False

    def get_dirty_fields(self, context=DIRTY_FILE_SAVING):
        """Get the set of dirty fields for the given context."""
        # Use object.__getattribute__ to bypass tracked_getattribute
        dirty_fields = object.__getattribute__(self, "_dirty_fields")
        if dirty_fields and context in dirty_fields:
            return dirty_fields[context].copy()
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
        # Use object.__getattribute__ to bypass tracked_getattribute
        parent_ref = object.__getattribute__(self, "_parent_ref")
        if parent_ref is not None:
            return parent_ref()
        return None

    def _mark_children_clean(self, context, build_cache=False):
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

            # Early exit: Only process user_data (fastest check first)
            # This skips tracking for ALL other attributes including private ones
            if name != "user_data":
                return value

            # Skip tracking during serialization (performance optimization)
            import context.BaseObject

            if context.BaseObject._SKIP_USER_DATA_TRACKING:
                return value

            # Handle user_data access (both empty and non-empty)
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
                    # Convert both empty and non-empty dicts for consistency
                    if isinstance(value, dict) and not isinstance(value, TrackedDict):
                        tracked = TrackedDict(owner=self)
                        if value:  # Only update if non-empty
                            tracked.update(value)
                        object.__setattr__(self, "user_data", tracked)
                        value = tracked

                    # Check for nested changes (only if non-empty TrackedDict)
                    if value and isinstance(value, TrackedDict):
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
        # With dict-backed storage, check the _separate_items class attribute
        # (This was previously stored in dataclass field metadata)
        return key in self._separate_items

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
        elif isinstance(v, dict) and set(v.keys()) == {"x", "y", "angle"}:
            # Position dict - serialize as [x, y, angle] list
            stream.write(b"[")
            stream.write(str(v["x"]).encode())
            stream.write(b", ")
            stream.write(str(v["y"]).encode())
            stream.write(b", ")
            stream.write(str(v["angle"]).encode())
            stream.write(b"]")
        elif isinstance(v, dict) and set(v.keys()) == {"r", "g", "b", "a"}:
            # Color dict - serialize as [r, g, b, a] list
            stream.write(b"[")
            stream.write(str(v["r"]).encode())
            stream.write(b", ")
            stream.write(str(v["g"]).encode())
            stream.write(b", ")
            stream.write(str(v["b"]).encode())
            stream.write(b", ")
            stream.write(str(v["a"]).encode())
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

        # With dict-backed storage, iterate _data directly
        # Skip internal tracking fields and empty values
        # Note: Back-references like Master.font are no longer in _data
        skip_keys = {
            "_dirty_flags",
            "_dirty_fields",
            "_parent_ref",
            "_user_data_snapshot",
            "_skip_user_data_check",
            "_tracking_enabled",
        }

        for k, v in self._data.items():
            # Skip internal fields and user_data (handled separately)
            if k in skip_keys or k == "_":
                continue
            # Skip empty values
            if not v and not isinstance(v, (int, float, bool)):
                continue
            # _data already contains file format names, no alias needed
            towrite.append((k, v))

        for ix, (k, v) in enumerate(towrite):
            if not self._write_one_line:
                stream.write(b"\n")
                stream.write(b"  " * (indent + 1))

            stream.write('"{0}": '.format(k).encode())
            self._write_value(stream, k, v, indent)
            if ix != len(towrite) - 1:
                stream.write(b", ")

        if self.user_data:
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

    def _convert_value_to_dict(self, v):
        """Convert a value to a dict-compatible representation."""
        if hasattr(v, "to_dict"):
            return v.to_dict()
        elif isinstance(v, tuple):
            return [self._convert_value_to_dict(entry) for entry in v]
        elif isinstance(v, dict):
            result = {}
            for k1, v1 in v.items():
                # Handle tuple keys (e.g., kerning keys)
                if not isinstance(k1, str):
                    dict_key = "//".join(k1)
                else:
                    dict_key = k1
                result[dict_key] = self._convert_value_to_dict(v1)
            return result
        elif isinstance(v, list):
            return [self._convert_value_to_dict(item) for item in v]
        elif isinstance(v, datetime.datetime):
            # Format without microseconds to match loader expectation
            return v.strftime("%Y-%m-%d %H:%M:%S")
        else:
            # Return primitive types as-is
            return v

    def to_dict(self):
        """
        Return dictionary representation.

        _data contains ONLY serializable data (dicts, lists, primitives).
        However, when dirty tracking is enabled, _data becomes a TrackedDict
        with shared references to other TrackedDict objects. We must convert
        these back to plain dicts for efficient serialization.

        Returns:
            dict: Plain dictionary representation (no TrackedDict objects)
        """

        # CRITICAL INSTRUCTION:
        # With dict-backed storage, _data already contains serializable data.
        # Never override this method to build dicts on-the-fly from properties,
        # but instead implement property getters/setters that convert to/from dicts.

        def _convert_to_plain_dict(obj):
            """Recursively convert TrackedDict instances to plain dicts."""
            if isinstance(obj, TrackedDict):
                # Convert TrackedDict to plain dict, recursively converting nested TrackedDicts
                return {k: _convert_to_plain_dict(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                # Recursively convert list items
                return [_convert_to_plain_dict(item) for item in obj]
            elif isinstance(obj, dict) and not isinstance(obj, I18NDictionary):
                # Convert any other dict subclass to plain dict
                return {k: _convert_to_plain_dict(v) for k, v in obj.items()}
            else:
                # Primitives, I18NDictionary, and other objects pass through
                return obj

        # If _data is a TrackedDict (dirty tracking enabled), convert to plain dict
        # Otherwise (plain dict), just return a shallow copy for safety
        if isinstance(self._data, TrackedDict):
            return _convert_to_plain_dict(self._data)
        else:
            return dict(self._data)

    @classmethod
    def from_dict(cls, data, _copy=True, _validate=True):
        """
        Create an instance from a dictionary representation.
        This is the inverse of to_dict().

        Args:
            data: Dictionary with object data
            _copy: If True, deep copy the data to prevent mutation.
                   Set to False when loading from disk for performance.
            _validate: If False, skip required field validation for performance.
                      Set to False when loading from disk.

        Returns:
            Instance of the class
        """
        if not isinstance(data, dict):
            return data

        # Deep copy nested lists/dicts to prevent mutation during round-trips
        # Skip copy when loading from disk (_copy=False) for performance
        if _copy:
            import copy

            data = copy.deepcopy(data)

        instance = cls(_data=data, _validate=_validate)

        return instance
