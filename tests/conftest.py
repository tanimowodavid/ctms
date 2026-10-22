from collections.abc import Iterator
import os
from urllib.parse import urlparse

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.models import Base


@pytest.fixture
def engine() -> Iterator[Engine]:
	database_url = os.getenv(
		"TEST_DATABASE_URL",
		"postgresql+psycopg2://postgres:change-this-local-password@localhost:5432/ctms_test",
	)
	database_name = urlparse(database_url).path.rsplit("/", 1)[-1]
	if not database_name.endswith("_test"):
		pytest.fail("TEST_DATABASE_URL must point to a dedicated database whose name ends in '_test'")
	engine = create_engine(database_url, pool_pre_ping=True)

	Base.metadata.drop_all(engine)
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
