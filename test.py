#!/usr/bin/python3

import id3
import os
import random
import warnings
import sys

warnings.simplefilter("always", id3.Warning)

#start = r"S:\Music\Instrumental\Mike Oldfield - 1998 Tubular Bells III"
w1 = r"C:\Users\lorentey\Music"
w2 = r"S:\Music"
root3 = r"."
l4 = r"/data/public/Music"

def list_mp3s(roots):
    for root in roots:
        if root.endswith(".mp3"):
            yield root
        else:
            for root, dirs, files in os.walk(root):
                dirs.sort()
                for file in sorted(files):
                    if file.endswith(".mp3"):
                        yield os.path.join(root, file)

def head(iterable, limit):
    if limit is None:
        for elem in iterable:
            yield elem
    else:
        for elem, i in zip(iterable, range(limit)):
            yield elem

def test(*roots, wait=False, randomize=False, limit=None):
    mp3s = list_mp3s(roots)

    if randomize:
        mp3s = list(mp3s)
        print("{0} files found".format(len(mp3s)))
        random.shuffle(mp3s)

    for mp3 in head(mp3s, limit):
        try:
            print(mp3)
            with id3.read(mp3) as tag:
                print(tag)
                last = None
                for frame in tag.frames():
                    #if type(frame) in [id3.ErrorFrame, id3.UnknownFrame]:
                    #    if last != mp3:
                    #        print(mp3)
                    #        last = mp3
                    print("    " + str(frame))
        except id3.NoTagError:
            pass
        except Exception as e:
            print("{0}: {1} {2}".format(mp3, type(e).__name__, str(e)))
        if wait: input()

