from collections.abc import Iterator
from sqlite3 import Connection as SQLiteConnection

import pytest
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session

from app.models import Base


@pytest.fixture
def engine() -> Iterator[Engine]:
	engine = create_engine("sqlite://")

	@event.listens_for(engine, "connect")
	def enable_foreign_keys(connection: SQLiteConnection, _: object) -> None:
		connection.execute("PRAGMA foreign_keys=ON")

	Base.metadata.create_all(engine)
	try:
		yield engine
	finally:
		Base.metadata.drop_all(engine)
		engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Iterator[Session]:
	with Session(engine) as session:
		yield session
