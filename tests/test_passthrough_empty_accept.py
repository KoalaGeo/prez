"""Regression tests for missing/empty Accept headers on the passthrough and
management endpoints.

These complement test_connegp_empty_accept.py (which covers the content
negotiation path used by object/listing endpoints). The /sparql passthrough
and /tbox-cache handlers parse the Accept header themselves with
``request.headers.get("accept").split(",")[0]``, which raised
``AttributeError: 'NoneType' object has no attribute 'split'`` when no Accept
header was sent. See https://github.com/RDFLib/prez/issues/380.

The `client` fixture is the one defined in test_endpoints_catprez.py / the
shared conftest (backed by the in-memory pyoxigraph store).
"""

from urllib.parse import quote


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