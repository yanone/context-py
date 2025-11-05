import logging

from context.fontFilters import parse_filter

logger = logging.getLogger(__name__)


class BaseConvertor:
    filename: str
    scratch: object
    font: "Font"  # Type hint only, avoid circular import
    compile_only: bool

    suffix = ".XXX"

    LOAD_FILTERS = []
    COMPILE_FILTERS = []
    SAVE_FILTERS = []

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @classmethod
    def can_load(cls, other, **kwargs):
        return other.filename.endswith(cls.suffix)

    @classmethod
    def can_save(cls, other, **kwargs):
        return other.filename.endswith(cls.suffix)

    @classmethod
    def load(cls, convertor, compile_only=False, filters=True, _validate=True):
        from context.Font import Font

        self = cls()
        self.font = Font()
        # Pass on information to child
        self.filename = convertor.filename
        self.scratch = convertor.scratch
        self.compile_only = compile_only
        self._validate = _validate  # Store for use in _load
        loaded = self._load()
        if filters:
            for f in cls.LOAD_FILTERS:
                fltr, filterargs = parse_filter(f)
                fltr(loaded, filterargs)

        return loaded

    @classmethod
    def save(cls, obj, convertor, **kwargs):
        self = cls()
        self.font = obj
        # Pass on information to child
        self.filename = convertor.filename
        self.scratch = convertor.scratch
        return self._save(**kwargs)

    def _load(self):
        raise NotImplementedError

    def _save(self):
        raise NotImplementedError


class Convert:
    def __init__(self, filename):
        self.filename = filename
        self.scratch = {}

    def load_convertor(self, **kwargs):
        from context.convertors.nfsf import Context

        if Context.can_load(self, **kwargs):
            return Context
        return None

    def save_convertor(self, **kwargs):
        from context.convertors.nfsf import Context

        if Context.can_save(self, **kwargs):
            return Context
        return None

    def load(self, **kwargs):
        c = self.load_convertor(**kwargs)
        if not c:
            logger.error("Could not find a convertor from %s", self.filename)
            raise NotImplementedError
        return c.load(self, **kwargs)

    def save(self, obj, **kwargs):
        c = self.save_convertor(**kwargs)
        if not c:
            logger.error("Could not find a convertor to %s", self.filename)
            raise NotImplementedError
        return c.save(obj, self, **kwargs)
