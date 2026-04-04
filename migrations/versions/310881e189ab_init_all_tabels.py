"""init all tabels

Revision ID: 310881e189ab
Revises: 
Create Date: 2026-03-18 20:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '310881e189ab'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Создаём таблицу users
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('password_hash', sa.String(), nullable=True),
        sa.Column('salt', sa.String(), nullable=True),
        sa.Column('yandex_id', sa.String(), nullable=True),
        sa.Column('vk_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reset_password_token', sa.String(), nullable=True),
        sa.Column('reset_password_expires', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_phone', 'users', ['phone'], unique=True)
    op.create_index('ix_users_reset_password_token', 'users', ['reset_password_token'], unique=False)
    op.create_index('ix_users_vk_id', 'users', ['vk_id'], unique=True)
    op.create_index('ix_users_yandex_id', 'users', ['yandex_id'], unique=True)

    # Создаём таблицу tokens
    op.create_table('tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('access_token_hash', sa.String(), nullable=False),
        sa.Column('refresh_token_hash', sa.String(), nullable=False),
        sa.Column('access_expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('refresh_expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tokens_id', 'tokens', ['id'], unique=False)

    # Создаём таблицу tests
    op.create_table('tests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tests_id', 'tests', ['id'], unique=False)

    # Создаём таблицу questions
    op.create_table('questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('test_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['test_id'], ['tests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_questions_id', 'questions', ['id'], unique=False)

    # Создаём таблицу answer_options
    op.create_table('answer_options',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('question_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_answer_options_id', 'answer_options', ['id'], unique=False)

    # Создаём таблицу test_results
    op.create_table('test_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('test_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('correct_answers', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_questions', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=True, server_default='in_progress'),
        sa.ForeignKeyConstraint(['test_id'], ['tests.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_test_results_id', 'test_results', ['id'], unique=False)

    # Создаём таблицу user_answers
    op.create_table('user_answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('result_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('selected_answer_id', sa.Integer(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.ForeignKeyConstraint(['result_id'], ['test_results.id'], ),
        sa.ForeignKeyConstraint(['selected_answer_id'], ['answer_options.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_answers_id', 'user_answers', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_user_answers_id', table_name='user_answers')
    op.drop_table('user_answers')
    op.drop_index('ix_test_results_id', table_name='test_results')
    op.drop_table('test_results')
    op.drop_index('ix_answer_options_id', table_name='answer_options')
    op.drop_table('answer_options')
    op.drop_index('ix_questions_id', table_name='questions')
    op.drop_table('questions')
    op.drop_index('ix_tests_id', table_name='tests')
    op.drop_table('tests')
    op.drop_index('ix_tokens_id', table_name='tokens')
    op.drop_table('tokens')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_phone', table_name='users')
    op.drop_index('ix_users_reset_password_token', table_name='users')
    op.drop_index('ix_users_vk_id', table_name='users')
    op.drop_index('ix_users_yandex_id', table_name='users')
    op.drop_table('users')