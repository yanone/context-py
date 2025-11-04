from .BaseObject import BaseObject, I18NDictionary

OPENTYPE_NAMES = [
    "copyright",
    "familyName",
    "preferredSubfamilyName",
    "uniqueID",
    "fullName",  # XXX?
    "version",
    "postscriptName",
    "trademark",
    "manufacturer",
    "designer",
    "description",
    "manufacturerURL",
    "designerURL",
    "license",
    "licenseURL",
    "reserved",
    "typographicFamily",
    "typographicSubfamily",
    "compatibleFullName",
    "sampleText",
    "postscriptCIDname",  # XXX?
    "WWSFamilyName",
    "WWSSubfamilyName",
]

NAME_FIELDS = [
    "familyName",
    "styleName",
    "copyright",
    "styleMapFamilyName",
    "styleMapStyleName",
    "uniqueID",
    "fullName",
    "version",
    "postscriptName",
    "trademark",
    "manufacturer",
    "designer",
    "description",
    "manufacturerURL",
    "designerURL",
    "license",
    "licenseURL",
    "typographicFamily",
    "typographicSubfamily",
    "compatibleFullName",
    "sampleText",
    "WWSFamilyName",
    "WWSSubfamilyName",
]


class Names(BaseObject):
    """A table of global, localizable names for the font."""

    def __init__(self, _data=None, **kwargs):
        """Initialize Names with dict-backed storage."""
        if _data is not None:
            # Convert dict values back to I18NDictionary
            for key, value in _data.items():
                if key == "_":
                    continue
                if isinstance(value, dict) and not isinstance(value, I18NDictionary):
                    i18n = I18NDictionary()
                    i18n.update(value)
                    _data[key] = i18n
                elif isinstance(value, str):
                    _data[key] = I18NDictionary.with_default(value)
            super().__init__(_data=_data)
        else:
            # Initialize all name fields with I18NDictionary
            data = {}
            for field in NAME_FIELDS:
                value = kwargs.pop(field, None)
                if value is None:
                    value = I18NDictionary()
                elif isinstance(value, str):
                    value = I18NDictionary.with_default(value)
                elif isinstance(value, dict) and not isinstance(value, I18NDictionary):
                    i18n = I18NDictionary()
                    i18n.update(value)
                    value = i18n
                data[field] = value
            data.update(kwargs)
            super().__init__(_data=data)

    def __getattr__(self, name):
        """Provide access to name fields."""
        if name.startswith("_"):
            msg = f"'{type(self).__name__}' object has no attribute '{name}'"
            raise AttributeError(msg)
        # Return value from _data, default to empty I18NDictionary
        value = self._data.get(name)
        if value is None and name in NAME_FIELDS:
            value = I18NDictionary()
            self._data[name] = value
        return value

    def __setattr__(self, name, value):
        """Set name field values."""
        if name.startswith("_") or name in ("mark_dirty", "mark_clean"):
            object.__setattr__(self, name, value)
        else:
            self._data[name] = value
            if self._tracking_enabled:
                self.mark_dirty(field_name=name)

    def as_nametable_dict(self):
        rv = {}
        ft_names = {
            "manufacturerURL": "vendorURL",
            "license": "licenseDescription",
            "licenseURL": "licenseInfoURL",
        }
        for k, v in self._data.items():
            if k == "_" or not v:
                continue
            rv[ft_names.get(k, k)] = v.default_or_dict()
        return rv

    def __getitem__(self, key):
        try:
            key = int(key)
        except ValueError as exc:
            raise ValueError("Name ID must be an integer") from exc
        if key == 0:
            return self.copyright
        if key == 1:
            return self.styleMapFamilyName or self.familyName
        if key == 2:
            return self.styleMapStyleName
        if key == 3:
            return self.uniqueID
        if key == 4:
            return self.fullName
        if key == 5:
            return self.version
        if key == 6:
            return self.postscriptName
        if key == 7:
            return self.trademark
        if key == 8:
            return self.manufacturer
        if key == 9:
            return self.designer
        if key == 10:
            return self.description
        if key == 11:
            return self.manufacturerURL
        if key == 12:
            return self.designerURL
        if key == 13:
            return self.license
        if key == 14:
            return self.licenseURL
        if key == 16:
            return self.typographicFamily
        if key == 17:
            return self.typographicSubfamily or self.styleName
        if key == 18:
            return self.compatibleFullName
        if key == 19:
            return self.sampleText
        if key == 21:
            return self.WWSFamilyName
        if key == 22:
            return self.WWSSubfamilyName
        return None
