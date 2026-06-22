from e2e_cli.cache import CacheKey, DictionaryCache, lookup_with_cache, make_cache_key
from e2e_cli.render import DictionaryResult


def test_cache_returns_none_for_missing_entry(tmp_path):
    cache = DictionaryCache(tmp_path / "cache.sqlite3")
    key = CacheKey("take off", "gpt-test", 2, "https://example.test/v1")

    assert cache.get(key) is None


def test_cache_stores_result_with_query_count_one(tmp_path):
    cache = DictionaryCache(tmp_path / "cache.sqlite3")
    key = CacheKey("take off", "gpt-test", 2, "https://example.test/v1")
    result = DictionaryResult(
        term="take off",
        meaning="To leave the ground.",
        examples=["The plane took off.", "Her career took off."],
    )

    cache.store_lookup(key, result)

    entry = cache.get(key)
    assert entry is not None
    assert entry.result == result
    assert entry.query_count == 1


def test_cache_hit_increments_query_count(tmp_path):
    cache = DictionaryCache(tmp_path / "cache.sqlite3")
    key = CacheKey("take off", "gpt-test", 2, "https://example.test/v1")
    result = DictionaryResult(
        term="take off",
        meaning="To leave the ground.",
        examples=["The plane took off."],
    )
    cache.store_lookup(key, result)

    entry = cache.record_hit(key)

    assert entry is not None
    assert entry.query_count == 2
    assert cache.get(key).query_count == 2


def test_refresh_replaces_result_and_increments_query_count(tmp_path):
    cache = DictionaryCache(tmp_path / "cache.sqlite3")
    key = CacheKey("take off", "gpt-test", 2, "https://example.test/v1")
    cache.store_lookup(
        key,
        DictionaryResult(
            term="take off",
            meaning="Old meaning.",
            examples=["Old example."],
        ),
    )
    refreshed = DictionaryResult(
        term="take off",
        meaning="New meaning.",
        examples=["New example."],
    )

    cache.store_lookup(key, refreshed)

    entry = cache.get(key)
    assert entry is not None
    assert entry.result == refreshed
    assert entry.query_count == 2


def test_make_cache_key_normalizes_term_and_blank_base_url():
    key = make_cache_key(
        "  Take   Off  ",
        model="gpt-test",
        examples_count=2,
        base_url="   ",
    )

    assert key == CacheKey("take off", "gpt-test", 2, "")


def test_lookup_with_cache_stores_miss(tmp_path):
    cache = DictionaryCache(tmp_path / "cache.sqlite3")
    calls = []

    def lookup(term, *, model, examples_count, base_url):
        calls.append((term, model, examples_count, base_url))
        return DictionaryResult(term=term, meaning="Meaning.", examples=["Example."])

    result = lookup_with_cache(
        "take off",
        model="gpt-test",
        examples_count=1,
        base_url="https://example.test/v1",
        lookup=lookup,
        cache=cache,
    )

    assert result == DictionaryResult(
        term="take off",
        meaning="Meaning.",
        examples=["Example."],
    )
    assert calls == [("take off", "gpt-test", 1, "https://example.test/v1")]
    entry = cache.get(
        CacheKey("take off", "gpt-test", 1, "https://example.test/v1")
    )
    assert entry is not None
    assert entry.query_count == 1


def test_lookup_with_cache_returns_hit_without_calling_lookup(tmp_path):
    cache = DictionaryCache(tmp_path / "cache.sqlite3")
    key = CacheKey("take off", "gpt-test", 1, "https://example.test/v1")
    cached_result = DictionaryResult(
        term="take off",
        meaning="Cached meaning.",
        examples=["Cached example."],
    )
    cache.store_lookup(key, cached_result)

    def lookup(term, *, model, examples_count, base_url):
        raise AssertionError("lookup should not be called on cache hit")

    result = lookup_with_cache(
        "take off",
        model="gpt-test",
        examples_count=1,
        base_url="https://example.test/v1",
        lookup=lookup,
        cache=cache,
    )

    assert result == cached_result
    assert cache.get(key).query_count == 2


def test_lookup_with_cache_refreshes_cached_result(tmp_path):
    cache = DictionaryCache(tmp_path / "cache.sqlite3")
    key = CacheKey("take off", "gpt-test", 1, "https://example.test/v1")
    cache.store_lookup(
        key,
        DictionaryResult(
            term="take off",
            meaning="Cached meaning.",
            examples=["Cached example."],
        ),
    )

    def lookup(term, *, model, examples_count, base_url):
        return DictionaryResult(
            term=term,
            meaning="Fresh meaning.",
            examples=["Fresh example."],
        )

    result = lookup_with_cache(
        "take off",
        model="gpt-test",
        examples_count=1,
        base_url="https://example.test/v1",
        lookup=lookup,
        cache=cache,
        refresh=True,
    )

    assert result.meaning == "Fresh meaning."
    assert cache.get(key).query_count == 2
