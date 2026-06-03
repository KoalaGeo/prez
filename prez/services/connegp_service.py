from connegp import Connegp
from fastapi import Request


def get_requested_profile_and_mediatype(request: Request):
    """Return the requested profile and mediatype.

    Some HTTP clients (e.g. Postman, Hopscotch) issue requests with no Accept
    header, or with an empty Accept header (``Accept:``). Browsers, curl and
    httpx send a populated header (``*/*`` etc.) by default and so never hit
    this path.

    When the Accept header is absent, connegp returns ``None`` for the
    requested mediatypes; calling ``frozenset(None)`` then raises
    ``TypeError`` and the request fails with HTTP 500. When the Accept header
    is present but empty, connegp returns a single placeholder mediatype with
    an empty name (``(1, "")``) which matches no profile and pollutes the
    downstream SPARQL generation.

    In both cases the correct behaviour is to treat the request as "no
    mediatype requested" so content negotiation falls back to the default
    profile and mediatype. See https://github.com/RDFLib/prez/issues/380 and
    https://github.com/RDFLib/prez/pull/318.
    """

    c = Connegp(request)

    # ``mediatypes_requested`` is either None (no Accept header / no _mediatype
    # query param), a list of ``(weight, mediatype)`` tuples (from the Accept
    # header) or a list of mediatype strings (from the _mediatype query param).
    requested_mediatypes = c.mediatypes_requested or []
    requested_mediatypes = frozenset(
        mt for mt in requested_mediatypes if not _is_blank_mediatype(mt)
    )

    return (
        c.profile_uris_requested,
        c.profile_tokens_requested,
        requested_mediatypes,
    )


def _is_blank_mediatype(mediatype) -> bool:
    """True if a requested mediatype is empty/placeholder and should be ignored.

    Handles both the ``(weight, mediatype)`` tuple form returned from the
    Accept header and the plain string form returned from the ``_mediatype``
    query parameter.
    """
    if isinstance(mediatype, tuple):
        return not (mediatype[1] or "").strip()
    return not (mediatype or "").strip()