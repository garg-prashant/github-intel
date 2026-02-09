"""Initial schema: extension, repositories, trend_snapshots, categories, content, embeddings.

Revision ID: 20250209000000
Revises:
Create Date: 2025-02-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "20250209000000"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "repositories",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("github_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("owner", sa.String(128), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("html_url", sa.String(512), nullable=False),
        sa.Column("homepage_url", sa.String(512), nullable=True),
        sa.Column("primary_language", sa.String(64), nullable=True),
        sa.Column("languages_json", sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("topics", sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("license_spdx", sa.String(64), nullable=True),
        sa.Column("has_readme", sa.Boolean(), default=False, nullable=False),
        sa.Column("readme_content", sa.Text(), nullable=True),
        sa.Column("stars_count", sa.Integer(), default=0, nullable=False),
        sa.Column("forks_count", sa.Integer(), default=0, nullable=False),
        sa.Column("open_issues_count", sa.Integer(), default=0, nullable=False),
        sa.Column("watchers_count", sa.Integer(), default=0, nullable=False),
        sa.Column("default_branch", sa.String(64), default="main", nullable=False),
        sa.Column("created_at_gh", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pushed_at_gh", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_fork", sa.Boolean(), default=False, nullable=False),
        sa.Column("is_archived", sa.Boolean(), default=False, nullable=False),
        sa.Column("is_mirror", sa.Boolean(), default=False, nullable=False),
        sa.Column("current_trend_score", sa.Float(), nullable=True),
        sa.Column("quality_passed", sa.Boolean(), default=False, nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_repositories_github_id", "repositories", ["github_id"], unique=True)
    op.create_index("ix_repositories_full_name", "repositories", ["full_name"], unique=True)
    op.create_index("ix_repositories_pushed_at_gh", "repositories", ["pushed_at_gh"], unique=False)
    op.create_index("ix_repositories_quality_passed", "repositories", ["quality_passed"], unique=False)
    op.create_index("ix_repositories_current_trend_score", "repositories", ["current_trend_score"], unique=False)
    op.create_index(
        "ix_repositories_quality_score",
        "repositories",
        ["quality_passed", "current_trend_score"],
        unique=False,
        postgresql_ops={"current_trend_score": "DESC"},
    )
    op.create_index(
        "ix_repositories_topics",
        "repositories",
        ["topics"],
        unique=False,
        postgresql_using="gin",
    )

    op.create_table(
        "trend_snapshots",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("repository_id", sa.BigInteger(), nullable=False),
        sa.Column("stars_count", sa.Integer(), nullable=False),
        sa.Column("forks_count", sa.Integer(), nullable=False),
        sa.Column("open_issues_count", sa.Integer(), nullable=False),
        sa.Column("watchers_count", sa.Integer(), nullable=False),
        sa.Column("stars_delta_1h", sa.Integer(), nullable=True),
        sa.Column("stars_delta_24h", sa.Integer(), nullable=True),
        sa.Column("forks_delta_24h", sa.Integer(), nullable=True),
        sa.Column("commits_7d", sa.Integer(), nullable=True),
        sa.Column("issue_events_7d", sa.Integer(), nullable=True),
        sa.Column("computed_trend_score", sa.Float(), nullable=True),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_trend_snapshots_repo_snapshot",
        "trend_snapshots",
        ["repository_id", "snapshot_at"],
        unique=False,
    )
    op.create_index("ix_trend_snapshots_snapshot_at", "trend_snapshots", ["snapshot_at"], unique=False)

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("keywords", sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)

    op.create_table(
        "repository_categories",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("repository_id", sa.BigInteger(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("classification_method", sa.String(32), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repository_id", "category_id", name="uq_repository_category_repo_cat"),
    )

    op.create_table(
        "generated_content",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("repository_id", sa.BigInteger(), nullable=False),
        sa.Column("content_type", sa.String(32), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("llm_provider", sa.String(32), nullable=False),
        sa.Column("llm_model", sa.String(64), nullable=False),
        sa.Column("prompt_version", sa.String(16), nullable=False),
        sa.Column("token_usage", sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "repository_id", "content_type", "prompt_version",
            name="uq_generated_content_repo_type_version",
        ),
    )

    op.create_table(
        "repo_embeddings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("repository_id", sa.BigInteger(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("embedding_model", sa.String(64), nullable=False),
        sa.Column("source_text_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repository_id", name="uq_repo_embeddings_repository_id"),
    )
    op.create_index(
        "ix_repo_embeddings_repository_id",
        "repo_embeddings",
        ["repository_id"],
        unique=True,
    )
    op.execute(
        "CREATE INDEX ix_repo_embeddings_embedding_hnsw ON repo_embeddings "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.drop_index("ix_repo_embeddings_embedding_hnsw", table_name="repo_embeddings")
    op.drop_index("ix_repo_embeddings_repository_id", table_name="repo_embeddings")
    op.drop_table("repo_embeddings")
    op.drop_table("generated_content")
    op.drop_table("repository_categories")
    op.drop_index("ix_categories_slug", table_name="categories")
    op.drop_table("categories")
    op.drop_index("ix_trend_snapshots_snapshot_at", table_name="trend_snapshots")
    op.drop_index("ix_trend_snapshots_repo_snapshot", table_name="trend_snapshots")
    op.drop_table("trend_snapshots")
    op.drop_index("ix_repositories_topics", table_name="repositories")
    op.drop_index("ix_repositories_quality_score", table_name="repositories")
    op.drop_index("ix_repositories_current_trend_score", table_name="repositories")
    op.drop_index("ix_repositories_quality_passed", table_name="repositories")
    op.drop_index("ix_repositories_pushed_at_gh", table_name="repositories")
    op.drop_index("ix_repositories_full_name", table_name="repositories")
    op.drop_index("ix_repositories_github_id", table_name="repositories")
    op.drop_table("repositories")
    op.execute("DROP EXTENSION IF EXISTS vector")
