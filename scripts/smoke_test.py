#!/usr/bin/env python3
"""
Full-Stack Live Smoke Test Script
Pings live Docker services, verifies health endpoints, and validates API contracts.

Usage:
  python3 scripts/smoke_test.py [FRONTEND_URL] [AIBACKEND_URL]
Defaults:
  FRONTEND_URL = http://localhost:13000
  AIBACKEND_URL = http://localhost:18001
"""

import json
import sys
import urllib.request

FRONTEND_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:13000"
AIBACKEND_URL = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:18001"


def http_get(url: str, timeout: float = 4.0):
    req = urllib.request.Request(url, headers={"User-Agent": "SmokeTest/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode())


def http_post(url: str, payload: dict, timeout: float = 10.0):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "SmokeTest/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode())


def main():
    print("=" * 60)
    print("🚀 Running Full-Stack Live Smoke Tests")
    print(f"   Frontend / API: {FRONTEND_URL}")
    print(f"   AI Assistant:   {AIBACKEND_URL}")
    print("=" * 60)

    checks = []

    # 1. Frontend Proxy & Core Backend Health
    try:
        status, data = http_get(f"{FRONTEND_URL}/api/health")
        ok = status == 200 and data.get("status") == "healthy"
        checks.append(("Backend /health via Frontend Proxy", ok, f"db: {data.get('database')}"))
    except Exception as e:
        checks.append(("Backend /health via Frontend Proxy", False, str(e)))

    # 2. Currencies Listing
    try:
        status, data = http_get(f"{FRONTEND_URL}/api/currencies")
        ok = status == 200 and isinstance(data, list) and len(data) >= 6
        codes = [c.get("code") for c in data] if isinstance(data, list) else []
        checks.append(("GET /api/currencies", ok, f"Currencies: {', '.join(codes)}"))
    except Exception as e:
        checks.append(("GET /api/currencies", False, str(e)))

    # 3. Categories Listing
    try:
        status, data = http_get(f"{FRONTEND_URL}/api/categories")
        ok = status == 200 and isinstance(data, list) and len(data) >= 12
        checks.append(
            (
                "GET /api/categories",
                ok,
                f"Categories count: {len(data) if isinstance(data, list) else 0}",
            )
        )
    except Exception as e:
        checks.append(("GET /api/categories", False, str(e)))

    # 4. Summary & View Query
    try:
        status, data = http_get(f"{FRONTEND_URL}/api/expenses/summary?year=2026")
        ok = status == 200 and "total" in data and "count" in data
        checks.append(
            (
                "GET /api/expenses/summary",
                ok,
                f"total: {data.get('total')}, count: {data.get('count')}",
            )
        )
    except Exception as e:
        checks.append(("GET /api/expenses/summary", False, str(e)))

    # 5. AI Assistant Backend Health
    try:
        status, data = http_get(f"{AIBACKEND_URL}/health")
        ok = status == 200 and data.get("status") in ["healthy", "degraded"]
        checks.append(("AI Backend /health", ok, f"status: {data.get('status')}"))
    except Exception as e:
        checks.append(("AI Backend /health", False, str(e)))

    # 6. Live Currency Rate Refresh via API
    try:
        status, data = http_post(f"{FRONTEND_URL}/api/currencies/refresh", {})
        ok = status == 200 and isinstance(data, list)
        checks.append(
            (
                "POST /api/currencies/refresh",
                ok,
                f"Refreshed {len(data) if isinstance(data, list) else 0} rates",
            )
        )
    except Exception as e:
        checks.append(("POST /api/currencies/refresh", False, str(e)))

    # Report results
    print("\nResults:")
    all_passed = True
    for name, passed, detail in checks:
        icon = "✅" if passed else "❌"
        status_text = "PASS" if passed else "FAIL"
        print(f"  {icon} [{status_text}] {name:<36} : {detail}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("🎉 ALL SMOKE CHECKS PASSED!")
        sys.exit(0)
    else:
        print("⚠️ SOME SMOKE CHECKS FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
