from typing import Optional, Tuple
import datetime
from time_util import today


def parse_since_until_n(
    since: Optional[datetime.date] = None,
    until: Optional[datetime.date] = None,
    n: Optional[int] = None,
    n_buffer: int = 0,
) -> Tuple[datetime.date, datetime.date]:
    if n is None:
        if since is None:
            raise ValueError('Must pass at least one of since, n')

        if until is None:
            until = today()

        return since, until

    if since is not None or until is not None:
        raise ValueError('Cannot pass n and since or until')

    until = today() - datetime.timedelta(days=n_buffer)
    since = until - datetime.timedelta(days=n - 1)

    return since, until
