from __future__ import annotations

import requests
from flask import Blueprint, request

from snipsel_api.auth_session import current_user, json_response, require_auth
from snipsel_api.errors import api_error
from snipsel_api.extensions import db
from snipsel_api.models import Collection, CollectionSnipsel, Snipsel

importer_bp = Blueprint("importer", __name__)


TWO_S_BASE_URL = "https://twosapp.com"


@importer_bp.route("/api/importer/twos/login", methods=["POST"])
@require_auth
def twos_login():
    """Authenticate with TwoS and return user info and token."""
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        raise api_error(400, "invalid_input", "username and password are required")

    try:
        response = requests.post(
            f"{TWO_S_BASE_URL}/apiV2/user/login/new",
            json={"user": {"username": username, "password": password}},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()

        if "user" not in result:
            raise api_error(401, "auth_failed", "Login failed")

        user_data = result["user"]
        return json_response(
            {
                "user": {
                    "id": user_data.get("_id"),
                    "username": user_data.get("username"),
                    "token": user_data.get("token"),
                }
            }
        )
    except requests.RequestException as e:
        raise api_error(502, "external_error", f"Failed to connect to TwoS: {str(e)}")


@importer_bp.route("/api/importer/twos/lists", methods=["GET"])
@require_auth
def twos_lists():
    """Get all lists from TwoS."""
    token = request.headers.get("X-TwoS-Token")
    if not token:
        raise api_error(401, "auth_required", "TwoS token required")

    try:
        response = requests.get(
            f"{TWO_S_BASE_URL}/api/lists",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()

        lists = result.get("lists", [])
        return json_response(
            {
                "lists": [
                    {
                        "id": lst.get("_id"),
                        "name": lst.get("name"),
                        "isDaily": lst.get("isDaily", False),
                        "thingsCount": len(lst.get("things", [])),
                    }
                    for lst in lists
                ]
            }
        )
    except requests.RequestException as e:
        raise api_error(502, "external_error", f"Failed to fetch lists: {str(e)}")


@importer_bp.route("/api/importer/twos/import", methods=["POST"])
@require_auth
def twos_import():
    """Import selected lists from TwoS."""
    user = current_user()
    data = request.get_json() or {}

    list_ids = data.get("listIds", [])
    overwrite = data.get("overwrite", False)
    token = data.get("token")

    if not list_ids:
        raise api_error(400, "invalid_input", "listIds required")
    if not token:
        raise api_error(401, "auth_required", "TwoS token required")

    # First, fetch all lists to get their details
    try:
        response = requests.get(
            f"{TWO_S_BASE_URL}/api/lists",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as e:
        raise api_error(502, "external_error", f"Failed to fetch lists: {str(e)}")

    all_lists = result.get("lists", [])
    lists_to_import = [lst for lst in all_lists if lst.get("_id") in list_ids]

    imported = 0
    skipped = 0
    errors = []

    for lst in lists_to_import:
        try:
            list_name = lst.get("name", "Untitled")
            is_daily = lst.get("isDaily", False)

            # Check if collection already exists
            existing = (
                db.session.execute(
                    db.select(Collection).where(
                        Collection.owner_user_id == user.id,
                        Collection.title == list_name,
                        Collection.deleted_at.is_(None),
                    )
                )
                .scalars()
                .first()
            )

            if existing:
                if overwrite:
                    # Delete existing collection and recreate
                    existing.deleted_at = db.func.now()
                    db.session.commit()
                else:
                    skipped += 1
                    continue

            # Create collection
            collection = Collection(
                owner_user_id=user.id,
                title=list_name,
                icon="📝",
                list_for_day=None,  # Will be set for daily lists
                created_by_id=user.id,
                modified_by_id=user.id,
            )

            # Handle daily lists
            if is_daily:
                # For daily lists, we need to figure out the date
                # TwoS daily lists might have the date in the name or a separate field
                # For now, create as regular collection with daily indicator in name
                collection.title = f"[Daily] {list_name}"

            db.session.add(collection)
            db.session.flush()

            # Import things as snipsels
            things = lst.get("things", [])
            for idx, thing in enumerate(things):
                content = thing.get("body", "")
                thing_type = "text"

                # Determine type based on thing properties
                if thing.get("isComplete"):
                    thing_type = "task"
                elif thing.get("url"):
                    thing_type = "link"

                snipsel = Snipsel(
                    owner_user_id=user.id,
                    type=thing_type,
                    content_markdown=content,
                    task_done=thing.get("isComplete", False),
                    created_by_id=user.id,
                    modified_by_id=user.id,
                )
                db.session.add(snipsel)
                db.session.flush()

                # Link to collection
                cs = CollectionSnipsel(
                    collection_id=collection.id,
                    snipsel_id=snipsel.id,
                    position=idx + 1,
                    indent=0,
                )
                db.session.add(cs)

            db.session.commit()
            imported += 1

        except Exception as e:
            db.session.rollback()
            errors.append(f"Failed to import list '{lst.get('name')}': {str(e)}")

    return json_response(
        {
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
        }
    )
