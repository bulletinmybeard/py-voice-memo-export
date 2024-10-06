# tests/unit/test_voice_memo_exporter.py
import platform
import re
from unittest.mock import AsyncMock, patch

import pytest

from pyvme.exporter import Memo, VoiceMemoExporter


def test_voice_memo_exporter_initialization():
    exporter = VoiceMemoExporter()
    assert exporter.source_path is not None
    assert exporter.export_path is not None
    assert exporter.db_path.endswith("CloudRecordings.db")


def test_get_default_source_path():
    path = VoiceMemoExporter._get_default_source_path()
    assert "Library" in path
    if int(platform.mac_ver()[0].split(".")[0]) >= 14:
        assert "group.com.apple.VoiceMemos.shared" in path
    else:
        assert "com.apple.voicememos" in path


@pytest.mark.asyncio
async def test_print_memo_row(capsys):
    memo = Memo(
        Z_PK=1,
        Z_ENT=1,
        Z_OPT=1,
        ZFLAGS=0,
        ZFOLDER=None,
        ZDATE=1672574400.0,  # 2023-01-01 12:00:00 in timestamp
        ZDURATION=60.0,
        ZEVICTIONDATE=None,
        ZLOCALDURATION=60.0,
        ZCUSTOMLABEL="Test Memo",
        ZCUSTOMLABELFORSORTING="Test Memo",
        ZENCRYPTEDTITLE="Test Memo",
        ZPATH="/source/test.m4a",
        ZUNIQUEID="unique_id_1",
        ZPLAYBACKPOSITION=0.0,
        ZSILENCEREMOVERENABLED=0,
        ZPLAYBACKRATE=1.0,
        source_path="/source/test.m4a",
        target_path="/export/test.m4a",
        status="Exported!",
    )

    exporter = VoiceMemoExporter()
    await exporter.print_memo_row(memo)
    captured = capsys.readouterr()

    # Check for the presence of key elements without relying on exact date
    assert "[✓]" in captured.out  # Status symbol
    assert "(00:01:00)" in captured.out  # Duration
    assert "(Test Memo)" in captured.out  # Memo title
    assert "test.m4a" in captured.out  # Source file
    assert "→" in captured.out  # Arrow symbol
    assert "test.m4a" in captured.out  # Target file

    # Check for date format without exact matching
    date_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
    assert re.search(date_pattern, captured.out) is not None


@pytest.mark.asyncio
async def test_cli_interface():
    test_args = [
        "pyvme",
        "--source_path",
        "/test/source",
        "--export_path",
        "/test/export",
        "--export_name_format",
        '{{ZENCRYPTEDTITLE}}_{{ZDATE.strftime("%Y-%m-%d")}}',
    ]

    with patch("sys.argv", test_args), patch(
        "pyvme.exporter.VoiceMemoExporter._validate_paths"
    ), patch(
        "pyvme.exporter.VoiceMemoExporter.run", new_callable=AsyncMock
    ) as mock_run, patch(  # noqa F841
        "pyvme.__main__.VoiceMemoExporter", autospec=True
    ) as mock_exporter:

        mock_exporter_instance = mock_exporter.return_value
        mock_exporter_instance.run = AsyncMock()

        from pyvme.__main__ import async_main

        await async_main()

        mock_exporter.assert_called_once_with(
            source_path="/test/source",
            export_path="/test/export",
            export_name_format='{{ZENCRYPTEDTITLE}}_{{ZDATE.strftime("%Y-%m-%d")}}',
        )
        mock_exporter_instance.run.assert_called_once()
