from argparse import ArgumentParser, Namespace

from analyze import Analyzer
from dtypes import AnalysisOptions, Logger

if __name__ == "__main__":
    logger = Logger()

    parser = ArgumentParser(prog="DDroid Core Analyzer", usage="analyze the output logs.")
    parser.add_argument("target_dir", help="the output logs dir that to be analyzed")

    parser.add_argument(
        "-v",
        "--html",
        action="store_true",
        default=False,
        help="let the FA wait at the current state when mismatching"
    )

    parser.add_argument(
        "-d",
        "--detail",
        action="store_true",
        default=False,
        help="Show more details"
    )

    parser.add_argument(
        "-b",
        "--batch",
        action="store_true",
        default=False,
        help="Parse the argument `target_dir` as the parent dir of result dirs"
    )

    args: Namespace = parser.parse_args()
    options: AnalysisOptions = AnalysisOptions(args.target_dir, args.html, args.batch)
    logger.info("ARGUMENTS:\n"
                + f"    > Target directory: {options.target_dir()}\n"
                # + "    > Use detailed output?   [%s]\n" % args.detail
                + f"    > Use web output? {options.is_html_output()}\n"
                + f"    > Use batch analysis? {options.is_batch_analysis()}")

    analyzer: Analyzer = Analyzer(options)
    analyzer.initialize()
    analyzer.run()
