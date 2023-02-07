import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from automata.fa.nfa import NFA

from dfa import DDroidDFA
from dtypes import NFATransitions, StringSet, Logger


class Convertor(Logger):
    """
    This class is used to convert .jff file to .json file, rebuild the NFA from that .json file
    and finally minimize the NFA to DDroidDFA.
    """
    __name__ = "Convertor"

    def __init__(self):
        """ Initialize the Convertor """
        super(Convertor, self).__init__()
        self.json_path: Path = Path("./converted_json.json")  # This path is fixed by tool PutFlap
        self.putflap_path: Path = Path('../tools/putflap.jar')

    def get_json_from_jff(self, nfa_path: Path) -> Tuple[bool, str]:
        """ Use tool PutFlap to convert a .jff file to a .json file"""

        if not self.putflap_path.exists():
            sys.exit(f"{self.putflap_path} does not exist!")

        if not nfa_path.exists():
            return False, f"{nfa_path} does not exist!"

        command: str = f"java -jar {self.putflap_path} convert -t json {nfa_path}"

        self.info(f"Executing \"{command}\"...")
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()

        if p.poll() == 0:
            self.info(f"Convert {nfa_path} to .json successfully!")
            return True, "Convert .jff to .json successfully!"
        else:
            self.error(f"Failed to convert {nfa_path} to .json.")
            return False, f"Failed to convert {nfa_path} to .json."

    def get_dfa_from_json(self) -> DDroidDFA:
        """ Get the DFA from the .json file converted from .jff """
        with self.json_path.open() as automata_json_file:
            automata_info = json.load(automata_json_file)
            raw_states: List = automata_info["conversions"][0]["result"]["states"]
            raw_transitions: List = automata_info["conversions"][0]["result"]["transitions"]

        self.info(f"The original NFA has {len(raw_states)} states and {len(raw_transitions)} edges.")
        init_state: str = ""
        final_states: StringSet = set()
        states: StringSet = set()
        transitions: NFATransitions = dict()
        names: Dict[int, str] = dict()
        input_symbols: StringSet = set()

        # Reconstruct the states of the nfa
        for state in raw_states:
            states.add(state["name"])
            names[state["id"]] = state["name"]
            if state["type"] == "INITIAL":
                init_state = state["name"]
            if state["type"] == "FINAL":
                final_states.add(state["name"])

        # Reconstruct the transitions of the nfa
        for raw_transition in raw_transitions:
            from_name, to_name = names[raw_transition["from"]], names[raw_transition["to"]]
            char_read = raw_transition["read"]
            input_symbols.add(char_read)
            if from_name not in transitions:
                transitions[from_name] = {char_read: {to_name}}
            else:
                if char_read not in transitions[from_name]:
                    transitions[from_name][char_read] = {to_name}
                else:
                    transitions[from_name][char_read].add(to_name)

        for final_state in final_states:
            if final_state not in transitions:
                transitions[final_state] = dict()

        dfa: DDroidDFA = DDroidDFA.from_nfa(NFA(
            states=states,
            input_symbols=input_symbols,
            transitions=transitions,
            initial_state=init_state,
            final_states=final_states
        ))

        self.info("Build a DFA from .json successfully.")
        self.json_path.unlink()
        return dfa
