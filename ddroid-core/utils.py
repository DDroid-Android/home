import re
from typing import Dict, Tuple, Optional, Match


def get_time_format(tool_name: str) -> str:
    """ To get the record time format of a specific tool """
    time_mapping: Dict[str, str] = dict()
    time_mapping["combodroid"] = "%Y-%m-%d-%H-%M-%S"

    if tool_name in time_mapping:
        return time_mapping[tool_name]
    else:
        return "%Y-%m-%d-%H:%M:%S"


def get_name(tool_name: str) -> str:
    """ To get the name of the tool, use this function to avoid the naming problem """
    name_mapping: Dict[str, str] = dict()
    name_mapping["combodroid"] = "combo"
    name_mapping["droidbot.dfs.greedy"] = "droidbot"

    if tool_name in name_mapping:
        return name_mapping[tool_name]
    else:
        return tool_name


def line_type_of(line: str) -> Tuple[str, Optional[Match[str]]]:
    """ Identify the type of the given line"""
    # Match crash
    match_crash: Match[str] = re.search("Crash!", line, re.I)
    if match_crash:
        return "d-crash", match_crash
    # Match event or warning
    match_event: Match[str] = re.search("Event ", line, re.I)
    match_warning: Match[str] = re.search("Warning", line, re.I)
    if match_event is None and match_warning is None:
        return "d-line", None
    elif match_event is None and match_warning is not None:
        return "d-warning", match_warning
    elif match_event is not None and match_warning is None:
        return "d-event", match_event
    elif match_event.span() < match_warning.span():
        return "d-event", match_event
    elif match_warning.span() < match_event.span():
        return "d-warning", match_warning
    else:
        return "d-line", None


def line_id_of(line: str, match: Match[str]) -> str:
    pos: int = match.span()[1]
    line_id: str = line[pos]
    pos += 1
    while line[pos] != ":":
        line_id += line[pos]
        pos += 1
    line_id = line_id.strip()
    if not ('a' <= line_id <= 'z') and int(line_id) >= 10:
        line_id = chr(int(line_id) - 10 + 97)
    return line_id
