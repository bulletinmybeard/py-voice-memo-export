# pyvme/__main__.py
import argparse
import asyncio

from pyvme.exporter import VoiceMemoExporter


async def async_main():
    parser = argparse.ArgumentParser(
        description="Export audio files from macOS Voice Memo App."
    )
    parser.add_argument(
        "-s", "--source_path", type=str, help="Path to the Voice Memos source directory"
    )
    parser.add_argument(
        "-e", "--export_path", type=str, help="Path to the export folder"
    )
    parser.add_argument(
        "--export_name_format",
        type=str,
        default="{{ ZDATE.strftime('%Y%m%d') }}_"
        "{{ ZENCRYPTEDTITLE|replace(' ', '_') }}_{{ ZUNIQUEID }}",
        help="Format string for exported file names. Available placeholders: "
        "{ZENCRYPTEDTITLE}, {ZCUSTOMLABEL}, {ZDATE}, {ZDURATION}, {ZUNIQUEID}, "
        "{ext} (file extension). Date formatting is supported, e.g., {ZDATE:%Y-%m-%d}",
    )

    args = parser.parse_args()

    exporter = VoiceMemoExporter(
        source_path=args.source_path,
        export_path=args.export_path,
        export_name_format=args.export_name_format,
    )
    await exporter.run()


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
