# tests BloomFilter.add(), check(), serialize()
def test_bloom_add_check(bloom_filter):
    bloom_filter.add("token123")
    assert bloom_filter.check("token123") == True
