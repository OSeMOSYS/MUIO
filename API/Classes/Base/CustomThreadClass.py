from collections.abc import Callable, Iterable, Mapping
from threading import Thread
from typing import Any

class CustomThread(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, Verbose=None):
        if kwargs is None:
            kwargs = {}

        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, *args, **kwargs):
        Thread.join(self, *args, **kwargs)
        return self._return
