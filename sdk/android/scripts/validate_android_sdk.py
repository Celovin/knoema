from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "settings.gradle.kts": ["include(\":luvoire-mobile\")"],
    "build.gradle.kts": ["com.android.library", "kotlin(\"android\")"],
    "luvoire-mobile/build.gradle.kts": ["namespace = \"com.celovin.luvoire\"", "compileSdk"],
    "luvoire-mobile/src/main/kotlin/com/celovin/luvoire/LuvoireClient.kt": [
        "class LuvoireClient",
        "fun restUrl",
        "fun webSocketUrl",
        "fun offlineResponse",
    ],
    "luvoire-mobile/src/main/kotlin/com/celovin/luvoire/NPCAgent.kt": [
        "class NPCAgent",
        "cachedOrOfflineResponse",
    ],
}


def validate() -> dict[str, object]:
    missing: dict[str, list[str]] = {}
    for relative_path, tokens in REQUIRED.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        absent = [token for token in tokens if token not in text]
        if absent:
            missing[relative_path] = absent
    return {"ok": not missing, "missing": missing, "checked": sorted(REQUIRED)}


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "build"
    if command not in {"build", "test", "validate"}:
        raise SystemExit(f"unsupported wrapper command: {command}")
    result = validate()
    print(json.dumps(result, indent=2))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
