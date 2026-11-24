"""会话受限与网络异常的回归测试。"""

from pathlib import Path

import httpx
import pytest

from campus_core.electricity_client import (
    ORIGIN, PAY_EXCHANGE, ROOM_ACCESS, ElectricityAccessDenied, ElectricityNetworkError,
    _exchange_cookie, query_address, query_saved)


def _context():
    return {
        "cookie": "TEST=x", "referer": ORIGIN + "/CloudPayment/bill/selectPayProject.do",
        "schoolcode": "school", "payProId": "project", "businesstype": "electricity",
    }


def test_use_flag_zero_is_access_denied_not_auth():
    def handle(request):
        assert str(request.url).split("?", 1)[0] == ROOM_ACCESS
        return httpx.Response(200, json={"businessData": {"useFlag": "0"}})

    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        with pytest.raises(ElectricityAccessDenied, match="未允许选房"):
            query_address(http, "东苑26 638", context=_context())


def test_access_denied_does_not_trigger_refresh(monkeypatch, tmp_path):
    from campus_core import electricity_client as ec

    path = tmp_path / "context.json"
    path.write_text('{"cookie":"TEST=x","referer":"%s","schoolcode":"s","payProId":"p",'
                    '"businesstype":"b","session_id":"sess"}' % (ORIGIN + "/CloudPayment/bill/selectPayProject.do"),
                    encoding="utf-8")
    path.chmod(0o600)
    monkeypatch.setattr(ec, "_query_once", lambda context, address, deadline: (_ for _ in ()).throw(
        ElectricityAccessDenied("云缴费暂未允许选房或查询。")))
    monkeypatch.setattr(ec, "refresh_saved", lambda p: pytest.fail("受限不应触发换票"))
    with pytest.raises(ElectricityAccessDenied):
        query_saved(path, "东苑26 638")


def test_exchange_network_error_is_wrapped():
    def boom(request):
        raise httpx.ConnectError("boom", request=request)

    with httpx.Client(transport=httpx.MockTransport(boom)) as http:
        with pytest.raises(ElectricityNetworkError, match="无法连接云缴费换票接口"):
            _exchange_cookie(http, _context(), "session")


@pytest.mark.parametrize(("failure", "message"), [
    (None, "暂时连不上电费登录服务，请稍后再试。"),
    ([], "电费登录服务返回异常，请稍后再试。"),
    ({"code_": "100600", "result_": False}, "电费查询的登录态已失效，请联系管理员重新导入。"),
])
def test_renewal_failure_reaches_bot_without_overwriting_context(monkeypatch, tmp_path, failure, message):
    import hashlib
    import json

    from campus_core import wmxy_auth
    from campus_core.atomic_io import atomic_write_json
    from henu_plugin.service import HenuPluginService

    path = tmp_path / "context.json"
    atomic_write_json(path, {**_context(), "session_id": "old-session", "login_token": "old-token",
                             "user_id": "user", "login_name": "login", "device_id": "device"})
    before = path.read_bytes()

    def respond(request):
        url = str(request.url).split("?", 1)[0]
        if url == ROOM_ACCESS:
            return httpx.Response(200, json={"returnmsg": "idserial为空"})
        if url == PAY_EXCHANGE:
            return httpx.Response(200, text="出错啦")
        assert url == wmxy_auth.LOGIN_URL
        if failure is None:
            raise httpx.ConnectError("synthetic connection error", request=request)
        body = json.dumps(failure).encode()
        return httpx.Response(200, content=body, headers={"campusSign": hashlib.sha256(body).hexdigest()})

    monkeypatch.setattr(wmxy_auth, "exchange_secret",
                        lambda _: wmxy_auth.CampusSession("0123456789abcdef01234567", "fixture-session"))
    client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kw: client(transport=httpx.MockTransport(respond), **kw))
    monkeypatch.setenv("HENU_ELECTRICITY_CONTEXT", str(path))
    result = HenuPluginService(tmp_path)._electricity_query({"text": "东苑26 638"})
    assert result == {"success": False, "msg": message}
    assert path.read_bytes() == before


def test_reimport_invalidates_directory_when_project_changes(monkeypatch, tmp_path):
    import io
    import json
    import sys

    from campus_core import electricity_client as ec
    from campus_core.atomic_io import atomic_write_json

    path = tmp_path / "context.json"
    atomic_write_json(path, {**_context(), "directory": [], "login_token": "previous-token"})
    imported = {**_context(), "payProId": "new-project"}
    monkeypatch.setattr(sys, "stdin", io.StringIO("synthetic import"))
    monkeypatch.setattr(ec, "_import_curl", lambda text: imported)
    assert ec.main(["--context", str(path), "--import-curl"]) == 0
    actual = json.loads(path.read_text())
    assert actual == {**imported, "login_token": "previous-token"}


def test_wmxy_login_validates_project_and_keeps_old_cookie_on_exchange_failure(monkeypatch, tmp_path):
    import json
    import runpy
    import sys
    from types import SimpleNamespace

    from campus_core.atomic_io import atomic_write_json

    main = runpy.run_path(str(Path(__file__).parents[1] / "ops" / "wmxy-login.py"))["main"]
    path = tmp_path / "context.json"
    device = tmp_path / "device.json"
    atomic_write_json(device, {"id": "test-device"})
    monkeypatch.setenv("WMXY_ACCOUNT", "synthetic")
    monkeypatch.setenv("WMXY_PASSWORD", "synthetic")
    monkeypatch.setattr(sys, "argv", ["wmxy-login", "--context", str(path), "--device", str(device)])
    logins = []
    exchange_secret = lambda http: logins.append("login") or SimpleNamespace(session="new-session")
    monkeypatch.setitem(main.__globals__, "exchange_secret", exchange_secret)
    monkeypatch.setitem(main.__globals__, "login_password", lambda *args, **kwargs: {
        "token": "new-token", "id": "test-user", "customId": "test-customer",
    })
    requests = []
    def reject_exchange(request):
        requests.append(request.url.path)
        return httpx.Response(503)

    client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kw: client(transport=httpx.MockTransport(reject_exchange), **kw))
    atomic_write_json(path, {"cookie": "TEST=old"})
    assert main() == 1
    assert logins == requests == []
    assert json.loads(path.read_text()) == {"cookie": "TEST=old"}

    atomic_write_json(path, _context())
    assert main() == 1
    assert len(logins) == len(requests) == 1
    saved = json.loads(path.read_text())
    assert saved["cookie"] == _context()["cookie"] and saved["login_token"] == "new-token"


def test_reimport_waits_for_refresh_and_keeps_latest_token(monkeypatch, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import io
    import json
    import sys
    from threading import Event
    from types import SimpleNamespace

    from campus_core import electricity_client as ec
    from campus_core.atomic_io import atomic_write_json

    path = tmp_path / "context.json"
    atomic_write_json(path, {
        **_context(), "session_id": "stale", "login_token": "old-token",
        "user_id": "synthetic", "login_name": "synthetic", "device_id": "synthetic",
    })
    rotating, finish, importing, imported = Event(), Event(), Event(), Event()

    def rotate_token(http, **kwargs):
        rotating.set()
        assert finish.wait(2)
        return SimpleNamespace(session="fresh"), {"token": "new-token"}

    def parse_import(text):
        importing.set()
        return {**_context(), "cookie": "SESSION=imported"}

    def import_context():
        result = ec.main(["--context", str(path), "--import-curl", "--keep-renewal"])
        imported.set()
        return result

    monkeypatch.setattr(ec, "login_and_refresh", rotate_token)
    monkeypatch.setattr(ec, "_exchange_cookie", lambda http, context, session_id: {
        "recognized": False, "session_expired": True,
    })
    monkeypatch.setattr(ec, "_import_curl", parse_import)
    monkeypatch.setattr(sys, "stdin", io.StringIO("synthetic"))
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending_refresh = pool.submit(ec.refresh_saved, path)
        try:
            assert rotating.wait(1)
            pending_import = pool.submit(import_context)
            assert importing.wait(1)
            assert not imported.wait(0.1)
        finally:
            finish.set()
        assert not pending_refresh.result()["recognized"]
        assert pending_import.result() == 0
    saved = json.loads(path.read_text())
    assert saved["cookie"] == "SESSION=imported" and saved["login_token"] == "new-token"


def test_file_transaction_times_out_before_entering_busy_transaction(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    from campus_core.atomic_io import file_transaction

    path = tmp_path / "context.json"

    def contend():
        with file_transaction(path, timeout=0.01):
            pytest.fail("超时的线程不能进入事务")

    with ThreadPoolExecutor(max_workers=1) as pool:
        with file_transaction(path), file_transaction(path, timeout=0):
            with pytest.raises(TimeoutError, match="file transaction lock timed out"):
                pool.submit(contend).result(timeout=2)


def test_file_transaction_passes_remaining_budget_to_file_lock(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from unittest.mock import Mock

    from campus_core import atomic_io

    process_lock = Mock()
    clock = iter((10.0, 10.0, 10.75))
    monkeypatch.setattr(atomic_io, "time", SimpleNamespace(monotonic=lambda: next(clock)))
    monkeypatch.setattr(atomic_io, "_process_lock", lambda _: process_lock)
    file_lock = Mock()
    file_lock.return_value.acquire.return_value = False
    monkeypatch.setattr(atomic_io, "FileLock", file_lock)
    with pytest.raises(TimeoutError, match="file transaction lock timed out"):
        with atomic_io.file_transaction(tmp_path / "context.json", timeout=1):
            pytest.fail("超时的线程不能进入事务")
    process_lock.acquire.assert_called_once_with(timeout=1)
    process_lock.release.assert_called_once()
    assert file_lock.call_args.kwargs["timeout"] == 0.25


def test_request_budget_stops_later_requests_and_shrinks_timeout(monkeypatch, tmp_path):
    from types import SimpleNamespace

    from campus_core import electricity_client as ec
    from campus_core.atomic_io import atomic_write_json

    path = tmp_path / "context.json"
    atomic_write_json(path, _context())
    clock = [100.0]
    monkeypatch.setattr(ec, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    requests = []

    def respond(request):
        requests.append(request)
        assert request.extensions["timeout"]["read"] == 2.0
        clock[0] += 3
        return httpx.Response(200, json={"businessData": {"useFlag": "1"}})

    client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kw: client(transport=httpx.MockTransport(respond), **kw))
    with pytest.raises(ElectricityNetworkError, match="超时"):
        ec.query_saved(path, "示例苑26 638", deadline=102.0)
    assert len(requests) == 1


def test_exchange_origin_policy_and_same_origin_hop_limit():
    from campus_core.electricity_client import ElectricityProtocolError, _exchange_destination

    base = httpx.URL(PAY_EXCHANGE)
    assert _exchange_destination(base, "/result") == httpx.URL(f"{ORIGIN}/result")
    for unrelated in ("http://example.invalid", "https://example.invalid", base.copy_with(port=443)):
        with pytest.raises(ElectricityProtocolError):
            _exchange_destination(base, str(unrelated))

    requests = []
    def redirect(request):
        requests.append(request)
        return httpx.Response(302, headers={"Set-Cookie": "SESSION=synthetic; Path=/", "Location": "/result"})

    with httpx.Client(transport=httpx.MockTransport(redirect)) as http:
        with pytest.raises(ElectricityProtocolError, match="跳转次数超限"):
            _exchange_cookie(http, _context(), "synthetic-session")
    assert len(requests) == 4


@pytest.mark.parametrize(("overrides", "keep_option", "keeps_renewal", "keeps_directory"), [
    ({}, False, True, True),
    ({"cookie": "SESSION=other"}, False, False, False),
    ({"cookie": "SESSION=same-account"}, True, True, False),
    ({"schoolcode": "new-school"}, True, False, False),
    ({"cookie": "SESSION=same-account", "payProId": "new-project"}, True, True, False),
    ({"businesstype": "new-business"}, False, True, False),
])
def test_reimport_separates_credentials_and_cached_directory(monkeypatch, tmp_path, overrides,
                                                            keep_option, keeps_renewal, keeps_directory):
    import io
    import sys

    from campus_core import electricity_client as ec
    from campus_core.atomic_io import atomic_write_json

    path = tmp_path / "context.json"
    credentials = {
        "login_token": "old-token", "session_id": "old-session", "custom_id": "old-customer",
        "user_id": "old-user", "login_name": "old-name", "device_id": "old-device",
        "device_model": "old-model", "device_product": "old-product", "device_release": "old-release",
    }
    atomic_write_json(path, {**_context(), **credentials, "directory": []})
    new_context = {**_context(), **overrides}
    monkeypatch.setattr(ec, "_import_curl", lambda text: new_context)
    monkeypatch.setattr(sys, "stdin", io.StringIO("synthetic cURL"))
    args = ["--import-curl", "--context", str(path)]
    if keep_option:
        args.append("--keep-renewal")
    assert ec.main(args) == 0
    expected = new_context.copy()
    if keeps_renewal:
        expected.update(credentials)
    if keeps_directory:
        expected["directory"] = []
    assert ec._load_context(path) == expected
