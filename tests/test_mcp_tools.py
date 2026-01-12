#!/usr/bin/env python3
"""Test MCP server tool discovery."""
import json
import os
import sys
import requests


def list_mcp_tools():
    """List available tools on the MCP server."""
    mcp_url = os.environ.get("PG_RAG_MCP_URL", "")
    token = os.environ.get("PG_RAG_TOKEN", "")

    if not mcp_url or not token:
        print("ERROR: PG_RAG_MCP_URL and PG_RAG_TOKEN must be set")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }

    print(f"Connecting to: {mcp_url}")

    # Initialize session
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "0.1.0"},
        },
    }

    try:
        resp = requests.post(mcp_url, json=init_payload, headers=headers, stream=True, timeout=30)
        print(f"Init status: {resp.status_code}")

        session_id = resp.headers.get("mcp-session-id")
        if session_id:
            headers["mcp-session-id"] = session_id
            print(f"Session ID: {session_id[:20]}...")

        # Consume init response
        for line in resp.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    print(f"Init response: {json.dumps(data, indent=2)[:500]}")
                except:
                    pass

        # List tools
        list_payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }

        print("\nListing tools...")
        resp = requests.post(mcp_url, json=list_payload, headers=headers, stream=True, timeout=30)
        print(f"List status: {resp.status_code}")

        for line in resp.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    print(f"\nTools response:\n{json.dumps(data, indent=2)}")
                except:
                    print(f"Raw line: {line}")

        return True

    except requests.RequestException as e:
        print(f"Request error: {e}")
        return False


if __name__ == "__main__":
    success = list_mcp_tools()
    sys.exit(0 if success else 1)
