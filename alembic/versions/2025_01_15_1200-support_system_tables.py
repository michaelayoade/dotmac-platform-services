"""Support System Tables - Complete Knowledge Base, Chat, and Enhanced Ticketing

Revision ID: 2025_01_15_1200_support_system_tables
Revises: 952b95951dab
Create Date: 2025-01-15 12:00:00.000000

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2025_01_15_1200_support_system_tables'
down_revision: Union[str, None] = '952b95951dab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all support system tables."""
    
    # Knowledge Base Tables
    
    # 1. Knowledge Articles Table
    op.create_table('knowledge_articles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('slug', sa.String(500), nullable=False),
        sa.Column('summary', sa.String(1000), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_html', sa.Text(), nullable=True),
        sa.Column('article_type', sa.String(), nullable=False, default='article'),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('subcategory', sa.String(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True, default=sa.text('\'[]\'::json')),
        sa.Column('status', sa.String(), nullable=False, default='draft'),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('author_id', sa.String(), nullable=False),
        sa.Column('author_name', sa.String(), nullable=False),
        sa.Column('reviewer_id', sa.String(), nullable=True),
        sa.Column('reviewer_name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('view_count', sa.Integer(), nullable=False, default=0),
        sa.Column('helpful_votes', sa.Integer(), nullable=False, default=0),
        sa.Column('unhelpful_votes', sa.Integer(), nullable=False, default=0),
        sa.Column('search_ranking', sa.Integer(), nullable=False, default=0),
        sa.Column('meta_description', sa.String(300), nullable=True),
        sa.Column('search_keywords', sa.JSON(), nullable=True, default=sa.text('\'[]\'::json')),
        sa.Column('external_links', sa.JSON(), nullable=True, default=sa.text('\'[]\'::json')),
        sa.Column('attachments', sa.JSON(), nullable=True, default=sa.text('\'[]\'::json')),
        sa.Column('related_tickets', sa.JSON(), nullable=True, default=sa.text('\'[]\'::json')),
        sa.Column('metadata', sa.JSON(), nullable=True, default=sa.text('\'{}\'::json')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for knowledge_articles
    op.create_index('ix_knowledge_articles_tenant_id', 'knowledge_articles', ['tenant_id'])
    op.create_index('ix_knowledge_articles_category', 'knowledge_articles', ['category'])
    op.create_index('ix_knowledge_articles_subcategory', 'knowledge_articles', ['subcategory'])
    op.create_index('ix_knowledge_articles_status', 'knowledge_articles', ['status'])
    op.create_index('ix_knowledge_articles_published_at', 'knowledge_articles', ['published_at'])
    op.create_index('ix_knowledge_articles_author_id', 'knowledge_articles', ['author_id'])
    op.create_index('ix_knowledge_articles_created_at', 'knowledge_articles', ['created_at'])
    op.create_index('ix_article_tenant_status', 'knowledge_articles', ['tenant_id', 'status'])
    op.create_index('ix_article_category_published', 'knowledge_articles', ['category', 'published_at'])
    op.create_index('ix_article_search_ranking', 'knowledge_articles', ['search_ranking', 'view_count'])
    
    # Unique constraint for tenant + slug
    op.create_unique_constraint('uq_article_slug_tenant', 'knowledge_articles', ['tenant_id', 'slug'])
    
    # Full-text search index for PostgreSQL
    op.execute("""
        CREATE INDEX ix_knowledge_articles_fts 
        ON knowledge_articles 
        USING gin(to_tsvector('english', title || ' ' || coalesce(summary, '') || ' ' || content))
    """)

    # 2. Article Comments Table
    op.create_table('article_comments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('article_id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_helpful_feedback', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_public', sa.Boolean(), nullable=False, default=True),
        sa.Column('author_id', sa.String(), nullable=True),
        sa.Column('author_name', sa.String(), nullable=False),
        sa.Column('author_email', sa.String(), nullable=True),
        sa.Column('author_type', sa.String(), nullable=False, default='customer'),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('is_approved', sa.Boolean(), nullable=False, default=True),
        sa.Column('moderated_by', sa.String(), nullable=True),
        sa.Column('moderated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['article_id'], ['knowledge_articles.id'], ondelete='CASCADE')
    )
    
    # Indexes for article_comments
    op.create_index('ix_article_comments_article_id', 'article_comments', ['article_id'])
    op.create_index('ix_article_comments_tenant_id', 'article_comments', ['tenant_id'])
    op.create_index('ix_article_comments_author_id', 'article_comments', ['author_id'])
    op.create_index('ix_article_comments_created_at', 'article_comments', ['created_at'])

    # 3. Article Analytics Table
    op.create_table('article_analytics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('article_id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('views', sa.Integer(), nullable=False, default=0),
        sa.Column('unique_views', sa.Integer(), nullable=False, default=0),
        sa.Column('time_on_page', sa.Integer(), nullable=False, default=0),
        sa.Column('bounce_rate', sa.Integer(), nullable=False, default=0),
        sa.Column('helpful_votes', sa.Integer(), nullable=False, default=0),
        sa.Column('unhelpful_votes', sa.Integer(), nullable=False, default=0),
        sa.Column('comments_count', sa.Integer(), nullable=False, default=0),
        sa.Column('shares', sa.Integer(), nullable=False, default=0),
        sa.Column('search_queries', sa.JSON(), nullable=True, default=sa.text('\'[]\'::json')),
        sa.Column('search_position', sa.Integer(), nullable=True),
        sa.Column('traffic_sources', sa.JSON(), nullable=True, default=sa.text('\'{}\'::json')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['article_id'], ['knowledge_articles.id'], ondelete='CASCADE')
    )
    
    # Indexes for article_analytics
    op.create_index('ix_analytics_article_date', 'article_analytics', ['article_id', 'date'])
    op.create_unique_constraint('uq_analytics_article_date', 'article_analytics', ['article_id', 'date'])

    # 4. Customer Portal Settings Table
    op.create_table('customer_portal_settings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('customer_id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('email_notifications', sa.Boolean(), nullable=False, default=True),
        sa.Column('sms_notifications', sa.Boolean(), nullable=False, default=False),
        sa.Column('push_notifications', sa.Boolean(), nullable=False, default=True),
        sa.Column('preferred_language', sa.String(), nullable=False, default='en'),
        sa.Column('timezone', sa.String(), nullable=False, default='UTC'),
        sa.Column('preferred_contact_method', sa.String(), nullable=False, default='email'),
        sa.Column('dashboard_layout', sa.JSON(), nullable=True, default=sa.text('\'{}\'::json')),
        sa.Column('favorite_articles', sa.JSON(), nullable=True, default=sa.text('\'[]\'::json')),
        sa.Column('bookmarked_tickets', sa.JSON(), nullable=True, default=sa.text('\'[]\'::json')),
        sa.Column('allow_chat_history', sa.Boolean(), nullable=False, default=True),
        sa.Column('allow_analytics_tracking', sa.Boolean(), nullable=False, default=True),
        sa.Column('public_profile', sa.Boolean(), nullable=False, default=False),
        sa.Column('high_contrast_mode', sa.Boolean(), nullable=False, default=False),
        sa.Column('large_text_mode', sa.Boolean(), nullable=False, default=False),
        sa.Column('screen_reader_mode', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for customer_portal_settings
    op.create_index('ix_customer_portal_settings_customer_id', 'customer_portal_settings', ['customer_id'])
    op.create_index('ix_customer_portal_settings_tenant_id', 'customer_portal_settings', ['tenant_id'])
    op.create_unique_constraint('uq_customer_portal_settings', 'customer_portal_settings', ['customer_id', 'tenant_id'])

    # Live Chat System Tables

    # 5. Chat Sessions Table
    op.create_table('chat_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default='waiting'),
        sa.Column('customer_id', sa.String(), nullable=True),
        sa.Column('customer_name', sa.String(), nullable=True),
        sa.Column('customer_email', sa.String(), nullable=True),
        sa.Column('visitor_id', sa.String(), nullable=True),
        sa.Column('assigned_agent_id', sa.String(), nullable=True),
        sa.Column('assigned_agent_name', sa.String(), nullable=True),
        sa.Column('queue_id', sa.String(), nullable=True),
        sa.Column('initial_message', sa.Text(), nullable=True),
        sa.Column('page_url', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('referrer', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('last_activity', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('wait_time_seconds', sa.Integer(), nullable=False, default=0),
        sa.Column('session_duration_seconds', sa.Integer(), nullable=False, default=0),
        sa.Column('message_count', sa.Integer(), nullable=False, default=0),
        sa.Column('customer_rating', sa.Integer(), nullable=True),
        sa.Column('customer_feedback', sa.Text(), nullable=True),
        sa.Column('ticket_id', sa.String(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True, default=sa.text('\'{}\'::json')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for chat_sessions
    op.create_index('ix_chat_sessions_tenant_id', 'chat_sessions', ['tenant_id'])
    op.create_index('ix_chat_sessions_status', 'chat_sessions', ['status'])
    op.create_index('ix_chat_sessions_customer_id', 'chat_sessions', ['customer_id'])
    op.create_index('ix_chat_sessions_visitor_id', 'chat_sessions', ['visitor_id'])
    op.create_index('ix_chat_sessions_assigned_agent_id', 'chat_sessions', ['assigned_agent_id'])
    op.create_index('ix_chat_sessions_queue_id', 'chat_sessions', ['queue_id'])
    op.create_index('ix_chat_sessions_created_at', 'chat_sessions', ['created_at'])
    op.create_index('ix_chat_sessions_ticket_id', 'chat_sessions', ['ticket_id'])
    op.create_unique_constraint('uq_chat_session_id', 'chat_sessions', ['session_id'])

    # 6. Chat Messages Table
    op.create_table('chat_messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('message_type', sa.String(), nullable=False, default='text'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_html', sa.Text(), nullable=True),
        sa.Column('sender_type', sa.String(), nullable=False),
        sa.Column('sender_id', sa.String(), nullable=True),
        sa.Column('sender_name', sa.String(), nullable=False),
        sa.Column('is_internal', sa.Boolean(), nullable=False, default=False),
        sa.Column('file_attachments', sa.JSON(), nullable=True, default=sa.text('\'[]\'::json')),
        sa.Column('sent_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True, default=sa.text('\'{}\'::json')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE')
    )
    
    # Indexes for chat_messages
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('ix_chat_messages_tenant_id', 'chat_messages', ['tenant_id'])
    op.create_index('ix_chat_messages_sent_at', 'chat_messages', ['sent_at'])

    # 7. Chat Agent Status Table
    op.create_table('chat_agent_status',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default='offline'),
        sa.Column('status_message', sa.String(), nullable=True),
        sa.Column('max_concurrent_chats', sa.Integer(), nullable=False, default=3),
        sa.Column('current_chat_count', sa.Integer(), nullable=False, default=0),
        sa.Column('skills', sa.JSON(), nullable=True, default=sa.text('\'[]\'::json')),
        sa.Column('queue_memberships', sa.JSON(), nullable=True, default=sa.text('\'[]\'::json')),
        sa.Column('last_seen', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('status_changed_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('websocket_connection_id', sa.String(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True, default=sa.text('\'{}\'::json')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for chat_agent_status
    op.create_index('ix_chat_agent_status_tenant_id', 'chat_agent_status', ['tenant_id'])
    op.create_unique_constraint('uq_chat_agent_status_agent_id', 'chat_agent_status', ['agent_id'])

    # Enhanced Ticketing System Columns
    
    # Add new columns to existing tickets table
    if not column_exists('tickets', 'source'):
        op.add_column('tickets', sa.Column('source', sa.String(), nullable=False, default='customer_portal'))
    
    if not column_exists('tickets', 'sla_breach_time'):
        op.add_column('tickets', sa.Column('sla_breach_time', sa.DateTime(), nullable=True))
    
    if not column_exists('tickets', 'response_time_minutes'):
        op.add_column('tickets', sa.Column('response_time_minutes', sa.Integer(), nullable=True))
    
    if not column_exists('tickets', 'resolution_time_minutes'):
        op.add_column('tickets', sa.Column('resolution_time_minutes', sa.Integer(), nullable=True))
    
    if not column_exists('tickets', 'external_references'):
        op.add_column('tickets', sa.Column('external_references', sa.JSON(), nullable=True, default=sa.text('\'{}\'::json')))

    # Add indexes for new ticket columns
    op.create_index('ix_tickets_source', 'tickets', ['source'])
    op.create_index('ix_tickets_sla_breach_time', 'tickets', ['sla_breach_time'])

    # Create trigger to update updated_at timestamps
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # Apply triggers to tables that need automatic updated_at
    tables_with_updated_at = [
        'knowledge_articles',
        'article_comments', 
        'customer_portal_settings'
    ]
    
    for table in tables_with_updated_at:
        op.execute(f"""
            DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};
            CREATE TRIGGER update_{table}_updated_at 
                BEFORE UPDATE ON {table}
                FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
        """)

    # Create views for common queries
    
    # 1. Popular Articles View
    op.execute("""
        CREATE VIEW popular_articles_view AS
        SELECT 
            ka.*,
            COALESCE(comment_count, 0) as comment_count,
            ROUND((helpful_votes::float / NULLIF(helpful_votes + unhelpful_votes, 0)) * 100, 2) as helpfulness_percentage
        FROM knowledge_articles ka
        LEFT JOIN (
            SELECT article_id, COUNT(*) as comment_count
            FROM article_comments 
            WHERE is_public = true AND is_approved = true
            GROUP BY article_id
        ) ac ON ka.id = ac.article_id
        WHERE ka.status = 'published'
        ORDER BY ka.view_count DESC, ka.helpful_votes DESC;
    """)

    # 2. Chat Session Summary View
    op.execute("""
        CREATE VIEW chat_session_summary_view AS
        SELECT 
            cs.*,
            COALESCE(message_count_calc, 0) as actual_message_count,
            CASE 
                WHEN cs.status = 'ended' AND cs.customer_rating IS NOT NULL THEN cs.customer_rating
                ELSE NULL
            END as final_rating
        FROM chat_sessions cs
        LEFT JOIN (
            SELECT session_id, COUNT(*) as message_count_calc
            FROM chat_messages
            WHERE is_internal = false
            GROUP BY session_id
        ) cm ON cs.id = cm.session_id;
    """)


def downgrade() -> None:
    """Remove all support system tables and related objects."""
    
    # Drop views
    op.execute("DROP VIEW IF EXISTS chat_session_summary_view;")
    op.execute("DROP VIEW IF EXISTS popular_articles_view;")
    
    # Drop triggers and function
    tables_with_updated_at = [
        'knowledge_articles',
        'article_comments',
        'customer_portal_settings'
    ]
    
    for table in tables_with_updated_at:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};")
    
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Drop new ticket columns
    columns_to_drop = [
        'external_references',
        'resolution_time_minutes', 
        'response_time_minutes',
        'sla_breach_time',
        'source'
    ]
    
    for column in columns_to_drop:
        if column_exists('tickets', column):
            op.drop_column('tickets', column)
    
    # Drop chat system tables
    op.drop_table('chat_agent_status')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    
    # Drop knowledge base tables
    op.drop_table('customer_portal_settings')
    op.drop_table('article_analytics')
    op.drop_table('article_comments')
    op.drop_table('knowledge_articles')


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if column exists in table."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = :table_name 
            AND column_name = :column_name
        """),
        {"table_name": table_name, "column_name": column_name}
    )
    return result.scalar() > 0