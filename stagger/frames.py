# Copyright (c) 2009, Karoly Lorentey  <karoly@lorentey.hu>

"""Class definitions for ID3v2 frames."""

import abc
import collections
from abc import abstractmethod

from stagger.specs import *

class Frame(metaclass=abc.ABCMeta):
    _framespec = tuple()
    _version = tuple()
    _allow_duplicates = False
    
    def __init__(self, frameid=None, flags=None, **kwargs):
        self.frameid = frameid if frameid else type(self).__name__
        self.flags = flags if flags else {}
        for spec in self._framespec:
            val = kwargs.get(spec.name, None)
            if val != None: spec.validate(self, val)
            setattr(self, spec.name, val)

    @classmethod
    def _from_data(cls, frameid, data, flags=None):
        frame = cls(frameid, flags)
        if getattr(frame, "_untested", False):
            warn("Support for {0} is untested; please verify results".format(frameid), 
                 UntestedFrameWarning)
        for spec in frame._framespec:
            val, data = spec.read(frame, data)
            setattr(frame, spec.name, val)
        return frame

    @classmethod
    def _from_frame(cls, frame):
        "Copy constructor"
        assert frame._framespec == cls._framespec
        new = cls(flags=frame.flags)
        for spec in cls._framespec:
            setattr(new, spec.name, getattr(frame, spec.name, None))
        return new

    @classmethod
    def _merge(cls, frames):
        if cls._allow_duplicates:
            return frames
        else:
            if len(frames) > 1:
                warn("Frame {0} duplicated, only the last instance is kept".format(frames[0].frameid))
            return frames[-1:]

    @classmethod
    def _in_version(self, *versions):
        "Returns true if this frame is defined in any of the specified versions of ID3."
        for version in version:
            if (self._version == version
                or (isinstance(self._version, collections.Container) 
                    and version in self._version)):
                return True
        return False

    def _to_version(self, version):
        if self._in_version(version):
            return self
        if version == 2 and hasattr(self, "_v2_frame"):
            return self._v2_frame._from_frame(self)
        if self._in_version(2):
            base = type(self).__bases__[0]
            if issubclass(base, Frame) and base._in_version(version): 
                return base._from_frame(self)
        raise IncompatibleFrameError("Frame {0} cannot be converted to ID3v2.{1} format".format(self.frameid, version))

    def _to_data(self):
        if getattr(self, "_bozo", False):
            warn("General support for frame {0} is virtually nonexistent; its use is discouraged".format(self.frameid), BozoFrameWarning)
        
        def encode():
            data = bytearray()
            for spec in self._framespec:
                data.extend(spec.write(self, getattr(self, spec.name)))
            return data

        def try_preferred_encodings():
            for encoding in EncodedStringSpec.preferred_encodings:
                try:
                    self.encoding = encoding
                    return encode()
                except UnicodeEncodeError:
                    pass
                finally:
                    self.encoding = None
            raise ValueError("Could not encode strings")
        
        if isinstance(self._framespec[0], EncodingSpec) and self.encoding == None:
            return try_preferred_encodings()
        else:
            try:
                return encode()
            except UnicodeEncodeError:
                return try_preferred_encodings()

    def __repr__(self):
        stype = type(self).__name__
        args = []
        if stype != self.frameid:
            args.append("frameid={0!r}".format(self.frameid))
        if self.flags:
            args.append("flags={0!r}".format(self.flags))
        args.extend("{0}={1!r}".format(spec.name, getattr(self, spec.name)) for spec in self._framespec)
        return "{0}({1})".format(stype, ", ".join(args))

    def _str_fields(self):
        fields = []
        for spec in self._framespec:
            fields.append(spec.to_str(getattr(self, spec.name, None)))
        return ", ".join(fields)
        
    def __str__(self):
        flag = " "
        if "unknown" in self.flags: flag = "?"
        if isinstance(self, ErrorFrame): flag = "!"
        return "{0}{1}({2})".format(flag, self.frameid, self._str_fields())

class UnknownFrame(Frame):
    _framespec = (BinaryDataSpec("data"),)

class ErrorFrame(Frame):
    _framespec = (BinaryDataSpec("data"),)

    def __init__(self, frameid, data, exception, **kwargs):
        super().__init__(frameid, {}, **kwargs)
        self.data = data
        self.exception = exception

    def _str_fields(self):
        strs = ["ERROR"]
        if self.exception:
            strs.append(str(self.exception))
        strs.append(repr(self.data))
        return ", ".join(strs)
    
    
class TextFrame(Frame):
    _framespec = (EncodingSpec("encoding"),
                  SequenceSpec("text", EncodedStringSpec("text")))
    def _str_fields(self):
        return "{0} {1}".format(EncodedStringSpec._encodings[self.encoding][0],
                                ", ".join(repr(t) for t in self.text))

    @classmethod
    def _merge(cls, frames):
        frame = cls(text=[])
        for f in frames:
            frame.text.extend(f.text)
        return [frame]

class URLFrame(Frame):
    _framespec = (URLStringSpec("url"), )
    def _str_fields(self):
        return repr(self.url)

class CreditsFrame(Frame):
    _framespec = (EncodingSpec("encoding"),
                  MultiSpec("people",
                            EncodedStringSpec("involvement"),
                            EncodedStringSpec("person")))


def gen_frame_classes(module=None):
    "A generator for all frame classes in the specified module."
    d = module.__dict__ if module else globals()
    for obj in d.values():
        if (isinstance(obj, type)
            and issubclass(obj, Frame)
            and 3 <= len(obj.__name__) <= 4
            and obj.__name__ == obj.__name__.upper()):
            yield obj

