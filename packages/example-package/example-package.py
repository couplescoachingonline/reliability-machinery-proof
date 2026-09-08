#!/usr/bin/env python3
import json
import sys


def build(payload: dict) -> dict:
    if set(payload) != {"left", "right"}:
        raise ValueError("input must contain exactly left and right")
    if not all(isinstance(payload[key], (int, float)) for key in payload):
        raise TypeError("left and right must be numbers")
    return {"sum": payload["left"] + payload["right"]}


if __name__ == "__main__":
    print(json.dumps(build(json.loads(sys.stdin.read())), sort_keys=True))
