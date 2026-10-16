import json
import os
from pathlib import Path
from typing import Any

import torch
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from sentence_transformers import SentenceTransformer


class RichEventIngester:
    skip_types: frozenset[str] = frozenset(
        {
            "Ball Receipt*",
            "Starting XI",
            "Half Start",
            "Half End",
            "Tactical Shift",
            "Player Off",
            "Player On",
            "Referee Ball-Drop",
            "Camera On",
            "Camera off",
        }
    )

    def __init__(
        self,
        host: str,
        index: str,
        events_dir: Path,
        max_matches: int | None,
        model_name: str,
    ) -> None:
        self._host: str = host
        self._index: str = index
        self._events_dir: Path = events_dir
        self._max_matches: int | None = max_matches
        self._model_name: str = model_name
        self._model: Any | None = None
        self._client: Elasticsearch | None = None
        self._skipped: int = 0

    def get_client(self) -> Elasticsearch:
        if self._client is None:
            self._client = Elasticsearch(self._host)
        return self._client

    def get_model(self) -> Any:
        if self._model is None:
            dtype: Any = (
                torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float32
            )
            self._model = SentenceTransformer(
                self._model_name, model_kwargs={"torch_dtype": dtype}
            )
        return self._model

    def describe_phase(self, minute: int, period: int) -> str:
        if minute >= 85:
            return "in the final minutes late in the game"
        if minute >= 75:
            return "late in the game"
        if minute <= 15 and period == 1:
            return "early in the game"
        if period == 1:
            return "in the first half"
        return "in the second half"

    def describe_zone(self, location: Any) -> str:
        if not isinstance(location, list) or len(location) < 2:
            return ""
        try:
            x: float = float(location[0])
            y: float = float(location[1])
        except (TypeError, ValueError):
            return ""
        parts: list[str] = []
        if 35.0 <= x <= 85.0 and 25.0 <= y <= 55.0:
            parts.append("in central midfield")
        elif x <= 40.0:
            parts.append("deep in the defensive third")
        elif x >= 80.0:
            parts.append("high up in the attacking third in the final third")
        else:
            parts.append("in the middle third of midfield")
        if y < 20.0 or y > 60.0:
            parts.append("out wide")
        elif not parts[0].startswith("in central"):
            parts.append("in a central area")
        return " ".join(parts)

    def describe_box_entry(self, end_location: Any) -> str:
        if not isinstance(end_location, list) or len(end_location) < 2:
            return ""
        try:
            ex: float = float(end_location[0])
            ey: float = float(end_location[1])
        except (TypeError, ValueError):
            return ""
        if (ex >= 102.0 or ex <= 18.0) and 18.0 <= ey <= 62.0:
            return "into the penalty box"
        return ""

    def extract_outcome(self, event: dict[str, Any], event_type: str) -> str | None:
        if event_type == "Shot":
            outcome: Any = event.get("shot", {}).get("outcome", {}).get("name")
            return str(outcome) if outcome else None
        if event_type == "Pass":
            outcome = event.get("pass", {}).get("outcome", {}).get("name")
            return str(outcome) if outcome else "Complete"
        if event_type == "Dribble":
            outcome = event.get("dribble", {}).get("outcome", {}).get("name")
            return str(outcome) if outcome else None
        if event_type == "Foul Committed":
            card: Any = event.get("foul_committed", {}).get("card", {}).get("name")
            return str(card) if card else None
        if event_type == "Bad Behaviour":
            card = event.get("bad_behaviour", {}).get("card", {}).get("name")
            return str(card) if card else None
        if event_type == "Goal Keeper":
            action: Any = event.get("goalkeeper", {}).get("type", {}).get("name")
            return str(action) if action else None
        if event_type == "Duel":
            result: Any = event.get("duel", {}).get("outcome", {}).get("name")
            if result:
                return str(result)
            return str(event.get("duel", {}).get("type", {}).get("name") or "")
        if event_type == "50/50":
            result = event.get("50_50", {}).get("outcome", {}).get("name")
            return str(result) if result else None
        return None

    def is_goal_event(self, event: dict[str, Any], event_type: str) -> bool:
        if event_type == "Shot":
            return event.get("shot", {}).get("outcome", {}).get("name") == "Goal"
        if event_type == "Goal Keeper":
            action: Any = event.get("goalkeeper", {}).get("type", {}).get("name")
            return action in ("Goal Conceded", "Penalty Conceded")
        return event_type in ("Own Goal For", "Own Goal Against")

    def is_key_pass(self, event: dict[str, Any]) -> bool:
        detail: dict[str, Any] = event.get("pass", {})
        return bool(detail.get("shot_assist") or detail.get("goal_assist"))

    def is_goal_assist(self, event: dict[str, Any]) -> bool:
        return bool(event.get("pass", {}).get("goal_assist"))

    def is_through_ball(self, event: dict[str, Any]) -> bool:
        return bool(event.get("pass", {}).get("through_ball"))

    def is_cross(self, event: dict[str, Any]) -> bool:
        return bool(event.get("pass", {}).get("cross"))

    def read_float(self, value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def format_shot(
        self,
        event: dict[str, Any],
        player: str,
        team: str,
        stamp: str,
        phase: str,
        zone: str,
        outcome: str | None,
        is_goal: bool,
    ) -> str:
        stats: dict[str, Any] = event.get("shot", {})
        xg: float | None = self.read_float(stats.get("statsbomb_xg", 0.0))
        xg_value: float = xg if xg is not None else 0.0
        outcome_text: str = str(outcome or "missed").lower()
        body: str = str(stats.get("body_part", {}).get("name") or "").lower()
        body_text: str = f" with {body}" if body else ""
        first_time: str = " first-time" if stats.get("first_time") is True else ""
        one_on_one: str = " one-on-one" if stats.get("one_on_one") is True else ""
        if xg_value >= 0.30:
            xg_text: str = (
                f"a high expected goals chance with xG {xg_value:.2f}, "
                f"a big scoring chance"
            )
        elif xg_value >= 0.12:
            xg_text = f"a good attacking chance with xG {xg_value:.2f}"
        else:
            xg_text = f"a low xG effort with xG {xg_value:.2f}"
        if is_goal:
            return (
                f"{stamp}, {player} for {team} scored a goal with a{first_time}"
                f"{one_on_one} shot{body_text} ({xg_text}). Goal scored, shot "
                f"resulting in a goal {zone} {phase}. Goals scored {phase}."
            )
        if outcome in ("Post", "Saved to Post"):
            return (
                f"{stamp}, {player} for {team} hit the woodwork with a"
                f"{first_time} shot{body_text} ({xg_text}), a missed opportunity "
                f"off the post {zone} {phase}."
            )
        if outcome in ("Off T", "Wayward"):
            return (
                f"{stamp}, {player} for {team} missed a shot{body_text} ({xg_text}), "
                f"a missed opportunity off target {zone} {phase}."
            )
        if outcome == "Blocked":
            return (
                f"{stamp}, {player} for {team} saw a shot{body_text} blocked "
                f"({xg_text}), a blocked goal attempt {zone} {phase}."
            )
        if outcome in ("Saved", "Saved Off Target"):
            return (
                f"{stamp}, {player} for {team} forced a save with a shot{body_text} "
                f"({xg_text}), a saved goal attempt {zone} {phase}."
            )
        return (
            f"{stamp}, {player} for {team} attempted a shot, a goal attempt "
            f"{body_text} with xG {xg_value:.2f}, resulting in {outcome_text} "
            f"{zone} {phase}."
        )

    def format_pass(
        self,
        event: dict[str, Any],
        player: str,
        team: str,
        stamp: str,
        phase: str,
        zone: str,
        outcome: str | None,
    ) -> str:
        detail: dict[str, Any] = event.get("pass", {})
        recipient: str = str(detail.get("recipient", {}).get("name") or "a teammate")
        outcome_text: str = str(outcome or "Complete").lower()
        box: str = self.describe_box_entry(detail.get("end_location"))
        pass_kind: str = str(detail.get("type", {}).get("name") or "")
        kind_text: str = f" from a {pass_kind.lower()}" if pass_kind else ""
        length: float | None = self.read_float(detail.get("length"))
        length_text: str = ""
        if length is not None:
            if length >= 30.0:
                length_text = f" a long {length:.0f} meter pass"
            elif length <= 10.0:
                length_text = " a short pass"
        pressure: str = (
            " under immediate opponent pressure"
            if event.get("under_pressure") is True
            else ""
        )
        extras: list[str] = []
        if detail.get("goal_assist"):
            extras.append(
                "a key pass leading directly to a goal, a goal assist creating "
                "an attacking chance"
            )
        elif detail.get("shot_assist"):
            extras.append(
                "a key pass leading directly to an attacking chance, a shot "
                "assist creating a shot"
            )
        if detail.get("through_ball"):
            extras.append("a through ball splitting the defence")
        if detail.get("cross"):
            extras.append("a cross into the box")
        if detail.get("cut_back"):
            extras.append("a cut-back across goal")
        if detail.get("switch"):
            extras.append("a switch of play")
        extra_text: str = ", ".join(extras)
        if box:
            if extra_text:
                extra_text = f"{extra_text} {box}"
            else:
                extra_text = f"a pass {box}"
        if extra_text:
            return (
                f"{stamp}, {player} for {team} played{length_text}{kind_text} to "
                f"{recipient}{pressure}, {extra_text}, which was {outcome_text} "
                f"{zone} {phase}."
            )
        return (
            f"{stamp}, {player} for {team} attempted{length_text}{kind_text} a pass "
            f"to {recipient}{pressure}, a completed pass attempt which was "
            f"{outcome_text} {zone} {phase}."
        )

    def format_carry(
        self,
        event: dict[str, Any],
        player: str,
        team: str,
        stamp: str,
        phase: str,
        zone: str,
    ) -> str:
        detail: dict[str, Any] = event.get("carry", {})
        start: Any = event.get("location")
        end: Any = detail.get("end_location")
        progress: str = "a ball carry progression"
        if (
            isinstance(start, list)
            and isinstance(end, list)
            and len(start) >= 1
            and len(end) >= 1
        ):
            start_x: float | None = self.read_float(start[0])
            end_x: float | None = self.read_float(end[0])
            if start_x is not None and end_x is not None:
                gain: float = end_x - start_x
                if gain >= 12.0:
                    progress = (
                        "an attacking ball carry breaking through the lines, "
                        "driving deep into opposition territory"
                    )
                elif gain >= 5.0:
                    progress = "a progressive ball carry moving upfield"
        return (
            f"{stamp}, {player} for {team} made {progress}, carrying the ball "
            f"forward {zone} {phase}."
        )

    def format_duel(
        self,
        event: dict[str, Any],
        player: str,
        team: str,
        stamp: str,
        phase: str,
        zone: str,
        outcome: str | None,
    ) -> str:
        duel: dict[str, Any] = event.get("duel", {})
        duel_type: str = str(duel.get("type", {}).get("name") or "duel").lower()
        if duel_type.startswith("aerial"):
            kind: str = "an aerial duel"
        elif duel_type == "tackle":
            kind = "a tackle duel, a ground duel"
        else:
            kind = f"a {duel_type} duel"
        if outcome in ("Won", "Success", "Success In Play") or (
            isinstance(outcome, str) and "Won" in outcome and "Lost" not in outcome
        ):
            result: str = "won the duel against his opponent"
        elif (
            outcome in ("Lost", "Lost In Play", "Lost Out")
            or "Lost" in str(outcome or "")
            or "Aerial Lost" in str(outcome or "")
        ):
            result = "lost the duel against his opponent"
        else:
            result = "contested the duel against his opponent"
        return (
            f"{stamp}, {player} for {team} contested {kind} and {result} "
            f"{zone} {phase}."
        )

    def format_foul(
        self,
        event: dict[str, Any],
        player: str,
        team: str,
        stamp: str,
        phase: str,
        zone: str,
        outcome: str | None,
    ) -> str:
        detail: dict[str, Any] = event.get("foul_committed", {})
        card: str = str(outcome or "no card").lower()
        if card == "yellow card":
            card_text: str = "a yellow card booking"
        elif card == "red card":
            card_text = "a red card sending off"
        else:
            card_text = "no card"
        foul_type: str = str(detail.get("type", {}).get("name") or "")
        type_text: str = f" a {foul_type.lower()} foul" if foul_type else " a foul"
        return (
            f"{stamp}, {player} for {team} committed{type_text} resulting in "
            f"{card_text} {zone} {phase}."
        )

    def format_keeper(
        self,
        event: dict[str, Any],
        player: str,
        team: str,
        stamp: str,
        phase: str,
        zone: str,
        outcome: str | None,
        is_goal: bool,
    ) -> str:
        action: str = str(outcome or "action")
        action_text: str = action.lower()
        pressure: str = (
            " under high pressure" if event.get("under_pressure") is True else ""
        )
        if is_goal:
            return (
                f"{stamp}, goalkeeper {player} for {team} conceded a goal, "
                f"a goal conceded from a shot faced ({action_text}). Goal scored "
                f"against {zone} {phase}."
            )
        if action in ("Keeper Sweeper",):
            return (
                f"{stamp}, goalkeeper {player} for {team} rushed out as a sweeper "
                f"keeper to claim the ball outside the box {zone} {phase}."
            )
        if action in ("Collected",):
            return (
                f"{stamp}, goalkeeper {player} for {team} claimed a cross, "
                f"collecting the ball cleanly{pressure} {zone} {phase}."
            )
        if action in ("Punch",):
            return (
                f"{stamp}, goalkeeper {player} for {team} punched the ball clear, "
                f"a punch under pressure {zone} {phase}."
            )
        return (
            f"{stamp}, goalkeeper {player} for {team} made a high-pressure save, "
            f"a goalkeeper {action_text} stop facing a shot{pressure} {zone} "
            f"{phase}."
        )

    def format_narrative(self, event: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        player: str = str(event.get("player", {}).get("name") or "Unknown Player")
        team: str = str(event.get("team", {}).get("name") or "Unknown Team")
        event_type: str = str(event.get("type", {}).get("name") or "Unknown")
        minute: int = int(event.get("minute", 0))
        second: int = int(event.get("second", 0))
        period: int = int(event.get("period", 1))
        phase: str = self.describe_phase(minute, period)
        zone: str = self.describe_zone(event.get("location"))
        outcome: str | None = self.extract_outcome(event, event_type)
        is_goal: bool = self.is_goal_event(event, event_type)
        stamp: str = f"At {minute}:{second:02d} in period {period} {phase}"
        narrative: str
        if event_type == "Shot":
            narrative = self.format_shot(
                event, player, team, stamp, phase, zone, outcome, is_goal
            )
        elif event_type == "Pass":
            narrative = self.format_pass(
                event, player, team, stamp, phase, zone, outcome
            )
        elif event_type == "Carry":
            narrative = self.format_carry(event, player, team, stamp, phase, zone)
        elif event_type == "Duel":
            narrative = self.format_duel(
                event, player, team, stamp, phase, zone, outcome
            )
        elif event_type == "Foul Committed":
            narrative = self.format_foul(
                event, player, team, stamp, phase, zone, outcome
            )
        elif event_type == "Bad Behaviour":
            card_text = str(outcome or "no card").lower()
            if card_text == "yellow card":
                card_text = "a yellow card booking"
            elif card_text == "red card":
                card_text = "a red card sending off"
            narrative = (
                f"{stamp}, {player} for {team} was booked for bad behaviour, "
                f"misconduct resulting in {card_text} {zone} {phase}."
            )
        elif event_type == "Foul Won":
            detail = event.get("foul_won", {})
            defensive_text: str = (
                " in a defensive duel, winning back possession"
                if detail.get("defensive") is True
                else ""
            )
            advantage_text: str = (
                " with advantage played" if detail.get("advantage") is True else ""
            )
            narrative = (
                f"{stamp}, {player} for {team} won a foul, drawing a foul from "
                f"an opponent{defensive_text}{advantage_text} {zone} {phase}."
            )
        elif event_type == "Dribbled Past":
            narrative = (
                f"{stamp}, {player} for {team} was beaten by a dribble, dribbled "
                f"past by an opponent breaking the defensive line {zone} {phase}."
            )
        elif event_type == "Substitution":
            detail = event.get("substitution", {})
            replacement: str = str(
                detail.get("replacement", {}).get("name") or "a substitute"
            )
            reason: str = str(detail.get("outcome", {}).get("name") or "").lower()
            reason_text: str = f" due to {reason}" if reason else ""
            narrative = (
                f"{stamp}, {player} for {team} was substituted off{reason_text}, "
                f"replaced by {replacement} {phase}."
            )
        elif event_type == "Injury Stoppage":
            narrative = (
                f"{stamp}, play stopped for an injury involving {player} for "
                f"{team}, an injury stoppage {zone} {phase}."
            )
        elif event_type == "Own Goal Against":
            narrative = (
                f"{stamp}, {player} for {team} scored an own goal, putting the "
                f"ball through his own net. Own goal conceded {zone} {phase}."
            )
        elif event_type == "Own Goal For":
            narrative = (
                f"{stamp}, {team} benefited from an own goal involving {player}, "
                f"an own goal scored in their favour {zone} {phase}."
            )
        elif event_type == "Offside":
            narrative = (
                f"{stamp}, {player} for {team} was caught offside, an offside "
                f"offence stopping the attack {zone} {phase}."
            )
        elif event_type == "Error":
            narrative = (
                f"{stamp}, {player} for {team} made an error, a costly mistake "
                f"gifting the opponent a turnover {zone} {phase}."
            )
        elif event_type == "50/50":
            if outcome in ("Won", "Success", "Success In Play"):
                duel_result: str = "winning the duel"
            elif outcome in ("Lost", "Lost In Play", "Lost Out"):
                duel_result = "losing the duel"
            else:
                duel_result = "contesting the duel"
            narrative = (
                f"{stamp}, {player} for {team} contested a 50/50 duel, an even "
                f"loose-ball duel, {duel_result} against his opponent {zone} "
                f"{phase}."
            )
        elif event_type == "Shield":
            narrative = (
                f"{stamp}, {player} for {team} shielded the ball, shielding "
                f"possession from an opponent {zone} {phase}."
            )
        elif event_type == "Goal Keeper":
            narrative = self.format_keeper(
                event, player, team, stamp, phase, zone, outcome, is_goal
            )
        elif event_type == "Pressure":
            counter: str = (
                " as an immediate counterpress"
                if event.get("counterpress") is True
                else ""
            )
            narrative = (
                f"{stamp}, {player} for {team} applied defensive pressure, "
                f"pressing an opponent{counter} {zone} {phase}."
            )
        elif event_type == "Ball Recovery":
            narrative = (
                f"{stamp}, {player} for {team} made a successful ball recovery, "
                f"immediately regaining possession {zone} {phase}."
            )
        elif event_type == "Block":
            narrative = (
                f"{stamp}, {player} for {team} made a defensive block, stopping a "
                f"goal-bound shot or pass {zone} {phase}."
            )
        elif event_type == "Clearance":
            narrative = (
                f"{stamp}, {player} for {team} made a clearance under heavy "
                f"pressure, clearing the ball from the danger zone {zone} {phase}."
            )
        elif event_type == "Interception":
            narrative = (
                f"{stamp}, {player} for {team} made an interception, cutting off "
                f"an opponent passing lane {zone} {phase}."
            )
        elif event_type == "Dribble":
            outcome_text: str = str(outcome or "complete").lower()
            if outcome in ("Complete", None):
                result_text: str = "beating his man and dribbling past an opponent"
            else:
                result_text = "failing to dribble past an opponent"
            narrative = (
                f"{stamp}, {player} for {team} attempted a dribble, {result_text}, "
                f"which was {outcome_text} {zone} {phase}."
            )
        elif event_type == "Miscontrol":
            press_text: str = (
                " under pressure" if event.get("under_pressure") is True else ""
            )
            narrative = (
                f"{stamp}, {player} for {team} miscontrolled the ball{press_text}, "
                f"a miscontrol causing a sudden turnover {zone} {phase}."
            )
        elif event_type == "Dispossessed":
            narrative = (
                f"{stamp}, {player} for {team} was dispossessed, tackled and "
                f"dispossessed in a transitional duel {zone} {phase}."
            )
        else:
            narrative = (
                f"{stamp}, {player} for {team} performed a {event_type} action, "
                f"a {event_type.lower()} event {zone} {phase}."
            )
        xg_value: float | None = self.read_float(
            event.get("shot", {}).get("statsbomb_xg")
        )
        structured: dict[str, Any] = {
            "event_type": event_type,
            "outcome": outcome,
            "period": period,
            "second": second,
            "minute": minute,
            "is_goal": is_goal,
            "is_key_pass": self.is_key_pass(event) if event_type == "Pass" else False,
            "is_goal_assist": self.is_goal_assist(event)
            if event_type == "Pass"
            else False,
            "is_through_ball": self.is_through_ball(event)
            if event_type == "Pass"
            else False,
            "is_cross": self.is_cross(event) if event_type == "Pass" else False,
            "under_pressure": event.get("under_pressure") is True,
            "xg": xg_value,
        }
        loc: Any = event.get("location")
        if isinstance(loc, list) and len(loc) >= 2:
            structured["location_x"] = self.read_float(loc[0])
            structured["location_y"] = self.read_float(loc[1])
        else:
            structured["location_x"] = None
            structured["location_y"] = None
        return narrative, structured

    def list_event_files(self) -> list[Path]:
        files: list[Path] = sorted(self._events_dir.glob("*.json"))
        if self._max_matches is not None:
            return files[: self._max_matches]
        return files

    def generate_actions(self) -> Any:
        model: Any = self.get_model()
        files: list[Path] = self.list_event_files()
        if not files:
            print("No event files found.")
            return
        for file_path in files:
            match_id: str = file_path.stem
            with open(file_path, encoding="utf-8") as handle:
                events: Any = json.load(handle)
            for event in events:
                event_id: Any = event.get("id")
                if not event_id:
                    continue
                if event.get("type", {}).get("name") in self.skip_types:
                    self._skipped += 1
                    continue
                narrative: str
                structured: dict[str, Any]
                narrative, structured = self.format_narrative(event)
                prefixed_text: str = f"title: none | text: {narrative}"
                vector: Any = model.encode(
                    prefixed_text, normalize_embeddings=True
                ).tolist()
                yield {
                    "_index": self._index,
                    "_id": event_id,
                    "_source": {
                        "event_id": event_id,
                        "match_id": match_id,
                        "team": event.get("team", {}).get("name"),
                        "player": event.get("player", {}).get("name"),
                        "minute": structured["minute"],
                        "second": structured["second"],
                        "period": structured["period"],
                        "event_type": structured["event_type"],
                        "outcome": structured["outcome"],
                        "is_goal": structured["is_goal"],
                        "is_key_pass": structured["is_key_pass"],
                        "is_goal_assist": structured["is_goal_assist"],
                        "is_through_ball": structured["is_through_ball"],
                        "is_cross": structured["is_cross"],
                        "under_pressure": structured["under_pressure"],
                        "xg": structured["xg"],
                        "location_x": structured["location_x"],
                        "location_y": structured["location_y"],
                        "narrative": narrative,
                        "narrative_vector": vector,
                    },
                }

    def run(self) -> tuple[int, int]:
        print("Starting bulk indexing of parsed match events into Elasticsearch...")
        success: int
        failed: int
        success, failed = bulk(
            self.get_client(),
            self.generate_actions(),
            chunk_size=500,
            raise_on_error=False,
        )
        print(f"Successfully indexed {success} documents. Failed: {failed}")
        print(f"Skipped {self._skipped} low-signal events.")
        return success, failed


def build_from_env() -> RichEventIngester:
    host: str = os.environ.get("ELASTICSEARCH_HOST", "http://localhost:9200")
    index: str = os.environ.get("INDEX_NAME", "statsbomb_events")
    data_dir: Path = Path(os.environ.get("DATA_DIR", "statsbomb-rag-data/data"))
    raw_max: str | None = os.environ.get("MAX_MATCHES")
    max_matches: int | None = int(raw_max) if raw_max else 3
    model_name: str = os.environ.get("EMBEDDING_MODEL", "google/embeddinggemma-2")
    return RichEventIngester(
        host=host,
        index=index,
        events_dir=data_dir / "events",
        max_matches=max_matches,
        model_name=model_name,
    )


if __name__ == "__main__":
    build_from_env().run()
