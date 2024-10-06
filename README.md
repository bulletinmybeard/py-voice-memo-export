[![Python 3.12](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Poetry 1.8.0](https://img.shields.io/badge/poetry-1.8.0+-blue.svg)](https://python-poetry.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![version](https://img.shields.io/badge/version-0.1.0-green.svg)](https://semver.org)

# py-voice-memo-export

A Python tool for effortlessly exporting Apple Voice Memos. PyVoiceMemoExport provides a simple solution to back up your voice memos from macOS.

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Contributing](#contributing)
- [Changelog](#changelog)
- [License](#license)

## Features

- Export all voice memos
- Preserve original recording dates
- Flexible filename formatting using Jinja2 templates
- Supports macOS Sonoma and earlier versions

## Prerequisites

- macOS (Catalina or later)
- Python 3.12 or higher
- Poetry 1.8.0 or higher

## Installation

1. Ensure you have Python 3.12 or later installed.
2. Install Poetry if you haven't already:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
3. Clone the repository:
   ```bash
   git clone https://github.com/bulletinmybeard/py-voice-memo-export.git
   cd py-voice-memo-export
   ```
4. Open poetry shell:
   ```bash
   poetry shell
   ```
5. Install dependencies:
   ```bash
   poetry install
   ```

## Usage

To use py-voice-memo-export, run the following command:

```bash
poetry run pyvme [OPTIONS]
```

### Command-line Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--source_path` | `-s` | Path to the Voice Memos source directory | Auto-detected based on macOS version |
| `--export_path` | `-e` | Path to the export folder | `~/Voice Memos Export` |
| `--export_name_format` | | Jinja2 template for exported filename format | `{{ZENCRYPTEDTITLE}}_{{ZDATE.strftime('%Y-%m-%d_%H-%M-%S')}}` |

## Export Name Format

The `--export_name_format` option allows you to customize the filenames of exported voice memos using Jinja2 templates.
This powerful feature gives you control over how your exported files are named.

### Available Placeholders

You can use the following placeholders in your export name format:

| Placeholder                  | Explanation | Example Value |
|:-----------------------------|:-------------|:---------------|
| `{{ZDATE}}`                  | The date and time of the recording (datetime object) | `2024-03-17 14:30:22` |
| `{{ZDURATION}}`              | The duration of the recording in seconds (float) | `180.5` |
| `{{ZENCRYPTEDTITLE}}`        | The title of the voice memo | `Meeting Notes` |
| `{{ZCUSTOMLABEL}}`           | Custom label for the memo (if set) | `Important` |
| `{{ZCUSTOMLABELFORSORTING}}` | Custom label used for sorting | `Work - Project A` |
| `{{ZUNIQUEID}}`              | Unique identifier for the memo | `A1B2C3D4-E5F6-G7H8-I9J0-K1L2M3N4O5P6` |
| `{{ZFLAGS}}`                 | Flags associated with the memo (integer) | `4` |

### Jinja2 Filters and Functions

Here are some useful Jinja2 filters and functions to modify the placeholders:

| Filter/Function | Explanation          | Example Usage | Example Output |
|-----------------|----------------------|---------------|---------------|
| `strftime()`    | Format dates         | `{{ZDATE.strftime('%Y-%m-%d')}}` | `2024-03-17` |
| `replace()`     | Replace characters   | `{{ZENCRYPTEDTITLE\|replace(' ', '_')}}` | `Meeting_Notes` |
| `truncate()`    | Limit string length  | `{{ZENCRYPTEDTITLE\|truncate(20, true, '')}}` | `Meeting Notes for P...` |
| `slugify`         | Slugify string (`AI & Machine Learning: Trends 2024`)    | `{{ZENCRYPTEDTITLE\|slugify}}` | `ai-machine-learning-trends-2024` |
| `lower`         | Convert to lowercase | `{{ZENCRYPTEDTITLE\|lower}}` | `meeting notes` |
| `upper`         | Convert to uppercase | `{{ZENCRYPTEDTITLE\|upper}}` | `MEETING NOTES` |

Note: When using these filters in the command line, make sure to properly escape any special characters.

### Examples

1. Basic format with date and title:
   ```
   {{ZENCRYPTEDTITLE}}_{{ZDATE.strftime('%Y-%m-%d_%H-%M-%S')}}
   ```
   Result: `My Voice Memo_2024-03-17_14-30-00.m4a`

2. Using duration and unique ID:
   ```
   {{ZDATE.strftime('%Y%m%d')}}_{{ZDURATION|int}}s_{{ZUNIQUEID[-8:]}}
   ```
   Result: `20240317_180s_A1B2C3D4.m4a`

3. Conditional formatting:
   ```
   {% if ZCUSTOMLABEL %}{{ZCUSTOMLABEL}}_{% endif %}{{ZDATE.strftime('%Y-%m-%d')}}
   ```
   Result: `Important Meeting_2024-03-17.m4a` or `2024-03-17.m4a`

4. Complex formatting:
   ```
   {{ZDATE.strftime('%Y-%m-%d')}}_{{ZENCRYPTEDTITLE|replace(' ', '_')|truncate(20, true, '')}}_{{ZUNIQUEID[-8:]}}
   ```
   Result: `2024-03-17_My_Voice_Memo_Wit_A1B2C3D4.m4a`

Remember to properly escape any special characters when using the `--export_name_format` option in the command line.

### Examples

1. Export all voice memos to the default location:
   ```bash
   poetry run pyvme
   ```

2. Export to a specific folder with a custom filename format:
   ```bash
   poetry run pyvme \
      --export_path ~/Documents/VoiceMemoBackup \
      --export_name_format "{{ZDATE.strftime('%Y%m%d')}}_{{ZENCRYPTEDTITLE}}"
   ```

3. Export from a custom source path with a complex filename format:
   ```bash
   poetry run pyvme \
      --source_path /path/to/custom/VoiceMemos \
      --export_name_format "{{ZDATE.strftime('%Y-%m-%d')}}_{{ZENCRYPTEDTITLE|replace(' ', '_')|truncate(20, true, '')}}_{{ZUNIQUEID[-8:]}}"
   ```

4. Use conditional formatting in the filename:
   ```bash
   poetry run pyvme \
      --export_name_format "{% if ZENCRYPTEDTITLE %}{{ZENCRYPTEDTITLE}}_{% endif %}{{ZDATE.strftime('%Y-%m-%d')}}_{{ZDURATION|int}}s"
   ```

## Troubleshooting

### Common Issues
1. **Issue**: Unable to find Voice Memos database
   **Solution**: Ensure you have created at least one voice memo using the Voice Memos app.

2. **Issue**: Permission denied errors
   **Solution**: Check that you have read access to the Voice Memos folder and write access to the export destination.

## Development

To contribute to the project:

1. Fork the repository
2. Create a new branch for your feature
3. Implement your changes
4. Run tests:
   ```bash
   # Simple
   poetry run pytest
   ```
5. Submit a pull request

## Contributing

We welcome contributions to py-voice-memo-export! Please see our [Contributing Guidelines](CONTRIBUTING.md) for more details on how to submit pull requests, report issues, or request features.

## Changelog

See the [CHANGELOG.md](CHANGELOG.md) file for details on what has changed in each version of the project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
