import os
from pathlib import Path
from typing import Union, Tuple, Optional

from jinja2 import Environment, FileSystemLoader

from dtypes import AnalysisResult, AnalysisResultSummary, AnalysisBasicInfo, Logger


class TerminalPrinter(Logger):
    """ This class is used to print the analysis result to terminal without any other output """
    __name__ = "TerminalPrinter"

    def __init__(self):
        super(TerminalPrinter, self).__init__()
        return

    def print(self, data: Union[AnalysisResult, AnalysisResultSummary]) -> None:
        self.info(str(data))
        return


class HTMLGenerator(Logger):
    """ This class is used to generate an HTML page using the analysis result like JUnit """
    __name__ = "HTMLGenerator"

    def __init__(self, timestamp: str):
        super().__init__()
        self.__timestamp: str = timestamp
        self.__result_template: str = "resulttmpl.html"
        self.__summary_template: str = "summarytmpl.html"
        self.__result_directory: Path = Path(os.path.join("..", "ddroid-result"))
        # Use the timestamp as the output directory name
        self.__current_result_directory: Path = self.__result_directory / self.__timestamp  # os.path.join(self.__result_directory, self.__timestamp)
        self.__template_env = Environment(loader=FileSystemLoader("./templates/"))
        return

    def __check_or_create_dirs(self) -> None:
        if not self.__result_directory.exists() or not self.__result_directory.is_dir():
            self.__result_directory.mkdir()
        if not self.__current_result_directory.exists() or not self.__current_result_directory.is_dir():
            self.__current_result_directory.mkdir()
        return

    def __analysis_result_to_html(self, data: AnalysisResult) -> Tuple[Path, str]:
        """ Generate a single html file from a AnalysisResult"""
        self.__check_or_create_dirs()
        basic_info: AnalysisBasicInfo = data.basic_info()
        template = self.__template_env.get_template(self.__result_template)
        title = repr(data)

        events = data.events()
        event_pairs = data.event_pairs()

        event_coverage = [sum(1 for event in events if event.count() > 0)]
        event_coverage.append(len(events) - event_coverage[0])

        event_pair_coverage = [sum(1 for event_pair in event_pairs if event_pair.count() > 0)]
        event_pair_coverage.append(len(event_pairs) - event_pair_coverage[0])

        html_path = self.__current_result_directory / f"{basic_info.dir_name.replace('#', '')}.html"
        content: str = template.render(
            title=title,
            timestamp=self.__timestamp,
            target=basic_info.dir_name,
            events=events,
            event_coverage=event_coverage,
            event_pairs=event_pairs,
            event_pair_coverage=event_pair_coverage,
            distances=data.distances()
        )
        return html_path, content

    def __analysis_result_summary_to_html(self, data: AnalysisResultSummary) -> Tuple[Path, str]:
        """ Generate the summary html from AnalysisResultSummary"""
        self.__check_or_create_dirs()
        template = self.__template_env.get_template(self.__summary_template)
        title = repr(data)

        html_path = self.__current_result_directory / "main.html"
        content = template.render(
            title=title,
            timestamp=self.__timestamp,
            summary=data.data()
        )
        return html_path, content

    def generate(self, data: Union[AnalysisResult, AnalysisResultSummary]) -> Path:
        """ Generate the html """
        self.info(f"Generating result report of {repr(data)}")
        file_name: Optional[Path] = None
        file_content: Optional[str] = None

        if isinstance(data, AnalysisResult):
            file_name, file_content = self.__analysis_result_to_html(data)
            data.html_file_name = os.path.basename(file_name)
        if isinstance(data, AnalysisResultSummary):
            file_name, file_content = self.__analysis_result_summary_to_html(data)

        if file_name is None or file_content is None:
            raise RuntimeError(f"Error in generating result report of {repr(data)}")

        file_name.write_text(file_content)
        return file_name


class Displayer:
    """ Analysis result displayer """
    __name__ = "Displayer"

    def __init__(self, _is_html_output: bool, timestamp: str):
        self.__terminal_printer: TerminalPrinter = TerminalPrinter()
        self.__html_generator: HTMLGenerator = HTMLGenerator(timestamp)
        self.__is_html_output: bool = _is_html_output
        return

    def display(self, data: Union[AnalysisResult, AnalysisResultSummary]) -> None:
        """ Display the result """
        if self.__is_html_output:
            self.__html_generator.generate(data)
        else:
            self.__terminal_printer.print(data)
        return
