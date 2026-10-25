"""Golden Hour recovery flow state helpers."""

from dataclasses import dataclass, field
import json
import uuid

from kavach.db import session


@dataclass
class Conversation:
    state: str = "IDLE"
    data: dict = field(default_factory=dict)


def get_conversation(user_id: str) -> Conversation:
    with session() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,),
        )
        connection.execute(
            "INSERT OR IGNORE INTO conversations (user_id) VALUES (?)",
            (user_id,),
        )
        row = connection.execute(
            "SELECT state, data_json FROM conversations WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    return Conversation(
        state=row["state"],
        data=json.loads(row["data_json"] or "{}"),
    )


def save_conversation(user_id: str, conversation: Conversation) -> None:
    with session() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,),
        )
        connection.execute(
            """
            INSERT INTO conversations (user_id, state, data_json)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                state = excluded.state,
                data_json = excluded.data_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                conversation.state,
                json.dumps(conversation.data, ensure_ascii=False),
            ),
        )


def start(user_id: str) -> Conversation:
    case_id = uuid.uuid4().hex
    conversation = Conversation(
        state="GH_WAIT_EVIDENCE",
        data={"evidence_paths": [], "case_id": case_id},
    )

    # Save the conversation first, in its own committed transaction.
    save_conversation(user_id, conversation)

    # Then create the case in a separate transaction.
    with session() as connection:
        connection.execute(
            """
            INSERT INTO cases (case_id, user_id, status, evidence_json)
            VALUES (?, ?, 'collecting_evidence', '{}')
            """,
            (case_id, user_id),
        )

    return conversation


def add_evidence(user_id: str, file_path: str) -> Conversation:
    conversation = get_conversation(user_id)
    if conversation.state != "GH_WAIT_EVIDENCE":
        return conversation

    paths = conversation.data.setdefault("evidence_paths", [])
    paths.append(file_path)
    save_conversation(user_id, conversation)
    return conversation


def finish_evidence(user_id: str) -> Conversation:
    conversation = get_conversation(user_id)
    if conversation.state == "GH_WAIT_EVIDENCE":
        conversation.state = "GH_TRANSACTION_ID"
        conversation.data.setdefault("evidence", {})
        save_conversation(user_id, conversation)
    return conversation

def save_case_evidence(user_id: str, evidence: dict) -> None:
    conversation = get_conversation(user_id)
    case_id = conversation.data.get("case_id")

    if not case_id:
        raise ValueError("No active Golden Hour case for this user")

    with session() as connection:
        connection.execute(
            """
            UPDATE cases
            SET evidence_json = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE case_id = ? AND user_id = ?
            """,
            (json.dumps(evidence, ensure_ascii=False), case_id, user_id),
        )


def save_acknowledgement(user_id: str, acknowledgement_number: str) -> None:
    conversation = get_conversation(user_id)
    case_id = conversation.data.get("case_id")

    if case_id:
        with session() as connection:
            connection.execute(
                """
                UPDATE cases
                SET acknowledgement_number = ?,
                    status = 'reported',
                    updated_at = CURRENT_TIMESTAMP
                WHERE case_id = ?
                """,
                (acknowledgement_number, case_id),
            )

    conversation.state = "IDLE"
    conversation.data = {}
    save_conversation(user_id, conversation)