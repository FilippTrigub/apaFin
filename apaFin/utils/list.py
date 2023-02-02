from typing import List
from typing import TypeVar

__CHUNK_LIST_ITEM_TYPE = TypeVar("__CHUNK_LIST_ITEM_TYPE")


def chunk(l: List[__CHUNK_LIST_ITEM_TYPE], size: int) -> List[__CHUNK_LIST_ITEM_TYPE]:
    """
    split a list into the given chunk size
    :param l: input list
    :param size: output chunk size
    :return:
    """
    for i in range(0, len(l), size):
        yield l[i:i + size]
