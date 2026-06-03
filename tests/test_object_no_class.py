"""Regression test: requesting an object whose URI has no rdf:type must return
a clean 404, not a 500.

Previously an empty ``classes`` set produced an empty ``VALUES ?class { }`` in
the profile-selection query, which crashes rdflib's SPARQL engine with
``AttributeError: 'list' object has no attribute 'name'`` (HTTP 500). This is
common from crawlers requesting stale/unknown URIs.
See https://github.com/RDFLib/prez/issues/380.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pyoxigraph.pyoxigraph import Store

from prez.app import assemble_app
from prez.dependencies import get_repo
from prez.models.model_exceptions import NoProfilesException
from prez.services.generate_profiles import get_profiles_and_mediatypes
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


def test_get_profiles_and_mediatypes_empty_classes_raises():
    # Unit-level: empty classes must raise NoProfilesException (-> 404), not the
    # rdflib AttributeError.
    with pytest.raises(NoProfilesException):
        get_profiles_and_mediatypes(frozenset())


def test_object_unknown_uri_returns_404(client):
    r = client.get("/object?uri=http://data.bgs.ac.uk/id/does/not/exist/NOPE")
    assert r.status_code == 404
    assert r.status_code != 500