# pyvme/exporter.py
import asyncio
import logging
import os
import platform
import shutil
import time
from datetime import datetime, timedelta
from typing import List, Optional

import aiosqlite
from colorama import Fore, Style
from jinja2 import Environment
from pydantic import BaseModel, Field
from slugify import slugify


def slugify_filter(value):
    return slugify(value)


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Memo(BaseModel):
    Z_PK: int
    Z_ENT: int
    Z_OPT: int
    ZFLAGS: int
    ZFOLDER: Optional[str]
    ZDATE: float
    ZDURATION: float
    ZEVICTIONDATE: Optional[float]
    ZLOCALDURATION: float
    ZCUSTOMLABEL: str
    ZCUSTOMLABELFORSORTING: str
    ZENCRYPTEDTITLE: str
    ZPATH: str
    ZUNIQUEID: str
    ZPLAYBACKPOSITION: float
    ZSILENCEREMOVERENABLED: int
    ZPLAYBACKRATE: float
    source_path: str
    target_path: str = ""
    status: str = "Pending"
    date: datetime = Field(default_factory=lambda: datetime.now())

    def get_formatted_date(self) -> datetime:
        return datetime.fromtimestamp(self.ZDATE + 978307200.825232)


class VoiceMemoExporter:
    default_export_name_format: str = (
        "{{ZENCRYPTEDTITLE}}_{{ZDATE.strftime('%Y-%m-%d_%H-%M-%S')}}"
    )

    def __init__(
        self,
        source_path: str = None,
        export_path: str = None,
        export_name_format: str = default_export_name_format,
    ):
        self.export_name_format = export_name_format
        self.source_path = source_path or self._get_default_source_path()
        self.export_path = export_path or os.path.expanduser("~/Voice Memos Export")
        self.db_path = os.path.join(self.source_path, "CloudRecordings.db")

        self._validate_paths()

    @staticmethod
    def _get_default_source_path() -> str:
        """
        Get the default source path for macOS Voice Memos.

        Note:
            This method assumes the Voice Memos.app is installed in the default location.

        Returns:
            str: The default source path.
        """
        home = os.path.expanduser("~")
        if platform.system() != "Darwin":
            raise OSError("This script is designed to run on macOS only.")

        # Check macOS version
        mac_version = platform.mac_ver()[0]
        if int(mac_version.split(".")[0]) >= 14:  # macOS Sonoma (14.0) and later
            return os.path.join(
                home,
                "Library",
                "Group Containers",
                "group.com.apple.VoiceMemos.shared",
                "Recordings",
            )
        else:
            return os.path.join(
                home,
                "Library",
                "Application Support",
                "com.apple.voicememos",
                "Recordings",
            )

    def _validate_paths(self) -> None:
        """
        Raises:
            FileNotFoundError: If the source path or database file does not exist.
        """
        logger.debug("Source Path: %r", self.source_path)
        logger.debug("Export Path: %r", self.export_path)
        logger.debug("SQLite db file path: %r", self.db_path)
        if not os.path.exists(self.source_path):
            raise FileNotFoundError(f"Source path does not exist: {self.source_path}")
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
        if not os.path.exists(self.export_path):
            try:
                os.makedirs(self.export_path, exist_ok=True)
                logger.error(
                    "Export path does not exist: %r. Attempting to create it",
                    self.export_path,
                )
            except Exception:
                raise FileNotFoundError(
                    f"Export path does not exist: {self.export_path}"
                )

    async def query_all_memos(self) -> List[Memo]:
        """
        Query all memos from the database and convert them into Memo objects.

        Returns:
            List[Memo]: A list of Memo objects.
        """
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.execute(
                "SELECT * FROM ZCLOUDRECORDING ORDER BY ZDATE"
            ) as cursor:
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]

        return [
            Memo(
                **dict(zip(columns, row)),
                source_path=os.path.join(self.source_path, row[columns.index("ZPATH")]),
                target_path="",
                date=datetime.fromtimestamp(
                    row[columns.index("ZDATE")] + 978307200.825232
                ),
            )
            for row in rows
        ]

    async def export_memo(self, memo: Memo) -> Memo:
        """
        Export a memo to the export path.

        Args:
            memo (Memo): The memo to export.

        Returns:
            Memo: The modified memo object.
        """
        if not os.path.exists(memo.source_path):
            memo.status = (
                f"Error: Source file not found: {os.path.basename(memo.source_path)}"
            )
            return memo

        # Prepare context for Jinja2 template
        context = memo.dict()
        context["ZDATE"] = memo.get_formatted_date()

        # Set up Jinja2 environment with custom slugify filter
        env = Environment(autoescape=True)
        env.filters["slugify"] = slugify

        # Render the filename using Jinja2
        template = env.from_string(self.export_name_format)
        new_filename = template.render(context)

        memo.target_path = os.path.join(self.export_path, f"{new_filename}.m4a")

        # Check for potential issues
        if not os.access(os.path.dirname(memo.target_path), os.W_OK):
            memo.status = (
                f"Error: Permission denied "
                f"for target directory: {os.path.dirname(memo.target_path)}"
            )
            return memo

        if os.path.exists(memo.target_path):
            memo.status = (
                f"Warning: Target file "
                f"already exists: {os.path.basename(memo.target_path)}"
            )
            return memo

        try:
            shutil.copyfile(memo.source_path, memo.target_path)
            mod_time = time.mktime(memo.get_formatted_date().timetuple())
            os.utime(memo.target_path, (mod_time, mod_time))
            memo.status = "Exported!"
        except FileNotFoundError:
            memo.status = (
                f"Error: Source file not found: {os.path.basename(memo.source_path)}"
            )
        except PermissionError:
            memo.status = (
                f"Error: Permission denied "
                f"for file: {os.path.basename(memo.source_path)}"
            )
        except IOError as e:
            memo.status = f"Error: I/O error occurred: {str(e)}"
        except Exception as e:
            memo.status = f"Error: Unexpected error: {str(e)}"

        return memo

    async def export_all_memos(self) -> List[Memo]:
        """
        Process and export all memos in the database.

        Returns:
            List[Memo]: A list of exported Memo objects.
        """
        memos = await self.query_all_memos()
        tasks = [self.export_memo(memo) for memo in memos]
        exported_memos = await asyncio.gather(*tasks)

        for memo in exported_memos:
            await self.print_memo_row(memo)

        return exported_memos

    @staticmethod
    def format_duration(duration: float) -> str:
        """
        Format the duration in seconds into a human-readable string.

        Args:
            duration (float): The duration in seconds.

        Returns:
            str: The formatted duration.
        """
        return str(timedelta(seconds=duration)).split(".")[0].zfill(8)

    @staticmethod
    def truncate_path(path: str, length: int = 20) -> str:
        """
        Truncate a file path to a specified length.

        Args:
            path (str): The file path to truncate.
            length (int): The desired length of the truncated file path. Defaults to 20.

        Returns:
            str: The truncated file path.
        """
        if len(path) <= length:
            return path
        return "..." + path[-(length - 3) :]

    async def print_memo_row(self, memo: Memo) -> None:
        """
        Prints a formatted row for a memo in the export.

        Args:
            memo (Memo): The memo object to print.
        """
        date_str = memo.date.strftime("%Y-%m-%d %H:%M:%S")
        duration_str = self.format_duration(memo.ZDURATION)
        source_file = os.path.basename(memo.source_path)
        target_file = os.path.basename(memo.target_path) if memo.target_path else "N/A"

        source_truncated = self.truncate_path(source_file)
        target_truncated = self.truncate_path(target_file)

        if memo.status == "Exported!":
            status_symbol = "✓"
            status_color = Fore.GREEN
        elif memo.status.startswith("Warning:"):
            status_symbol = "!"
            status_color = Fore.YELLOW
        elif memo.status == "Pending":
            status_symbol = "•"
            status_color = Fore.BLUE
        else:
            status_symbol = "!"
            status_color = Fore.RED

        arrow_symbol = f"{Fore.GREEN}→{Style.RESET_ALL}"
        title_part = f" ({memo.ZENCRYPTEDTITLE})" if memo.ZENCRYPTEDTITLE else ""

        main_line = (
            f"{status_color}[{status_symbol}]{Style.RESET_ALL} "
            f"{date_str} ({duration_str}){title_part} "
            f"{source_truncated} {arrow_symbol} {target_truncated}"
        )
        print(main_line)

        if memo.status not in ["Exported!", "Pending"]:
            error_message = memo.status.replace("Error: ", "").replace("Warning: ", "")
            print(f"{status_color} └─ {error_message}{Style.RESET_ALL}")

    async def run(self) -> None:
        """
        Run the voice memo exporter.
        """
        print(f"Exporting voice memos to: {self.export_path}\n")

        exported_memos = await self.export_all_memos()

        for memo in exported_memos:
            await self.print_memo_row(memo)

        print(f"\nExport complete. {len(exported_memos)} memos processed.")
        print(f"Exported to: {self.export_path}")
