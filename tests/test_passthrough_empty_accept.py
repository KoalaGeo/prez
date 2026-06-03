"""Regression tests for missing/empty Accept headers on the passthrough and
management endpoints.

These complement test_connegp_empty_accept.py (which covers the content
negotiation path used by object/listing endpoints). The /sparql passthrough
and /tbox-cache handlers parse the Accept header themselves with
``request.headers.get("accept").split(",")[0]``, which raised
``AttributeError: 'NoneType' object has no attribute 'split'`` when no Accept
header was sent. See https://github.com/RDFLib/prez/issues/380.

This module defines its own fixtures (mirroring tests/test_endpoints_catprez.py)
because the project has no shared ``client`` fixture in conftest.py.
"""

from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient
from pyoxigraph.pyoxigraph import Store

from prez.app import assemble_app
from prez.dependencies import get_repo
from prez.sparql.methods import PyoxigraphRepo, Repo


@pytest.fixture(scope="session")
def test_store() -> Store:
    store = Store()
    for file in Path(__file__).parent.glob("../tests/data/*/input/*.ttl"):
        store.load(file.read_bytes(), "text/turtle")
    return store


@pytest.fixture(scope="session")
def test_repo(test_store: Store) -> Repo:
    return PyoxigraphRepo(test_store)


@pytest.fixture(scope="session")
def client(test_repo: Repo) -> TestClient:
    def override_get_repo():
        return test_repo

    app = assemble_app()
    app.dependency_overrides[get_repo] = override_get_repo

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_sparql_get_no_accept_header(client):
    # GET /sparql with no Accept header must not 500.
    q = quote("SELECT * WHERE { ?s ?p ?o } LIMIT 1")
    r = client.get(f"/sparql?query={q}")
    assert r.status_code != 500


def test_sparql_get_empty_accept_header(client):
    q = quote("SELECT * WHERE { ?s ?p ?o } LIMIT 1")
    r = client.get(f"/sparql?query={q}", headers={"Accept": ""})
    assert r.status_code != 500


def test_tbox_cache_no_accept_header(client):
    # /tbox-cache with no Accept header should fall back to text/turtle, not 500.
    r = client.get("/tbox-cache")
    assert r.status_code == 200


def test_tbox_cache_empty_accept_header(client):
    r = client.get("/tbox-cache", headers={"Accept": ""})
    assert r.status_code == 200