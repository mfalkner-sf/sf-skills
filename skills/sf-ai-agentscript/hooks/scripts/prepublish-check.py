#!/usr/bin/env python3
"""
Agent Script prepublish checker.

Purpose:
- Parse a local .agent file.
- Verify agent_type/default_agent_user semantics.
- For Service Agents, confirm default_agent_user exists in the target org,
  is active, is NOT an Automated Process user, and has the
  'Einstein Agent User' profile.
- Print actionable guidance before running `sf agent publish authoring-bundle`.

Examples:
  python3 prepublish-check.py force-app/main/default/aiAuthoringBundles/MyAgent/MyAgent.agent --target-org DevOrg
  python3 prepublish-check.py ./MyAgent.agent --target-org AgentforceTesting --api-name MyAgent --json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple


def parse_agent_config(agent_file: Path) -> Dict[str, Tuple[str, int]]:
    lines = agent_file.read_text().splitlines()
    in_config = False
    config: Dict[str, Tuple[str, int]] = {}

    for i, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if raw.startswith("config:"):
            in_config = True
            continue

        if in_config and raw and not raw[0].isspace():
            break

        if in_config:
            if ":" not in stripped:
                continue
            key, value = stripped.split(":", 1)
            value = value.strip().strip('"').strip("'")
            config[key.strip()] = (value, i)

    return config


def sf_query(org_alias: str, soql: str) -> dict:
    cmd = [
        "sf", "data", "query",
        "--query", soql,
        "-o", org_alias,
        "--json",
    ]
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stdout or result.stderr)
    return json.loads(result.stdout)


def check_default_agent_user(org_alias: str, username: str) -> Dict[str, object]:
    escaped = username.replace("'", "\\'")
    soql = (
        "SELECT Username, IsActive, UserType, Profile.Name "
        f"FROM User WHERE Username = '{escaped}' LIMIT 1"
    )
    payload = sf_query(org_alias, soql)
    records = payload.get("result", {}).get("records", [])
    if not records:
        return {
            "ok": False,
            "reason": f"User '{username}' not found in target org.",
            "record": None,
        }

    record = records[0]
    user_type = record.get("UserType")
    is_active = record.get("IsActive")
    profile_name = ((record.get("Profile") or {}).get("Name"))

    if not is_active:
        return {
            "ok": False,
            "reason": f"User '{username}' exists but is inactive.",
            "record": record,
        }

    if user_type == "AutomatedProcess":
        return {
            "ok": False,
            "reason": f"User '{username}' is an Automated Process user, not a real Einstein Agent User.",
            "record": record,
        }

    if profile_name != "Einstein Agent User":
        return {
            "ok": False,
            "reason": (
                f"User '{username}' does not have Profile.Name = 'Einstein Agent User' "
                f"(actual: {profile_name or 'null'})."
            ),
            "record": record,
        }

    return {
        "ok": True,
        "reason": f"User '{username}' is active and has the Einstein Agent User profile.",
        "record": record,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepublish check for Agent Script bundles")
    parser.add_argument("agent_file", help="Path to .agent file")
    parser.add_argument("--target-org", required=True, help="Salesforce org alias/username")
    parser.add_argument("--api-name", help="Optional authoring bundle API name (for publish command output)")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    agent_file = Path(args.agent_file).expanduser().resolve()
    if not agent_file.exists():
        print(json.dumps({"ok": False, "error": f"Agent file not found: {agent_file}"}) if args.json else f"❌ Agent file not found: {agent_file}")
        return 1

    config = parse_agent_config(agent_file)
    developer_name = config.get("developer_name", (None, None))[0] or config.get("agent_name", (None, None))[0]
    description = config.get("agent_description", (None, None))[0] or config.get("description", (None, None))[0]
    agent_type = config.get("agent_type", (None, None))[0]
    default_agent_user = config.get("default_agent_user", (None, None))[0]
    effective_agent_type = agent_type or ("AgentforceServiceAgent" if default_agent_user else None)
    api_name = args.api_name or developer_name or agent_file.stem

    errors = []
    warnings = []
    checks = []

    if not developer_name:
        errors.append("Missing agent identifier in config (developer_name or legacy agent_name).")
    if not description:
        warnings.append("Missing agent description in config (agent_description or legacy description).")

    if not agent_type:
        if default_agent_user:
            warnings.append("Missing agent_type. Compiler defaults to Service Agent behavior when default_agent_user is present; set agent_type explicitly.")
        else:
            errors.append("Missing both agent_type and default_agent_user. Publish is likely to fail.")

    if effective_agent_type == "AgentforceEmployeeAgent":
        if default_agent_user:
            errors.append("Employee Agents must not include default_agent_user.")
        checks.append({"name": "agent_type", "ok": len(errors) == 0, "detail": "Employee Agent path"})

    elif effective_agent_type == "AgentforceServiceAgent":
        if not default_agent_user:
            errors.append("Service Agents require default_agent_user.")
        else:
            try:
                user_check = check_default_agent_user(args.target_org, default_agent_user)
                checks.append({"name": "default_agent_user", "ok": bool(user_check["ok"]), "detail": user_check["reason"]})
                if not user_check["ok"]:
                    errors.append(user_check["reason"])
            except Exception as exc:
                errors.append(f"Failed to verify default_agent_user via sf CLI: {exc}")

    publish_hint = (
        f"sf agent publish authoring-bundle --api-name {api_name} -o {args.target_org} --skip-retrieve --json"
        if api_name else None
    )

    result = {
        "ok": len(errors) == 0,
        "agentFile": str(agent_file),
        "apiName": api_name,
        "agentType": effective_agent_type,
        "defaultAgentUser": default_agent_user,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
        "recommendedPublish": publish_hint,
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if result["ok"]:
        print("✅ Prepublish check passed")
    else:
        print("❌ Prepublish check failed")

    print(f"Agent file: {agent_file}")
    print(f"API name:   {api_name}")
    print(f"Agent type: {effective_agent_type or 'unknown'}")
    if default_agent_user:
        print(f"Agent user: {default_agent_user}")

    for check in checks:
        icon = "✅" if check["ok"] else "❌"
        print(f"{icon} {check['name']}: {check['detail']}")

    for msg in warnings:
        print(f"⚠️ {msg}")
    for msg in errors:
        print(f"❌ {msg}")

    if publish_hint:
        print("\nRecommended publish command:")
        print(publish_hint)
        print("\nNote: If plain publish fails after successful validate/preview, retry with --skip-retrieve to bypass CLI retrieve-phase failures.")

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
