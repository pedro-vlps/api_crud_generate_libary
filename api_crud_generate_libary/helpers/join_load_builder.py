"""Sencondary level joins helper functions file"""
from sqlalchemy.orm import joinedload

def build_joinedload_chain(path_list):
    """
    Takes a list of relationship attribute names
    and chains them using joinedload().

    Args:
        path_list (list): A list of strings representing
        the names of relationships to be eagerly loaded.

    Returns:
        sqlalchemy.orm.Load: A chained joinedload
        object for use in SQLAlchemy queries.
    """
    loader = joinedload(path_list[0])
    for attr in path_list[1:]:
        loader = loader.joinedload(attr)
    return loader
