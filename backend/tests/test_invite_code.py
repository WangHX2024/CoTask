from app.common.utils import gen_invite_code, gen_anon_id


def test_invite_code_format():
    code = gen_invite_code()
    assert len(code) == 8
    # ambiguous chars excluded
    assert all(c not in code for c in "0OI1")


def test_anon_id_format():
    anon = gen_anon_id()
    assert len(anon) == 4
    assert anon.isalnum()
