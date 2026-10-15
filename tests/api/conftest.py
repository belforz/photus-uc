from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.deps import get_evaluation_job
from infra.db.base import Base
from infra.db.session import get_session
from main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def _override_get_session() -> Iterator[Session]:
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    # Sem `with`: evita disparar o lifespan da app, que criaria tabelas no
    # engine "real" (sqlite:///./photus.db) desnecessariamente durante os
    # testes, já que as tabelas do teste são criadas acima no engine em memória.
    app.dependency_overrides[get_session] = _override_get_session
    # UC06 roda em background após o POST /batches; por padrão os testes NÃO
    # devem acionar os binários C++ reais nem tocar o banco real. Os testes do
    # UC06 sobrescrevem este job com um SessionEvaluationJob + pipeline fake.
    app.dependency_overrides[get_evaluation_job] = lambda: (lambda batch_id: None)
    test_client = TestClient(app)
    # Exposto para testes que montam um SessionEvaluationJob sobre o MESMO
    # SQLite em memória da request.
    test_client.testing_session_factory = testing_session_local  # type: ignore[attr-defined]
    yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
