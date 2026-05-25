"""WebSocket gateway. Clients connect to /ws?token=<JWT>.

The gateway subscribes the connection to Redis channels for:
 - user:<uid>             (private notifications)
 - group:<gid>            (each group the user is in)

Server-side events from the rest of the app call notifications.service.push_ws / push_user,
which publish to Redis; this gateway forwards them down the socket as JSON.
"""
from __future__ import annotations

import json
import logging
import threading

from flask import request
from flask_jwt_extended import decode_token

from .service import user_groups

log = logging.getLogger(__name__)


def register_ws(sock):
    from ...extensions import get_redis

    @sock.route("/ws")
    def ws(ws):
        token = request.args.get("token", "")
        try:
            ident = decode_token(token).get("sub")
            uid = int(ident)
        except Exception:
            ws.close()
            return

        gids = user_groups(uid)
        channels = [f"user:{uid}"] + [f"group:{g}" for g in gids]

        r = get_redis()
        pubsub = r.pubsub()
        pubsub.subscribe(*channels)

        stop_flag = {"done": False}

        def reader():
            try:
                for msg in pubsub.listen():
                    if stop_flag["done"]:
                        break
                    if msg["type"] != "message":
                        continue
                    try:
                        ws.send(msg["data"] if isinstance(msg["data"], str)
                                else msg["data"].decode())
                    except Exception:
                        break
            finally:
                try:
                    pubsub.close()
                except Exception:
                    pass

        t = threading.Thread(target=reader, daemon=True)
        t.start()

        try:
            ws.send(json.dumps({"event": "hello", "data": {"user_id": uid, "channels": channels}}))
            while True:
                # echo / heartbeat
                msg = ws.receive()
                if msg is None:
                    break
                if msg == "ping":
                    ws.send("pong")
        finally:
            stop_flag["done"] = True
            try:
                pubsub.unsubscribe()
            except Exception:
                pass
