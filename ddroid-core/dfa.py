from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import automata.base.exceptions as exceptions
from automata.fa.dfa import DFA

from dtypes import StringSet, DFATransitions, Event, EventPair, Distances


class DDroidDFA(DFA):
    """ An DFA implementation that fits DDroid's needs """

    def __init__(self, *, states: StringSet, input_symbols: StringSet, transitions: DFATransitions, initial_state: str, final_states: StringSet,
                 allow_partial=False):
        super().__init__(states=states,
                         input_symbols=input_symbols,
                         transitions=transitions,
                         initial_state=initial_state,
                         final_states=final_states,
                         allow_partial=allow_partial)
        # Add this to record the current state of the DFA
        self.__current_state: str = initial_state
        # A dict recording the distance to the final state from each state
        self.__minimal_distances: Dict[str, int] = self.__initialize_minimal_distances()

        self.__events: Dict[str, Event] = dict()
        self.__event_pairs: Dict[str, EventPair] = dict()
        self.__distances: Distances = Distances(self.now_distance())
        self.__last_event: Optional[Event] = None

    def init(self, event_info: Dict[str, Dict[str, str]], event_warning: Dict[str, str]):
        self.__events = self.__initialize_events(event_info, event_warning)
        self.__event_pairs = self.__initialize_event_pairs()

    def metrics(self) -> Tuple[Dict[str, Event], Dict[str, EventPair], Distances]:
        return self.__events, self.__event_pairs, self.__distances

    def __reset(self):
        self.__current_state = self.initial_state
        self.__last_event = None

    def is_valid_event(self, event: str) -> bool:
        """ To validate an event """
        return event in self.transitions[self.__current_state] and self.transitions[self.__current_state][event] != "{}"

    def input_symbols_contains(self, event: str):
        """ Check whether the event is in input symbols """
        return event in self.input_symbols

    def trigger_event(self, event: str, trigger_time: timedelta, new: bool = True) -> bool:
        """ Change the state of the DFA according to the transitions """
        if new:
            self.__events[event].trigger_at(trigger_time)
            self.__trigger_event_pair(event, trigger_time)
            self.__last_event = self.__events[event]
        try:
            old_state = self.__current_state
            self.__current_state = self._get_next_current_state(self.__current_state, event)
            if self.__current_state == "{}":
                raise exceptions.RejectionException
            self.__record_distance()
        except exceptions.RejectionException:
            self.__reset()
            return False
        if self.__current_state in self.final_states:
            self.__reset()
        return True

    def trigger_warning(self, warning: str, trigger_time: timedelta = None) -> bool:
        self.__events[warning].trigger_warning_at(trigger_time)
        return True

    def __trigger_event_pair(self, event: str, trigger_time: timedelta) -> None:
        """ Trigger event pair """
        if self.__last_event is not None:
            event_pair = self.__event_pairs.get(f"({repr(self.__last_event)}, Event {event})")
            if isinstance(event_pair, EventPair):
                event_pair.trigger_at(trigger_time)
        return

    def __record_distance(self) -> None:
        """ Record the current minimal distance from the current state to the final state """
        self.__distances.reach_distance(self.now_distance())

    def now_distance(self) -> int:
        """ Return the distance to the final state from the current state """
        return self.__minimal_distances[self.__current_state]

    def __initialize_events(self, event_info: Dict[str, Dict[str, str]], event_warning: Dict[str, str]) -> Dict[str, Event]:
        return {eid: Event(_id=eid, _description=event["info"], _reason=event["reason"],
                           _dependency=event["dependency"], _warning=event_warning.get(eid))
                for eid, event in event_info.items() if eid in self.input_symbols}

    def __initialize_event_pairs(self) -> Dict[str, EventPair]:
        event_pairs: Dict[str, EventPair] = dict()
        for from_state in self.transitions:
            for first_event in self.transitions[from_state]:
                if first_event != '' and self.transitions[from_state][first_event] != "{}":
                    to_state = self.transitions[from_state][first_event]
                    for second_event in self.transitions[to_state]:
                        if second_event != '' and self.transitions[to_state][second_event] != "{}":
                            event_pairs.setdefault(f"(Event {first_event}, Event {second_event})", EventPair((first_event, second_event)))
        return event_pairs

    def __initialize_minimal_distances(self) -> Dict[str, int]:
        """ Compute the shortest distance from every state to the final state using Floyd algorithm """
        states: StringSet = self.states
        if '{}' in states:
            states.remove('{}')
        final_state: str = self.final_states.copy().pop()

        # Init the DFA graph
        graph: Dict[str, Dict[str, int]] = dict()
        for from_state in states:
            # if from_state == '{}':
            #     continue
            graph[from_state] = dict()
            to_states: StringSet = self.transitions[from_state].values()
            for to_state in states:
                # if to_state == '{}':
                #     continue
                if to_state == from_state:  # The distance from itself to itself is 0
                    graph[from_state][to_state] = 0
                elif to_state in to_states:  # There is an edge between from_state and to_state
                    graph[from_state][to_state] = 1
                else:
                    graph[from_state][to_state] = 1000

        # Floyd algorithm
        for i in states:
            for j in states:
                for k in states:
                    if graph[j][i] + graph[i][k] < graph[j][k]:
                        graph[j][k] = graph[j][i] + graph[i][k]

        # Get the shortest distance from every state in the DFA to the final state
        ret: Dict[str, int] = dict()
        for i in states:
            ret[i] = graph[i][final_state]

        return ret
