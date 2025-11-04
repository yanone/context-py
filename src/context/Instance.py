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
            # Convert customNames if it's a dict
            if "customNames" in _data and isinstance(_data["customNames"], dict):
                _data["customNames"] = Names.from_dict(_data["customNames"])
            super().__init__(_data=_data)
        else:
            # Convert name to I18NDictionary if needed
            if isinstance(name, str):
                name = I18NDictionary.with_default(name)
            elif isinstance(name, dict) and not isinstance(name, I18NDictionary):
                i18n = I18NDictionary()
                i18n.update(name)
                name = i18n

            data = {
                "name": name,
                "location": location,
                "variable": variable,
                "customNames": customNames or Names(),
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
            self.mark_dirty()

    @property
    def location(self):
        return self._data.get("location")

    @location.setter
    def location(self, value):
        self._data["location"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def variable(self):
        return self._data.get("variable", False)

    @variable.setter
    def variable(self, value):
        self._data["variable"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def customNames(self):
        names = self._data.get("customNames")
        if isinstance(names, dict) and not isinstance(names, Names):
            names = Names.from_dict(names)
            self._data["customNames"] = names
        return names or Names()

    @customNames.setter
    def customNames(self, value):
        self._data["customNames"] = value
        if self._tracking_enabled:
            self.mark_dirty()

    @property
    def localisedStyleName(self):
        return (
            self.customNames.styleName.as_fonttools_dict or self.name.as_fonttools_dict
        )

    @property
    def postScriptFontName(self):
        return self.customNames.postscriptName.as_fonttools_dict

    def to_dict(self, use_cache=True):
        """
        Convert instance to dictionary, properly serializing customNames.
        """
        result = super().to_dict(use_cache=use_cache)

        # Serialize customNames if it's a Names object
        if "customNames" in result and isinstance(result["customNames"], Names):
            result["customNames"] = result["customNames"].to_dict(use_cache=use_cache)

        return result
