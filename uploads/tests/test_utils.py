"""Legacy utility tests kept as reference examples."""

# tests normalize_string(), generate_trigrams()
def test_generate_trigrams():
    assert generate_trigrams("john doe") == ['joh', 'ohn', 'hn_', 'n_d', '_do', 'doe']
