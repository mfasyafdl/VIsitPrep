"""Plain session state for the VisitPrep UI.

The state is a dict holding only plain JSON-like data: the record is
stored with record_to_dict, alerts as {"code", "message", "level"}
dicts, asked as {"question", "answer"} dicts and the summary as a
dict. Dataclasses are built only at the call sites of core and the
component functions.
"""


def new_state() -> dict:
    """A fresh session state for step 1."""
    return {
        "step": 1,
        "story": "",
        "details": {},
        "alert_texts": [],
        "alerts": [],
        "alerts_error": False,
        "record": None,
        "asked": [],
        "skipped": [],
        "question": None,
        "summary": None,
        "pdf_path": None,
        "error": None,
        "busy": False,
        "token": 0,
    }


def bump(state: dict) -> dict:
    """A copy of the state with the token incremented by one."""
    new_state = dict(state)
    new_state["token"] = state["token"] + 1
    return new_state
