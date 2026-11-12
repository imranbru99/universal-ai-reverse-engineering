from workers.exploration.fingerprint import canonicalize_url, state_fingerprint


def test_canonicalize_strips_utm():
    a = canonicalize_url("http://demo-target:3100/catalog?utm_source=x&q=1")
    b = canonicalize_url("http://demo-target:3100/catalog/?q=1")
    assert a == b


def test_fingerprint_stable():
    f1 = state_fingerprint("http://demo-target:3100/", "anonymous", "desktop", ["Home"])
    f2 = state_fingerprint("http://demo-target:3100/", "anonymous", "desktop", ["Home"])
    assert f1 == f2
