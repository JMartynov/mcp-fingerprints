import curses
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

from mcp_fingerprints.config_exporter import export_client_config

logger = logging.getLogger("mcp_fingerprints.tui")


def copy_to_clipboard(text: str) -> bool:
    try:
        if sys.platform == "darwin":
            subprocess.run(["pbcopy"], text=True, input=text, check=True)
            return True
        elif sys.platform == "linux":
            try:
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    text=True,
                    input=text,
                    check=True,
                )
                return True
            except FileNotFoundError:
                try:
                    subprocess.run(
                        ["xsel", "--clipboard", "--input"],
                        text=True,
                        input=text,
                        check=True,
                    )
                    return True
                except FileNotFoundError:
                    pass
        elif sys.platform == "win32":
            subprocess.run("clip", text=True, input=text, shell=True, check=True)
            return True
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Clipboard copy failed: {e}")
    return False


class MCPCatalogBrowser:
    def __init__(self, stdscr, data_dir: Path, initial_query: str = ""):
        self.stdscr = stdscr
        self.data_dir = data_dir
        self.query = initial_query

        self.all_passports: list[dict[str, Any]] = []
        skip_files = {"sync_state.json", "index.json", ".passport_index.pickle"}
        for file_path in self.data_dir.rglob("*.json"):
            if file_path.name in skip_files:
                continue
            try:
                content = json.loads(file_path.read_text(encoding="utf-8"))
                if "package_name" in content:
                    self.all_passports.append(content)
            except Exception:  # noqa: BLE001, S110
                pass

        self.ecosystems = ["All", "NPM", "PyPI", "GitHub"]
        self.current_tab = 0

        self.filtered_passports: list[dict[str, Any]] = []
        self.selected_index = 0
        self.scroll_offset = 0

        self.in_search = False
        self.status_message = ""
        self.status_timer = 0

        self.is_test = False
        try:
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
            curses.init_pair(3, curses.COLOR_GREEN, -1)
            curses.init_pair(4, curses.COLOR_RED, -1)
            curses.init_pair(5, curses.COLOR_YELLOW, -1)
            curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_CYAN)
            curses.init_pair(7, curses.COLOR_CYAN, -1)
        except Exception:  # noqa: BLE001
            self.is_test = True  # Ignore if not running in real curses (e.g., tests)

        self.apply_filters()

    def apply_filters(self):
        if self.query:
            results = []
            q = self.query.lower()
            for p in self.all_passports:
                score = 0
                pkg = p.get("package_name", "").lower()
                desc = p.get("description", "").lower()
                if q == pkg:
                    score += 10
                elif q in pkg:
                    score += 4
                if q in desc:
                    score += 1

                for v in p.get("versions", []):
                    for t in v.get("tool_signatures", []):
                        tname = t.get("name", "").lower()
                        if q == tname:
                            score += 10
                        elif q in tname:
                            score += 5

                if score > 0:
                    results.append((score, p))
            results.sort(key=lambda x: x[0], reverse=True)
            filtered = [r[1] for r in results]
        else:
            filtered = sorted(
                self.all_passports, key=lambda x: x.get("package_name", "")
            )

        eco = self.ecosystems[self.current_tab]
        if eco != "All":
            filtered = [
                p for p in filtered if p.get("ecosystem", "").lower() == eco.lower()
            ]

        self.filtered_passports = filtered
        if self.selected_index >= len(self.filtered_passports):
            self.selected_index = max(0, len(self.filtered_passports) - 1)
        self.scroll_offset = 0

    def safe_attron(self, pair):
        if not self.is_test:
            try:
                self.stdscr.attron(pair)
            except Exception:  # noqa: BLE001, S110
                pass

    def safe_attroff(self, pair):
        if not self.is_test:
            try:
                self.stdscr.attroff(pair)
            except Exception:  # noqa: BLE001, S110
                pass

    def safe_color_pair(self, n):
        if not self.is_test:
            try:
                return curses.color_pair(n)
            except Exception:  # noqa: BLE001
                return 0
        return 0

    def draw(self):
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()

        if width < 40 or height < 10:
            self.stdscr.addstr(0, 0, "Terminal too small")
            self.stdscr.refresh()
            return

        header_text = f" MCP Catalog Browser (Total: {len(self.all_passports)}) "
        self.safe_attron(self.safe_color_pair(1))
        self.stdscr.addstr(0, 0, header_text.ljust(width)[:width])
        self.safe_attroff(self.safe_color_pair(1))

        search_label = " Search: "
        self.stdscr.addstr(1, 0, search_label)
        query_display = self.query + ("_" if self.in_search else "")
        if self.in_search:
            self.safe_attron(self.safe_color_pair(7))
        self.stdscr.addstr(
            1,
            len(search_label),
            query_display.ljust(width - len(search_label))[: width - len(search_label)],
        )
        if self.in_search:
            self.safe_attroff(self.safe_color_pair(7))

        tab_y = 2
        tab_x = 0
        for i, tab in enumerate(self.ecosystems):
            text = f" [{tab}] "
            if i == self.current_tab:
                self.safe_attron(self.safe_color_pair(2))
                self.stdscr.addstr(tab_y, tab_x, text)
                self.safe_attroff(self.safe_color_pair(2))
            else:
                self.stdscr.addstr(tab_y, tab_x, text)
            tab_x += len(text)

        list_width = width // 3
        list_height = height - 5
        list_y = 3

        for i in range(list_height):
            idx = self.scroll_offset + i
            if idx < len(self.filtered_passports):
                p = self.filtered_passports[idx]
                pkg = p.get("package_name", "Unknown")[: list_width - 2]

                # Check badges for risk
                risk = "Low"
                security = p.get("security_profile", {})
                if security:
                    risk = security.get("risk_tier", "Low")

                badge = "[L]"
                color = 3
                if risk == "Critical":
                    badge = "[C]"
                    color = 4
                elif risk == "High":
                    badge = "[H]"
                    color = 4
                elif risk == "Medium":
                    badge = "[M]"
                    color = 5

                if idx == self.selected_index:
                    self.safe_attron(self.safe_color_pair(6))
                    self.stdscr.addstr(list_y + i, 0, pkg.ljust(list_width))
                    self.safe_attroff(self.safe_color_pair(6))
                else:
                    self.stdscr.addstr(list_y + i, 0, pkg.ljust(list_width))
                    self.safe_attron(self.safe_color_pair(color))
                    # draw badge at end if fits
                    if list_width > len(pkg) + 5:
                        self.stdscr.addstr(list_y + i, list_width - 5, badge)
                    self.safe_attroff(self.safe_color_pair(color))

        for i in range(list_height):
            self.stdscr.addstr(list_y + i, list_width, "|")

        detail_x = list_width + 2
        detail_width = width - detail_x
        if self.filtered_passports and self.selected_index < len(
            self.filtered_passports
        ):
            p = self.filtered_passports[self.selected_index]
            lines = []
            lines.append(f"Package: {p.get('package_name', 'Unknown')}")
            lines.append(f"Ecosystem: {p.get('ecosystem', 'Unknown')}")
            lines.append(f"Description: {p.get('description', '')}")
            if p.get("repository_url"):
                lines.append(f"Repository: {p.get('repository_url')}")

            security = p.get("security_profile", {})
            if security:
                lines.append(f"Risk Tier: {security.get('risk_tier', 'Unknown')}")

            lines.append("")

            versions = p.get("versions", [])
            if versions:
                v = versions[0]
                lines.append(f"Latest Version: {v.get('version', 'Unknown')}")
                tools = v.get("tool_signatures", [])
                lines.append(f"Tools ({len(tools)}):")
                for t in tools[:10]:
                    lines.append(f"  - {t.get('name', 'Unknown')}")
                    # Show some parameters if available
                    params = t.get("inputSchema", {}).get("properties", {})
                    if params:
                        lines.append(f"    Params: {', '.join(params.keys())}")
                if len(tools) > 10:
                    lines.append(f"  ... and {len(tools) - 10} more")
            else:
                lines.append("No versions found.")

            y_offset = list_y
            for line in lines:
                if y_offset >= height - 2:
                    break
                self.stdscr.addstr(y_offset, detail_x, line[: detail_width - 1])
                y_offset += 1
        else:
            self.stdscr.addstr(list_y, detail_x, "No servers found.")

        # Footer
        footer_text = (
            "[↑/↓] Navigate  [Tab] Ecosystem  [S] Search  [C] Copy Config  [Q] Quit"
        )
        if self.status_message and self.status_timer > 0:
            footer_text = self.status_message
            self.status_timer -= 1

        self.safe_attron(self.safe_color_pair(1))
        self.stdscr.addstr(height - 1, 0, footer_text.ljust(width)[:width])
        self.safe_attroff(self.safe_color_pair(1))

        self.stdscr.refresh()

    def set_status(self, message: str, ticks: int = 20):
        self.status_message = message
        self.status_timer = ticks

    def run(self):
        self.stdscr.timeout(100)

        while True:
            self.draw()

            try:
                ch = self.stdscr.getch()
            except curses.error:
                continue

            if ch == -1:
                continue

            if ch == curses.KEY_RESIZE:
                continue

            if self.in_search:
                if ch in (27, 10, 13):
                    self.in_search = False
                elif ch in (curses.KEY_BACKSPACE, 127, 8):
                    self.query = self.query[:-1]
                    self.apply_filters()
                elif 32 <= ch <= 126:
                    self.query += chr(ch)
                    self.apply_filters()
            else:
                if ch in (ord("q"), ord("Q")):
                    break
                elif ch in (ord("s"), ord("S"), ord("/")):
                    self.in_search = True
                elif ch == curses.KEY_UP:
                    if self.selected_index > 0:
                        self.selected_index -= 1
                        self.scroll_offset = min(
                            self.scroll_offset, self.selected_index
                        )
                elif ch == curses.KEY_DOWN:
                    if self.selected_index < len(self.filtered_passports) - 1:
                        self.selected_index += 1
                        height, _ = self.stdscr.getmaxyx()
                        list_height = height - 5
                        if self.selected_index >= self.scroll_offset + list_height:
                            self.scroll_offset += 1
                elif ch == 9:
                    self.current_tab = (self.current_tab + 1) % len(self.ecosystems)
                    self.apply_filters()
                elif (
                    ch in (ord("c"), ord("C"))
                    and self.filtered_passports
                    and self.selected_index < len(self.filtered_passports)
                ):
                    p = self.filtered_passports[self.selected_index]
                    try:
                        config = export_client_config(p, client="claude")
                        config_str = json.dumps(config, indent=2)
                        success = copy_to_clipboard(config_str)
                        if success:
                            self.set_status("Copied Claude config to clipboard!", 20)
                        else:
                            self.set_status("Clipboard copy failed.", 20)
                    except Exception as e:  # noqa: BLE001
                        self.set_status(f"Export error: {e}", 20)


def run_tui(data_dir: Path, initial_query: str = ""):
    def wrapper(stdscr):
        curses.curs_set(0)
        browser = MCPCatalogBrowser(stdscr, data_dir, initial_query)
        browser.run()

    curses.wrapper(wrapper)
