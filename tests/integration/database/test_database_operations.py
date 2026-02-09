"""
Integration tests for database operations.

Tests use testcontainers to spin up real PostgreSQL instances.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# =============================================================================
# Database Connection Tests
# =============================================================================

class TestDatabaseConnection:
    """Tests for database connectivity."""

    @pytest.mark.integration
    @pytest.mark.postgres
    @pytest.mark.asyncio
    async def test_database_connection(self, async_db_session: AsyncSession):
        """Database connection is established."""
        result = await async_db_session.execute(text("SELECT 1"))
        row = result.scalar()
        assert row == 1

    @pytest.mark.integration
    @pytest.mark.postgres
    @pytest.mark.asyncio
    async def test_database_version(self, async_db_session: AsyncSession):
        """Database version can be retrieved."""
        result = await async_db_session.execute(text("SELECT version()"))
        version = result.scalar()
        assert "PostgreSQL" in version


# =============================================================================
# Schema Migration Tests
# =============================================================================

class TestSchemaMigration:
    """Tests for database schema operations."""

    @pytest.mark.integration
    @pytest.mark.postgres
    @pytest.mark.asyncio
    async def test_create_tables(self, async_db_session: AsyncSession):
        """Tables can be created."""
        # Create test table
        await async_db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS test_tasks (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        await async_db_session.commit()
        
        # Verify table exists
        result = await async_db_session.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = 'test_tasks'
        """))
        table = result.scalar()
        assert table == "test_tasks"

    @pytest.mark.integration
    @pytest.mark.postgres
    @pytest.mark.asyncio
    async def test_create_recurring_tasks_table(self, async_db_session: AsyncSession):
        """Recurring tasks table can be created."""
        await async_db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS recurring_tasks (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT DEFAULT '',
                rrule VARCHAR(500) NOT NULL,
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                last_generated TIMESTAMP,
                next_occurrence TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        await async_db_session.commit()
        
        # Verify
        result = await async_db_session.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'recurring_tasks'
        """))
        columns = [row[0] for row in result.fetchall()]
        assert "rrule" in columns
        assert "next_occurrence" in columns


# =============================================================================
# CRUD Operation Tests
# =============================================================================

class TestCRUDOperations:
    """Tests for CRUD database operations."""

    @pytest.mark.integration
    @pytest.mark.postgres
    @pytest.mark.asyncio
    async def test_insert_task(self, async_db_session: AsyncSession):
        """Insert operation works correctly."""
        # Setup table
        await async_db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS crud_tasks (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                user_id INTEGER NOT NULL
            )
        """))
        
        # Insert
        result = await async_db_session.execute(
            text("INSERT INTO crud_tasks (title, user_id) VALUES (:title, :user_id) RETURNING id"),
            {"title": "Test Task", "user_id": 1}
        )
        task_id = result.scalar()
        await async_db_session.commit()
        
        assert task_id is not None
        assert task_id > 0

    @pytest.mark.integration
    @pytest.mark.postgres
    @pytest.mark.asyncio
    async def test_select_task(self, async_db_session: AsyncSession):
        """Select operation works correctly."""
        # Setup
        await async_db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS select_tasks (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL
            )
        """))
        await async_db_session.execute(
            text("INSERT INTO select_tasks (title) VALUES ('Task 1'), ('Task 2')")
        )
        await async_db_session.commit()
        
        # Select
        result = await async_db_session.execute(
            text("SELECT * FROM select_tasks ORDER BY id")
        )
        rows = result.fetchall()
        
        assert len(rows) == 2
        assert rows[0][1] == "Task 1"

    @pytest.mark.integration
    @pytest.mark.postgres
    @pytest.mark.asyncio
    async def test_update_task(self, async_db_session: AsyncSession):
        """Update operation works correctly."""
        # Setup
        await async_db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS update_tasks (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        result = await async_db_session.execute(
            text("INSERT INTO update_tasks (title) VALUES ('Original') RETURNING id")
        )
        task_id = result.scalar()
        await async_db_session.commit()
        
        # Update
        await async_db_session.execute(
            text("UPDATE update_tasks SET title = :title WHERE id = :id"),
            {"title": "Updated", "id": task_id}
        )
        await async_db_session.commit()
        
        # Verify
        result = await async_db_session.execute(
            text("SELECT title FROM update_tasks WHERE id = :id"),
            {"id": task_id}
        )
        title = result.scalar()
        assert title == "Updated"

    @pytest.mark.integration
    @pytest.mark.postgres
    @pytest.mark.asyncio
    async def test_delete_task(self, async_db_session: AsyncSession):
        """Delete operation works correctly."""
        # Setup
        await async_db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS delete_tasks (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL
            )
        """))
        result = await async_db_session.execute(
            text("INSERT INTO delete_tasks (title) VALUES ('ToDelete') RETURNING id")
        )
        task_id = result.scalar()
        await async_db_session.commit()
        
        # Delete
        await async_db_session.execute(
            text("DELETE FROM delete_tasks WHERE id = :id"),
            {"id": task_id}
        )
        await async_db_session.commit()
        
        # Verify
        result = await async_db_session.execute(
            text("SELECT COUNT(*) FROM delete_tasks WHERE id = :id"),
            {"id": task_id}
        )
        count = result.scalar()
        assert count == 0


# =============================================================================
# Task Instance Generation Tests
# =============================================================================

class TestTaskInstanceGeneration:
    """Tests for recurring task instance generation."""

    @pytest.mark.integration
    @pytest.mark.postgres
    @pytest.mark.asyncio
    async def test_generate_task_instances(self, async_db_session: AsyncSession):
        """Task instances can be generated from recurring task."""
        # Setup tables
        await async_db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS gen_recurring_tasks (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                rrule VARCHAR(500) NOT NULL,
                start_date TIMESTAMP NOT NULL
            )
        """))
        await async_db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS gen_task_instances (
                id SERIAL PRIMARY KEY,
                recurring_task_id INTEGER REFERENCES gen_recurring_tasks(id),
                due_date TIMESTAMP NOT NULL,
                is_generated BOOLEAN DEFAULT FALSE,
                UNIQUE(recurring_task_id, due_date)
            )
        """))
        
        # Create recurring task
        result = await async_db_session.execute(
            text("""
                INSERT INTO gen_recurring_tasks (user_id, rrule, start_date)
                VALUES (1, 'FREQ=DAILY;INTERVAL=1', :start_date)
                RETURNING id
            """),
            {"start_date": datetime.utcnow()}
        )
        recurring_id = result.scalar()
        await async_db_session.commit()
        
        # Generate instances
        base_date = datetime.utcnow()
        for i in range(7):
            due_date = base_date + timedelta(days=i)
            await async_db_session.execute(
                text("""
                    INSERT INTO gen_task_instances (recurring_task_id, due_date)
                    VALUES (:recurring_id, :due_date)
                    ON CONFLICT (recurring_task_id, due_date) DO NOTHING
                """),
                {"recurring_id": recurring_id, "due_date": due_date}
            )
        await async_db_session.commit()
        
        # Verify
        result = await async_db_session.execute(
            text("SELECT COUNT(*) FROM gen_task_instances WHERE recurring_task_id = :id"),
            {"id": recurring_id}
        )
        count = result.scalar()
        assert count == 7

    @pytest.mark.integration
    @pytest.mark.postgres
    @pytest.mark.asyncio
    async def test_prevent_duplicate_instances(self, async_db_session: AsyncSession):
        """Duplicate task instances are prevented."""
        # Setup
        await async_db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS dup_task_instances (
                id SERIAL PRIMARY KEY,
                recurring_task_id INTEGER NOT NULL,
                due_date TIMESTAMP NOT NULL,
                UNIQUE(recurring_task_id, due_date)
            )
        """))
        
        due_date = datetime.utcnow()
        
        # Insert first instance
        await async_db_session.execute(
            text("""
                INSERT INTO dup_task_instances (recurring_task_id, due_date)
                VALUES (1, :due_date)
                ON CONFLICT (recurring_task_id, due_date) DO NOTHING
            """),
            {"due_date": due_date}
        )
        
        # Insert duplicate (should be ignored)
        await async_db_session.execute(
            text("""
                INSERT INTO dup_task_instances (recurring_task_id, due_date)
                VALUES (1, :due_date)
                ON CONFLICT (recurring_task_id, due_date) DO NOTHING
            """),
            {"due_date": due_date}
        )
        await async_db_session.commit()
        
        # Verify only one exists
        result = await async_db_session.execute(
            text("SELECT COUNT(*) FROM dup_task_instances WHERE recurring_task_id = 1")
        )
        count = result.scalar()
        assert count == 1


# =============================================================================
# Transaction Tests
# =============================================================================

class TestTransactions:
    """Tests for database transaction handling."""

    @pytest.mark.integration
    @pytest.mark.postgres
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, async_db_session: AsyncSession):
        """Transaction rollback works correctly."""
        # Setup
        await async_db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS tx_tasks (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL
            )
        """))
        await async_db_session.commit()
        
        # Insert in transaction
        await async_db_session.execute(
            text("INSERT INTO tx_tasks (title) VALUES ('Should Rollback')")
        )
        
        # Rollback
        await async_db_session.rollback()
        
        # Verify nothing was inserted
        result = await async_db_session.execute(
            text("SELECT COUNT(*) FROM tx_tasks")
        )
        count = result.scalar()
        assert count == 0
