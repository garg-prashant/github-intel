"""Switch repo_embeddings to 384-dim for local (sentence-transformers) embeddings.

Revision ID: 20250209180000
Revises: 20250209000000
Create Date: 2025-02-09

"""
from typing import Sequence, Union

from alembic import op

revision: str = "20250209180000"
down_revision: Union[str, None] = "20250209000000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("TRUNCATE TABLE repo_embeddings")
    op.drop_index("ix_repo_embeddings_embedding_hnsw", table_name="repo_embeddings")
    op.execute("ALTER TABLE repo_embeddings DROP COLUMN embedding")
    op.execute("ALTER TABLE repo_embeddings ADD COLUMN embedding vector(384) NOT NULL")
    op.execute(
        "CREATE INDEX ix_repo_embeddings_embedding_hnsw ON repo_embeddings "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.execute("TRUNCATE TABLE repo_embeddings")
    op.drop_index("ix_repo_embeddings_embedding_hnsw", table_name="repo_embeddings")
    op.execute("ALTER TABLE repo_embeddings DROP COLUMN embedding")
    op.execute("ALTER TABLE repo_embeddings ADD COLUMN embedding vector(1536) NOT NULL")
    op.execute(
        "CREATE INDEX ix_repo_embeddings_embedding_hnsw ON repo_embeddings "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )