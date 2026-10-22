"""Opt-in PostgreSQL migration test for a dedicated, empty test database."""

import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


@pytest.mark.skipif(
	not os.environ.get("CTMS_MIGRATION_TEST_DATABASE_URL"),
	reason="set CTMS_MIGRATION_TEST_DATABASE_URL to an empty, disposable PostgreSQL database",
)
def test_initial_migration_applies_to_fresh_postgresql_database() -> None:
	database_url = os.environ["CTMS_MIGRATION_TEST_DATABASE_URL"]
	if "+psycopg2" not in database_url:
		pytest.fail("migration integration test requires the PostgreSQL psycopg2 URL")

	engine = create_engine(database_url)
	config = Config("alembic.ini")
	config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
	previous_database_url = os.environ.get("DATABASE_URL")
	migrated = False
	try:
		inspector = inspect(engine)
		if inspector.get_table_names() == ["alembic_version"]:
			with engine.begin() as connection:
				version_count = connection.scalar(text("SELECT count(*) FROM alembic_version"))
			if version_count == 0:
				with engine.begin() as connection:
					connection.exec_driver_sql("DROP TABLE alembic_version")
		inspector = inspect(engine)
		assert inspector.get_table_names() == [], "migration test database must be empty"

		os.environ["DATABASE_URL"] = database_url
		command.upgrade(config, "head")
		migrated = True

		inspector = inspect(engine)
		assert set(inspector.get_table_names()) == {
			"alembic_version", "application", "cohort", "conversation", "email_outbox", "message",
			"password_setup_token", "profile", "track"
		}
		with engine.connect() as connection:
			assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0002_staff_onboarding"
	finally:
		if migrated:
			command.downgrade(config, "base")
			with engine.begin() as connection:
				connection.exec_driver_sql("DROP TABLE IF EXISTS alembic_version")
		if previous_database_url is None:
			os.environ.pop("DATABASE_URL", None)
		else:
			os.environ["DATABASE_URL"] = previous_database_url
		engine.dispose()
