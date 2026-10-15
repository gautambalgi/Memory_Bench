from concurrent.futures import ThreadPoolExecutor

from memorybench.tracing.store import RunStore


def test_trace_survives_store_reopen(tmp_path):
    store = RunStore(tmp_path)
    run = store.create("A task", {"provider": "demo"})
    store.append(run["id"], "tool_call", name="calculate")
    store.append(run["id"], "tool_result", duration_ms=1.23456, result=4)
    reopened = RunStore(tmp_path)
    assert reopened.recent()[0]["status"] == "running"
    events = reopened.get(run["id"])["events"]
    assert [e["seq"] for e in events] == [1, 2]
    assert events[1]["duration_ms"] == 1.235


def test_redaction_covers_task_events_and_result(tmp_path):
    secret = "local-secret-for-tests"
    store = RunStore(tmp_path, (secret,))
    run = store.create(f"Task {secret}", {"api_key": "hide me"})
    store.append(
        run["id"],
        "test",
        nested={"password": "hidden", "text": secret},
        token="sk-test1234567890123456789",
    )
    run["answer"] = secret
    store.save(run)
    record = str(store.get(run["id"]))
    assert secret not in record
    assert "hide me" not in record
    assert "hidden" not in record
    assert "sk-test" not in record
    assert "[redacted]" in record


def test_concurrent_events_have_unique_order(tmp_path):
    store = RunStore(tmp_path)
    run = store.create("task", {})
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda i: store.append(run["id"], "test", number=i), range(20)))
    assert [e["seq"] for e in store.get(run["id"])["events"]] == list(range(1, 21))
