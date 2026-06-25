# -*- coding: utf-8 -*-
"""Configuración de pytest.

Notas sobre path:
- ``src/`` se agrega a ``sys.path`` via ``pyproject.toml`` (``pythonpath = ["src"]``).
- ``main.app`` se importa de forma diferida dentro del fixture ``client``
  para no arrastrar la cadena de imports ``main → core.pipeline →
  messaging.publisher`` (que abre conexión a RabbitMQ) al cargar el conftest.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from sqlalchemy.pool import StaticPool

from models.database import Base, get_db

# Base de datos SQLite en memoria con StaticPool para mantener la conexión abierta
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    # Crea las tablas antes de cada test
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Borra las tablas después de cada test para empezar de cero
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    # Import diferido: evita que el conftest abra conexiones RabbitMQ
    # al cargarse (la app importa EventPublisher que se conecta al broker).
    from main import app  # noqa: WPS433 — import diferido intencional

    # Override de la dependencia get_db para usar la sesión de test
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    # Limpiar los overrides después del test
    app.dependency_overrides.clear()
