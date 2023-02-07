import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from convert import Convertor
from dfa import DDroidDFA
from display import Displayer
from dtypes import AnalysisOptions, AnalysisResult, AnalysisResultSummary, Logger
from error import StartTimeValueError, DFAInitializationError
from utils import get_name, get_time_format, line_type_of, line_id_of


class AnalysisCore(Logger):
    """
    This class is utilized to perform the main analysis
    """
    __name__ = "AnalysisCore"

    def __init__(self, first_init: bool = False):
        if first_init:
            super().__init__()
        self.__target_dir: Path = Path()
        # File paths
        self.__configuration_path: Path = Path()
        self.__nfa_path: Path = Path()
        self.__logcat_path: Path = Path()
        self.__time_record_path: Path = Path()

        self.__tool_name: str = ""
        self.__app_name: str = ""
        self.__bug_id: str = ""
        self.__reason: str = ""
        self.__convertor: Convertor = Convertor()
        self.__dfa: Optional[DDroidDFA] = None

        self.__crash_time: List[timedelta] = []
        return

    def set_target_dir(self, _target_dir: str) -> None:
        """ Set the target directory of the analysis """
        self.__init__()
        self.__target_dir = Path(_target_dir)
        self.__initialize()
        self.info(f"Finishing initialization for {_target_dir}")
        return

    def __initialize(self):
        """ Initialize all information and data stored in this class """
        self.__dir_name, self.__tool_name = self.__resolve_target_dir()
        base_info: Tuple[str, str, Dict, Dict, str] = self.__read_configuration()
        self.__app_name = base_info[0]
        self.__bug_id = base_info[1]
        self.__reason = base_info[4]
        self.__dfa = self.__initialize_dfa(base_info[2], base_info[3])

    def __resolve_target_dir(self) -> Tuple[str, str]:
        """ Initialize all the related files' paths """
        base_dir = os.path.basename(self.__target_dir)
        first_pos: Tuple[int, int] = re.search("instrumented-", base_dir).span()
        second_pos: Tuple[int, int] = re.search("-#", base_dir).span()
        third_pos: Tuple[int, int] = re.search(".apk.", base_dir).span()
        forth_pos: Tuple[int, int] = re.search(".result", base_dir).span()

        app_name: str = base_dir[first_pos[1]: second_pos[0]]
        bug_id: str = base_dir[second_pos[0] + 1: third_pos[0]]
        tool_name: str = get_name(base_dir[third_pos[1]: forth_pos[0]].lower())

        config_path = Path(os.path.join("..", app_name, f"configuration-{bug_id}.json"))
        if self.__check_file_exists(config_path):
            self.__configuration_path = config_path

        nfa_path = Path(os.path.join("..", app_name, f"{bug_id[1:]}-NFA.jff"))
        if self.__check_file_exists(nfa_path):
            self.__nfa_path = nfa_path

        logcat_path = Path(os.path.join(self.__target_dir, "logcat.log"))
        if self.__check_file_exists(logcat_path):
            self.__logcat_path = logcat_path

        time_record_path = Path(os.path.join(self.__target_dir, f"{tool_name}_testing_time_on_emulator.txt"))
        if self.__check_file_exists(time_record_path):
            self.__time_record_path = time_record_path

        return base_dir, tool_name

    def __read_configuration(self) -> Tuple[str, str, Dict, Dict, str]:
        with self.__configuration_path.open() as f:
            config = json.load(f)
            app_name: str = str(config["app_name"])
            bug_id: str = str(config["bug_id"])
            warnings: Dict[str, str] = config["warnings"]
            events: Dict[str, Dict[str, str]] = dict(config["events"])
            reason: str = config["all_events_happened"]
            return app_name, bug_id, events, warnings, reason

    def __initialize_dfa(self, event_info: Dict[str, Dict[str, str]], event_warning: Dict[str, str]) -> DDroidDFA:
        """ Initialize the DDroid DFA for analysis """
        success, msg = self.__convertor.get_json_from_jff(Path(self.__nfa_path))
        if success:
            dfa = self.__convertor.get_dfa_from_json()
            dfa.init(event_info, event_warning)
            return dfa
        else:
            raise DFAInitializationError(msg)

    def run(self) -> AnalysisResult:
        """ Execute the analysis """
        self.info(f"Start analyzing {self.__target_dir} result...")
        year: str = str(datetime.now().year)
        time_format: str = get_time_format(self.__tool_name)
        start_time: Optional[datetime] = None
        end_time: Optional[datetime] = None
        with self.__time_record_path.open() as time_file:
            try:
                start_time = datetime.strptime(time_file.readline().split("\n")[0], time_format)
                year = f"{str(start_time.year)}-"
            except ValueError:
                raise StartTimeValueError(f"The time value is incorrect in {self.__time_record_path}")
            try:
                end_time = datetime.strptime(time_file.readline().split("\n")[0], time_format)
            except ValueError:
                end_time = None
                # raise EndTimeValueError(f"The time value is incorrect in {self.__time_record_path}")

        now_time: Optional[datetime] = None
        with self.__logcat_path.open() as log:
            for line in log:

                if not line.startswith("---"):
                    split_line = line.split(" ")
                    now_time = datetime.strptime(f"{year}{split_line[0]} {split_line[1].split('.')[0]}", "%Y-%m-%d %H:%M:%S")

                if re.search("Themis", line):
                    # Get the trigger time
                    line_type, match_pos = line_type_of(line)
                    if line_type == "d-event":  # Process event
                        event_id = line_id_of(line, match_pos)
                        if not self.__dfa.input_symbols_contains(event_id):
                            continue
                        success: bool = self.__dfa.trigger_event(event_id, now_time - start_time)
                        if not success:
                            self.__dfa.trigger_event(event_id, now_time - start_time, False)
                    if line_type == "d-warning":  # Process warning
                        warning_id = line_id_of(line, match_pos)
                        if not self.__dfa.input_symbols_contains(warning_id):
                            continue
                        self.__dfa.trigger_warning(warning_id, now_time - start_time)
                    if line_type == "d-crash":  # Process crash
                        self.__crash_time.append(now_time - start_time)

        if end_time is None:
            end_time = now_time

        return AnalysisResult(self.__dir_name, app_name=self.__app_name, tool_name=self.__tool_name, bug_id=self.__bug_id, reason=self.__reason,
                              elapsed_time=end_time - start_time, crash_time=self.__crash_time,
                              metrics=self.__dfa.metrics())

    def __check_file_exists(self, file_path: Path) -> bool:
        """ Check existence of the given file """
        if file_path.exists():
            self.info(f"Using file {file_path}")
            return True
        else:
            self.error(f"{file_path} doesn't exists!")
            raise FileNotFoundError(f"{file_path} doesn't exists!")


class Analyzer(Logger):
    """
    The Analyzer of DDroid
    """
    __name__ = "Analyzer"

    def __init__(self, _options: AnalysisOptions):
        super(Analyzer, self).__init__()
        self.__options: AnalysisOptions = _options
        self.__work_list: List[str] = []  # Contains the DDroid log directories needed to analyze

        self.__timestamp: str = str(datetime.now()).replace(" ", "-").replace(":", "-")
        self.__error_list: List[str] = []

        self.__analysis_core: AnalysisCore = AnalysisCore(first_init=True)
        self.__displayer: Displayer = Displayer(self.is_html_output(), self.__timestamp)

    def get_target_dir(self) -> str:
        return self.__options.target_dir()

    def is_html_output(self) -> bool:
        return self.__options.is_html_output()

    def is_batch_analysis(self) -> bool:
        return self.__options.is_batch_analysis()

    def initialize(self) -> None:
        """ Initialize the work list """
        target_dir: str = self.get_target_dir()
        if self.is_batch_analysis():
            with os.scandir(target_dir) as dirs:
                self.__work_list = [os.path.join(target_dir, sub_dir.name)
                                    for sub_dir in dirs
                                    if sub_dir.name.find("instrumented-") != -1]
        else:
            self.__work_list = [target_dir]

        self.info(f"Analyzer initialized with {len(self.__work_list)} targets")
        return

    def run(self) -> None:
        """ Run the analyses """
        self.info(f"Analysis starts...")
        analysis_result_summary: AnalysisResultSummary = AnalysisResultSummary()
        for target in self.__work_list:
            try:
                self.__analysis_core.set_target_dir(target)
                result: AnalysisResult = self.__analysis_core.run()
                self.__displayer.display(result)
                analysis_result_summary.add_result(result)
            except RuntimeError as e:
                self.error(str(e))
                self.__error_list.append(target)
        self.__displayer.display(analysis_result_summary)
        # Print summary
        self.info(f"Analysis completed. Analyzed {len(self.__work_list)} targets, {len(self.__error_list)} failed")
        for idx, target in enumerate(self.__error_list):
            self.info(f"Analysis failure {idx}: {target}")

        return
