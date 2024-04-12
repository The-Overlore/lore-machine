# NpcDatabase
class NpcProfileNotFoundError(Exception):
    """Exception raised when an NPC is not found in the database."""

    pass


class NpcDescriptionNotFoundError(Exception):
    """Exception raised during a failed insertion of an NPC."""

    pass


class NpcProfileNotDeleted(Exception):
    """Exception raised during a failed insertion of an NPC."""

    pass


# DiscussionDatabase
class CosineSimilarityNotFoundError(Exception):
    """Exception raised during a cosine similarity search."""

    pass
