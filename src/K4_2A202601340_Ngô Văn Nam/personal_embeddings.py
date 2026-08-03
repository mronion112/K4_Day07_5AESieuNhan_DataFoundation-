"""Backend embedding được cố định cho benchmark cá nhân."""

from ..embeddings import MockEmbedder


class PersonalMockEmbedder(MockEmbedder):
    """Mock deterministic để kiểm pipeline; không biểu diễn ngữ nghĩa."""

    _backend_name = "personal deterministic MockEmbedder"
