import logging
from collections import namedtuple
from datetime import datetime, timedelta
from typing import Dict, Set, List, Optional, Tuple


StringSet = Set[str]
NFATransitions = Dict[str, Dict[str, Set[str]]]
DFATransitions = Dict[str, Dict[str, str]]
AnalysisMetrics = Tuple[Optional[float], Optional[float], Tuple[int, int]]

AnalysisBasicInfo = namedtuple("AnalysisBasicInfo", ["tool_name", "app_name", "bug_id", "dir_name"])
AnalysisSummary = namedtuple("AnalysisSummary", ["event_cov", "event_pair_cov", "minimal_distance", "elapsed_time", "has_crash", "repr"])


class Event:
    """ This class is used to collect the information of an event """
    __name__ = "Event"

    def __init__(self, *, _id: str, _description: str, _reason: str, _dependency: str, _warning: Optional[str]):
        # Basic infos
        self.__id: str = _id
        self.__description: str = _description
        self.__reason: str = _reason
        self.__dependency: str = _dependency
        self.__warning: Optional[str] = _warning
        # Statistics
        self.__count: int = 0
        self.__warning_count: int = 0
        self.__first_trigger_time: Optional[timedelta] = None
        self.__first_trigger_warning_time: Optional[timedelta] = None
        return

    def trigger_at(self, trigger_time: timedelta) -> None:
        """ Trigger this event """
        self.__count += 1
        if self.__first_trigger_time is None:
            self.__first_trigger_time = trigger_time
        return

    def trigger_warning_at(self, trigger_time: timedelta) -> None:
        """ Trigger the corresponding warning of this event"""
        self.__warning_count += 1
        if self.__first_trigger_warning_time is None:
            self.__first_trigger_warning_time = trigger_time
        return

    # def set_warning(self, warning_msg: str) -> None:
    #     self.__warning = warning_msg
    #     return

    def id(self) -> str:
        return self.__id

    def count(self) -> int:
        return self.__count

    def warning_count(self) -> int:
        return self.__warning_count

    def first_trigger_seconds(self) -> int:
        if self.__first_trigger_time is None:
            return -1
        return self.__first_trigger_time.seconds

    def first_trigger_warning_seconds(self) -> int:
        if self.__first_trigger_warning_time is None:
            return 0
        return self.__first_trigger_warning_time.seconds

    def description(self) -> str:
        return self.__description

    def warning(self) -> str:
        return self.__warning if self.__warning is not None else ""

    def reason(self) -> str:
        return self.__reason

    def dependency(self):
        return self.__dependency

    def __repr__(self) -> str:
        return f"Event {self.__id}"

    def __str__(self) -> str:
        string: str = f"\t- {repr(self)} {self.count()}/{self.__warning_count} ({self.__first_trigger_time})"
        return string


class EventPair:
    """ This class is used to collect the information of event-pair """
    __name__ = "EventPair"

    def __init__(self, _event_pair: Tuple[Event, Event]):
        self.__event_pair: Tuple[Event, Event] = _event_pair
        self.__count: int = 0
        self.__first_trigger_time: Optional[datetime] = None
        return

    def trigger_at(self, trigger_time: timedelta) -> None:
        self.__count += 1
        if self.__first_trigger_time is None:
            self.__first_trigger_time = trigger_time
        return

    def first(self) -> Event:
        return self.__event_pair[0]

    def second(self) -> Event:
        return self.__event_pair[1]

    def count(self) -> int:
        return self.__count

    def __repr__(self) -> str:
        return f"({repr(self.first())}, {repr(self.second())})"

    def __str__(self) -> str:
        return f"{repr(self)} triggered {self.count()} times"


class Distances:
    """ This class is used to collect the distance information """
    __name__ = "Distances"

    def __init__(self, init_distance: int):
        self.__distances: Dict[int, int] = {init_distance: 1}
        return

    def reach_distance(self, distance: int) -> None:
        """ Update the distance record """
        if distance not in self.__distances:
            self.__distances[distance] = 1
        else:
            self.__distances[distance] += 1
        return

    def reached_distances(self) -> List[int]:
        return sorted(self.__distances.keys())

    def reached_distances_count(self) -> List[int]:
        return [self.__distances[dist] for dist in self.reached_distances()]

    def min(self) -> int:
        """ Return the minimal distance of all reached distances"""
        return min(self.reached_distances())

    def max(self) -> int:
        """ Return the maximal distance of all reached distances"""
        return max(self.reached_distances())

    def count_of(self, distance: int) -> int:
        return self.__distances[distance]

    def __repr__(self):
        print(f"The total distance is {self.max()}")
        for distance in sorted(self.reached_distances()):
            print(f"\tDistance {distance} is reached {self.count_of(distance)} times")


class AnalysisResult:
    """ This class is used to store all the analysis result """
    __name__ = "AnalysisResult"

    def __init__(self, dir_name: str, *, app_name: str, bug_id: str, tool_name: str, reason: str,
                 elapsed_time: timedelta, crash_time: List[timedelta],
                 metrics: Tuple[Dict[str, Event], Dict[str, EventPair], Distances]):
        # Basic infos
        self.__dir_name: str = dir_name
        self.__app_name: str = app_name
        self.__bug_id: str = bug_id
        self.__tool_name: str = tool_name
        self.__possible_reason: str = reason
        self.__elapsed_time: timedelta = elapsed_time
        self.__crash_time: List[timedelta] = crash_time
        # Metrics
        self.__events: Dict[str, Event] = metrics[0]
        self.__event_pairs: Dict[str, EventPair] = metrics[1]
        self.__distances: Distances = metrics[2]
        self.__metrics: AnalysisMetrics = self.__compute_metrics()
        # Link
        self.html_file_name: Optional[str] = None
        # Summary
        self.summary: AnalysisSummary = self.__summary()

    def events(self) -> List[Event]:
        return list(self.__events.values())

    def event_pairs(self) -> List[EventPair]:
        return list(self.__event_pairs.values())

    def distances(self) -> Distances:
        return self.__distances

    def basic_info(self) -> AnalysisBasicInfo:
        return AnalysisBasicInfo(self.__tool_name, self.__app_name, self.__bug_id, self.__dir_name)

    def __summary(self) -> AnalysisSummary:
        """ Generate the summary """
        ec, epc, md = self.__metrics
        elapsed_time: timedelta = self.__elapsed_time
        has_crash: bool = len(self.__crash_time) > 0
        return AnalysisSummary(ec, epc, md, elapsed_time, has_crash, self.__str_summary())

    def __str_summary(self) -> str:
        """ Generate the summary in string format """
        ec, epc, md = self.__metrics

        event_coverage: str = str(None) if ec is None else f"{ec:4.2%}" if int(ec) != 1 else "100%"
        event_pair_coverage: str = str(None) if epc is None else f"{epc:4.2%}" if int(epc) != 1 else "100%"
        min_distance, sum_distance = md
        has_crash: bool = len(self.__crash_time) > 0
        return f"({event_coverage}, {event_pair_coverage}, {min_distance}/{sum_distance}, {str(has_crash)})"

    def __compute_metrics(self) -> AnalysisMetrics:
        event_coverage: float = None if len(self.__events) == 0 \
            else sum(1 for event in self.__events.values() if event.count() > 0) / len(self.__events)
        event_pair_coverage: float = None if len(self.__event_pairs) == 0 \
            else sum(1 for ep in self.__event_pairs.values() if ep.count() > 0) / len(self.__event_pairs)
        min_and_sum_distance: Tuple[int, int] = (self.__distances.min(), self.__distances.max())
        return event_coverage, event_pair_coverage, min_and_sum_distance

    def __repr__(self) -> str:
        return f"Analysis Result of {str(self.__app_name)}-{str(self.__bug_id)} ({self.__tool_name})"

    def __str__(self) -> str:
        string: str = f"\n\n<{repr(self)}>\n[{self.__dir_name}]\n"

        string += f"[Event Info]\n"
        string += "\n".join([f"{str(self.__events[e_id])}" for e_id in sorted(self.__events.keys())])

        event_cov, event_pair_cov, min_max_distance, has_crash = self.summary.repr[1:-1].split(", ")
        string += f"\n[Analysis Summary (elapsed time: {self.__elapsed_time})]\n"
        string += f"\t- Event Coverage (EC): {event_cov}\n"
        string += f"\t- Event Pair Coverage (EPC): {event_pair_cov}\n"
        string += f"\t- Minimal Distance (MD): {min_max_distance}\n"
        string += f"\t- Has crash: {has_crash}\n"
        return string


class AnalysisOptions:
    """ DDroid Analysis Options """

    def __init__(self, _target_dir: str, _html_output: bool, _batch_analysis: bool):
        self.__target_dir: str = _target_dir
        self.__html_output: bool = _html_output
        self.__batch_analysis: bool = _batch_analysis

    def target_dir(self) -> str:
        return self.__target_dir

    def is_html_output(self) -> bool:
        return self.__html_output

    def is_batch_analysis(self) -> bool:
        return self.__batch_analysis


class AnalysisResultSummary:
    """ The summary collecting all analysis results """

    def __init__(self):
        self.__summary: Dict[str, Dict[str, Dict[str, List[Tuple[AnalysisSummary, Optional[str]]]]]] = dict()
        return

    def add_result(self, analysis_result: AnalysisResult) -> None:
        tool_name, app_name, bug_id, _ = analysis_result.basic_info()
        analysis_summary: AnalysisSummary = analysis_result.summary
        html_file_name: Optional[str] = analysis_result.html_file_name
        if tool_name not in self.__summary:
            self.__summary[tool_name] = dict()
        if app_name not in self.__summary[tool_name]:
            self.__summary[tool_name][app_name] = dict()
        if bug_id not in self.__summary[tool_name][app_name]:
            self.__summary[tool_name][app_name][bug_id] = [(analysis_summary, html_file_name)]
        else:
            self.__summary[tool_name][app_name][bug_id].append((analysis_summary, html_file_name))
        return

    def data(self):
        return self.__summary

    def __repr__(self) -> str:
        return "DDroid Analysis Result Summary"

    def __str__(self) -> str:
        representation: str = ""
        for tool in sorted(self.__summary.keys()):
            representation += f"\n<{str(tool)}>\n"
            for app in sorted(self.__summary[tool].keys()):
                representation += f"[{str(app)}]\n"
                for bug in sorted(self.__summary[tool][app].keys()):
                    summaries: List[AnalysisSummary] = list(map(lambda x: x[0], self.__summary[tool][app][bug]))
                    representation += f"{bug} -> {str([summary.repr for summary in summaries])}\n"
        return representation


class Logger:
    __name__ = "Logger"

    def __init__(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.__logger = logging.getLogger(self.__name__)
        return

    def info(self, msg: str) -> None:
        self.__logger.info(msg)
        return

    def error(self, msg: str) -> None:
        self.__logger.error(msg)
        return

    def warning(self, msg: str) -> None:
        self.__logger.warning(msg)
        return
