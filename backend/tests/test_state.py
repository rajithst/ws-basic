from app.schemas import Entity
from app.state import SessionState


def test_session_advances_on_confirm():
    session = SessionState()
    interaction_id = session.next_interaction_id()

    session.set_result(interaction_id, "example", [Entity(name="foo", value="bar")])
    assert session.results[interaction_id].status == "awaiting_confirmation"

    session.confirm(interaction_id, True)
    assert session.results[interaction_id].status == "confirmed"


def test_not_complete_until_all_confirmed():
    session = SessionState()
    ids = [session.next_interaction_id() for _ in range(3)]
    for pid in ids:
        session.set_result(pid, "text", [Entity(name="n", value="v")])
        session.confirm(pid, True)
    assert all(r.status == "confirmed" for r in session.summary())
