"""Bounded five-minute cache for this read-only dashboard process."""
from collections import OrderedDict
from concurrent.futures import Future
from copy import deepcopy
from functools import wraps
import json
from threading import Lock
from time import monotonic

TTL = 300
MAX_ENTRIES = 64
_entries = OrderedDict()
_pending = {}
_lock = Lock()


def cached(function):
    @wraps(function)
    def load(*args, **kwargs):
        key = (function.__module__, function.__qualname__,
               json.dumps([args, kwargs], sort_keys=True, default=str))
        with _lock:
            now = monotonic()
            for expired in [k for k, (deadline, _) in _entries.items() if deadline <= now]:
                del _entries[expired]
            if key in _entries:
                _entries.move_to_end(key)
                return deepcopy(_entries[key][1])
            owner = key not in _pending
            if owner:
                _pending[key] = Future()
            pending = _pending[key]
        if not owner:
            return deepcopy(pending.result())
        try:
            result = function(*args, **kwargs)
            with _lock:
                _entries[key] = (monotonic() + TTL, deepcopy(result))
                while len(_entries) > MAX_ENTRIES:
                    _entries.popitem(last=False)
            pending.set_result(result)
            return deepcopy(result)
        except Exception as error:
            pending.set_exception(error)
            raise
        finally:
            with _lock:
                del _pending[key]
    return load
