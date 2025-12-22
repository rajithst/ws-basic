from app.schemas import Entity
from app.state import SessionState


def test_session_advances_on_confirm():
    session = SessionState()
    phrase_id = session.next_phrase_id()

    session.set_result(phrase_id, "example", [Entity(name="foo", value="bar")])
    assert session.results[phrase_id].status == "awaiting_confirmation"

    session.confirm(phrase_id, True)
    assert session.results[phrase_id].status == "confirmed"


def test_not_complete_until_all_confirmed():
    session = SessionState()
    ids = [session.next_phrase_id() for _ in range(3)]
    for pid in ids:
        session.set_result(pid, "text", [Entity(name="n", value="v")])
        session.confirm(pid, True)
    assert all(r.status == "confirmed" for r in session.summary())
