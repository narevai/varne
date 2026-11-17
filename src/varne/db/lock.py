import threading
from collections.abc import Callable
from functools import wraps

db_lock = threading.RLock()


def serialized[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        with db_lock:
            return fn(*args, **kwargs)

    return wrapper
