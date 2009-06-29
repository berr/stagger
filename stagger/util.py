# Copyright (c) 2009, Karoly Lorentey  <karoly@lorentey.hu>

import stagger

def verb(verbose, *args, **kwargs):
    if verbose:
        print(*args, **kwargs)

def check_tag_data(data):
    "Raise a ValueError if DATA doesn't seem to be a well-formed ID3 tag."
    if len(data) < 10:
        raise ValueError("Tag too short")
    if data[0:3] != b"ID3":
        raise ValueError("Missing ID3 identifier")
    if data[3] >= 5 or data[4] != 0:
        raise ValueError("Unknown ID3 version")
    length = stagger.conversions.Syncsafe.decode(data[6:10]) + 10
    if len(data) != length:
        raise ValueError("Tag size mismatch")
    
def get_raw_tag_data(filename):
    "Return the ID3 tag in FILENAME as a raw byte string."
    with open(filename, "rb") as file:
        try:
            (cls, offset, length) = stagger.tags.detect_tag(file)
        except stagger.NoTagError:
            return bytes()
        file.seek(offset)
        return file.read(length)

def set_raw_tag_data(filename, data, act=True, verbose=False):
    "Replace the ID3 tag in FILENAME with DATA."
    check_tag_data(data)
    with open(filename, "rb+") as file:
        try:
            (cls, offset, length) = stagger.tags.detect_tag(file)
        except stagger.NoTagError:
            (offset, length) = (0, 0)
        if length > 0:
            verb(verbose, "{0}: replaced tag with {1} bytes of data"
                 .format(filename, len(data)))
        else:
            verb(verbose, "{0}: created tag with {1} bytes of data"
                 .format(filename, len(data)))
        if act:
            stagger.fileutil.replace_chunk(file, offset, length, data)

def set_frames(filename, valuedict, act=True, verbose=False):
    try:
        tag = stagger.read_tag(filename)
    except stagger.NoTagError:
        verb(verbose, "{0}: new ID3v2.{1} tag"
             .format(filename, stagger.default_tag.version))
        tag = stagger.default_tag()
    for (frameid, value) in valuedict.items():
        tag[frameid] = value
        verb(verbose, "{0}: {1}: set to {2}"
             .format(filename, frameid, str(tag[frameid])))
    if act:
        tag.write(filename)

def remove_frames(filename, frameids, act=True, verbose=False):
    try:
        tag = stagger.read_tag(filename)
    except stagger.NoTagError:
        verb(verbose, "{0}: no ID3 tag".format(filename))
        return

    for frameid in frameids:
        try:
            del tag[frameid]
            verb(verbose, "{0}: {1}: deleted".format(filename, frameid))
        except KeyError:
            verb(verbose, "{0}: {1}: not in file".format(filename, frameid))
    if act:
        tag.write(filename)
