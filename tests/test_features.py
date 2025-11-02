from context import Features


def test_parse():
    features = Features.from_fea(
        """
lookup foobar { 
    sub a by b;                                 
} foobar;
@group_one = [a b c];
@group_two = [@group_one d e f];
feature test {
    sub X by Y;
} test;
lookup foobar2 { sub c by d; } foobar2;
# Prefix: namedPrefix
lookup foobar3 {
    sub e by f;                                 
} foobar3;
feature test {
    pos X Y -150;
} test;
"""
    )
    assert "group_one" in features.classes
    assert features.classes["group_one"] == ["a", "b", "c"]
    assert features.classes["group_two"] == ["@group_one", "d", "e", "f"]
    # Parser preserves original formatting (single-line stays single-line)
    expected_anon = (
        "lookup foobar {\n    sub a by b;\n} foobar;\n"
        "lookup foobar2 { sub c by d; } foobar2;"
    )
    assert features.prefixes["anonymous"] == expected_anon
    assert len(features.features) == 2
    expected_named = "lookup foobar3 {\n    sub e by f;\n} foobar3;"
    assert features.prefixes["namedPrefix"] == expected_named
    # Feature code is stripped of trailing newlines
    assert features.features[0] == ("test", "    sub X by Y;")
    assert features.features[1] == ("test", "    pos X Y -150;")
