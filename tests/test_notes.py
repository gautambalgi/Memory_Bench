import pytest

from memorybench.memory.notes import NoteStore


def test_notes_are_relevant_current_and_scoped_to_the_learner(tmp_path):
    store = NoteStore(tmp_path)
    maya = store.create("Maya")
    leo = store.create("Leo")
    store.save(maya, {"exam_date": "June 12", "study_group": "Blue Lantern"})
    store.save(maya, {"exam_date": "June 19"})

    reopened = NoteStore(tmp_path)
    assert reopened.retrieve(maya, "When is my exam?") == {"exam_date": "June 19"}
    assert reopened.retrieve(maya, "What is my study group?") == {"study_group": "Blue Lantern"}
    assert reopened.retrieve(maya, "Explain lists and tuples.") == {}
    assert reopened.retrieve(leo, "When is my exam?") == {}
    assert reopened.get(maya).text == ""


def test_invalid_note_update_preserves_prior_notes(tmp_path):
    store = NoteStore(tmp_path)
    learner = store.create("Maya")
    store.save(learner, {"exam_date": "June 19"})
    with pytest.raises(ValueError, match="Invalid learner notes"):
        store.save(learner, {"exam_date": "June 12", "unknown": "Unexpected"})
    assert store.notes(learner) == {"exam_date": "June 19"}
