from .BaseObject import BaseObject, I18NDictionary
from .Names import Names


class Instance(BaseObject):
    """An object representing a named or static instance."""

    _write_one_line = True

    def __init__(
        self,
        name=None,
        location=None,
        variable=False,
        customNames=None,
        _data=None,
        **kwargs,
    ):
        """Initialize Instance with dict-backed storage."""
        if _data is not None:
            # Convert name if it's a dict
            if "name" in _data and isinstance(_data["name"], dict):
                if not isinstance(_data["name"], I18NDictionary):
                    i18n = I18NDictionary()
                    i18n.update(_data["name"])
                    _data["name"] = i18n
            # Ensure customNames is a dict (serialize Names objects)
            if "customNames" in _data and isinstance(_data["customNames"], Names):
                _data["customNames"] = _data["customNames"].to_dict()
            super().__init__(_data=_data)
        else:
            # Convert name to I18NDictionary if needed
            if isinstance(name, str):
                name = I18NDictionary.with_default(name)
            elif isinstance(name, dict) and not isinstance(name, I18NDictionary):
                i18n = I18NDictionary()
                i18n.update(name)
                name = i18n

            # Serialize customNames to dict
            if customNames and isinstance(customNames, Names):
                customNames = customNames.to_dict()
            elif not customNames:
                customNames = {}

            data = {
                "name": name,
                "location": location,
                "variable": variable,
                "customNames": customNames,
            }
            data.update(kwargs)
            super().__init__(_data=data)

    @property
    def name(self):
        name = self._data.get("name")
        if isinstance(name, dict) and not isinstance(name, I18NDictionary):
            i18n = I18NDictionary()
            i18n.update(name)
            self._data["name"] = i18n
            name = i18n
        return name

    @name.setter
    def name(self, value):
        if isinstance(value, str):
            value = I18NDictionary.with_default(value)
        self._data["name"] = value
        if self._tracking_enabled:
            self.mark_dirty(field_name="name")

    @property
    def location(self):
        return self._data.get("location")

    @location.setter
    def location(self, value):
        self._data["location"] = value
        if self._tracking_enabled:
            self.mark_dirty(field_name="location")

    @property
    def variable(self):
        return self._data.get("variable", False)

    @variable.setter
    def variable(self, value):
        self._data["variable"] = value
        if self._tracking_enabled:
            self.mark_dirty(field_name="variable")

    @property
    def customNames(self):
        """Return Names object, but keep _data as dict for serialization."""
        names = self._data.get("customNames")
        if isinstance(names, dict) and not isinstance(names, Names):
            # Convert to Names for returning, but DON'T store back in _data
            names = Names.from_dict(names)
        return names or Names()

    @customNames.setter
    def customNames(self, value):
        # Serialize customNames if it's a Names object
        if value and isinstance(value, Names):
            self._data["customNames"] = value.to_dict()
        else:
            self._data["customNames"] = value
        if self._tracking_enabled:
            self.mark_dirty(field_name="customNames")

    @property
    def localisedStyleName(self):
        return (
            self.customNames.styleName.as_fonttools_dict or self.name.as_fonttools_dict
        )

    @property
    def postScriptFontName(self):
        return self.customNames.postscriptName.as_fonttools_dict
