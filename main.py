import os
import re
import time
import json
import glob
import logging
from flask import Flask, Response, jsonify, request
from collections import defaultdict

# ------------------------------------------------
# global
# ------------------------------------------------

app = Flask(__name__)

# offsets
last_processed_offsets = {}

# global counter
total_disconnects = 0
disconnect_errors = 0
total_connects = 0
connection_timeouts = 0
total_reservations = 0

# init metrics
last_metrics = {
    "fps": 0.0,
    "players": 0,
    "ai": 0,
    "avg_rtt": 0.0,
    "avg_pktloss": 0.0,
    "veh_count": 0,
    "veh_extra_count": 0,
    "proj_shells": 0,
    "proj_missiles": 0,
    "proj_grenades": 0,
    "proj_total": 0,
    "streaming_dynam": 0,
    "streaming_static": 0,
    "streaming_disabled": 0,
    "streaming_new": 0,
    "streaming_del": 0,
    "streaming_bump": 0
}

# ------------------------------------------------
# regex definition
# ------------------------------------------------
fps_regex = re.compile(r"FPS:\s([0-9.]+)")
player_regex = re.compile(r"Player:\s([0-9]+)")
ai_regex = re.compile(r"AI:\s([0-9]+)")
rtt_pkt_regex = re.compile(r"PktLoss:\s([0-9]+)/100,\sRtt:\s([0-9]+)")
veh_regex = re.compile(r"Veh:\s([0-9]+)\s\(([0-9]+)\)")
proj_regex = re.compile(r"Proj\s\(S:\s([0-9]+),\sM:\s([0-9]+),\sG:\s([0-9]+)\s\|\s([0-9]+)\)")
streaming_regex = re.compile(
    r"Streaming\(Dynam:\s([0-9]+),\sStatic:\s([0-9]+),\sDisabled:\s([0-9]+)\s\|\sNew:\s([0-9]+),\sDel:\s([0-9]+),\sBump:\s([0-9]+)\)"
)

disconnect_regex = re.compile(r"disconnected.*reason=([0-9]+)")
timeout_regex = re.compile(r"connection timeout.*identity=0x[0-9A-F]+")
connect_regex = re.compile(r"Player connected:")
reserve_slot_regex = re.compile(r"Reserving slot for player")

# ------------------------------------------------
# helpers
# ------------------------------------------------
def load_offsets_from_disk(filename="offsets.json"):
    """ Beim Start werden ggf. gespeicherte Offsets aus einer Datei geladen,
        um sie über Container-Neustarts zu behalten. """
    global last_processed_offsets
    if not os.path.exists(filename):
        return
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            last_processed_offsets = {k: int(v) for k, v in data.items()}
    except Exception as e:
        logging.warning(f"Could not load offsets from disk: {e}")

def persist_offsets_to_disk(filename="offsets.json"):
    """ Speichert die aktuellen Offsets in eine JSON-Datei. """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(last_processed_offsets, f)
    except Exception as e:
        logging.warning(f"Could not persist offsets: {e}")


def get_last_offset_for_file(log_file: str) -> int:
    """ Liefert den zuletzt bekannten Offset für eine Datei zurück. """
    return last_processed_offsets.get(log_file, 0)


def save_offset_for_file(log_file: str, offset: int):
    """ Merkt sich den Offset in der globalen Map und schreibt ihn auf Disk. """
    last_processed_offsets[log_file] = offset


def get_last_log_folders(logs_dir: str, limit: int):
    """ Sucht bis zu 'limit' Verzeichnisse im logs_dir, die mit 'logs_' beginnen. """
    if not os.path.isdir(logs_dir):
        return []
    all_dirs = []
    for entry in os.listdir(logs_dir):
        full_path = os.path.join(logs_dir, entry)
        if os.path.isdir(full_path) and entry.startswith("logs_"):
            all_dirs.append(entry)
    # sort data
    all_dirs.sort()
    # return last value
    return all_dirs[-limit:]


def get_last_log_data():
    """ Liest aus den letzten 5 'logs_'-Ordnern die console.log ein und aktualisiert last_metrics. """
    global total_disconnects, disconnect_errors, total_connects
    global connection_timeouts, total_reservations

    rtt_values = []
    pkt_loss_values = []

    logs_dir = "logs"
    folders = get_last_log_folders(logs_dir, 5)

    local_metrics = dict(last_metrics)

    for folder in folders:
        log_file = os.path.join(logs_dir, folder, "console.log")
        if not os.path.isfile(log_file):
            continue

        offset = get_last_offset_for_file(log_file)

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                f.seek(offset)
                for line in f:
                    line = line.strip()

                    # FPS
                    match = fps_regex.search(line)
                    if match:
                        local_metrics["fps"] = float(match.group(1))

                    # Players
                    match = player_regex.search(line)
                    if match:
                        local_metrics["players"] = int(match.group(1))

                    # AI
                    match = ai_regex.search(line)
                    if match:
                        local_metrics["ai"] = int(match.group(1))

                    # RTT + PacketLoss
                    match = rtt_pkt_regex.search(line)
                    if match:
                        pkt_loss = float(match.group(1))
                        rtt = float(match.group(2))
                        pkt_loss_values.append(pkt_loss)
                        rtt_values.append(rtt)

                    # Disconnect
                    match = disconnect_regex.search(line)
                    if match:
                        total_disconnects += 1
                        reason = int(match.group(1))
                        if reason == 6:
                            disconnect_errors += 1

                    # connection timeout
                    if timeout_regex.search(line):
                        connection_timeouts += 1

                    # connect
                    if connect_regex.search(line):
                        total_connects += 1

                    # reserve
                    if reserve_slot_regex.search(line):
                        total_reservations += 1

                    # vehicles
                    match = veh_regex.search(line)
                    if match:
                        local_metrics["veh_count"] = int(match.group(1))
                        local_metrics["veh_extra_count"] = int(match.group(2))

                    # projectile-data
                    match = proj_regex.search(line)
                    if match:
                        local_metrics["proj_shells"] = int(match.group(1))
                        local_metrics["proj_missiles"] = int(match.group(2))
                        local_metrics["proj_grenades"] = int(match.group(3))
                        local_metrics["proj_total"] = int(match.group(4))

                    # streaming
                    match = streaming_regex.search(line)
                    if match:
                        local_metrics["streaming_dynam"] = int(match.group(1))
                        local_metrics["streaming_static"] = int(match.group(2))
                        local_metrics["streaming_disabled"] = int(match.group(3))
                        local_metrics["streaming_new"] = int(match.group(4))
                        local_metrics["streaming_del"] = int(match.group(5))
                        local_metrics["streaming_bump"] = int(match.group(6))

                # find new position and save
                current_offset = f.tell()
                save_offset_for_file(log_file, current_offset)

        except Exception as e:
            logging.warning(f"Fehler beim Lesen der Datei {log_file}: {e}")

    # RTT and packets
    if rtt_values:
        local_metrics["avg_rtt"] = sum(rtt_values) / len(rtt_values)
    if pkt_loss_values:
        local_metrics["avg_pktloss"] = sum(pkt_loss_values) / len(pkt_loss_values)

    # renew data
    for k, v in local_metrics.items():
        last_metrics[k] = v

    # persistent on disk
    persist_offsets_to_disk()

    return dict(last_metrics)

# ------------------------------------------------
# Flask /metrics Endpoint
# ------------------------------------------------

@app.route("/metrics", methods=["GET"])
def metrics_handler():
    """ Bietet die gesammelten Werte als Prometheus-kompatiblen Text an. """
    data = get_last_log_data()  # refresh data

    lines = []
    # formats for prometheus

    # FPS
    lines.append("# HELP server_fps Die FPS des Servers")
    lines.append("# TYPE server_fps gauge")
    lines.append(f"server_fps {data['fps']}")

    lines.append("# HELP server_players Anzahl der Spieler")
    lines.append("# TYPE server_players gauge")
    lines.append(f"server_players {data['players']}")

    lines.append("# HELP server_ai Anzahl der AI")
    lines.append("# TYPE server_ai gauge")
    lines.append(f"server_ai {data['ai']}")

    lines.append("# HELP server_avg_rtt Durchschnittliche RTT in Millisekunden")
    lines.append("# TYPE server_avg_rtt gauge")
    lines.append(f"server_avg_rtt {data['avg_rtt']}")

    lines.append("# HELP server_avg_pktloss Durchschnittlicher Paketverlust (in % pro 100)")
    lines.append("# TYPE server_avg_pktloss gauge")
    lines.append(f"server_avg_pktloss {data['avg_pktloss']}")

    lines.append("# HELP server_veh_count Anzahl der Fahrzeuge")
    lines.append("# TYPE server_veh_count gauge")
    lines.append(f"server_veh_count {data['veh_count']}")

    lines.append("# HELP server_veh_extra_count Anzahl der zusätzlichen Fahrzeuge")
    lines.append("# TYPE server_veh_extra_count gauge")
    lines.append(f"server_veh_extra_count {data['veh_extra_count']}")

    # Proj
    lines.append("# HELP server_proj_shells Anzahl der aktiven Granaten")
    lines.append("# TYPE server_proj_shells gauge")
    lines.append(f"server_proj_shells {data['proj_shells']}")

    lines.append("# HELP server_proj_missiles Anzahl der aktiven Raketen")
    lines.append("# TYPE server_proj_missiles gauge")
    lines.append(f"server_proj_missiles {data['proj_missiles']}")

    lines.append("# HELP server_proj_grenades Anzahl der aktiven Granaten")
    lines.append("# TYPE server_proj_grenades gauge")
    lines.append(f"server_proj_grenades {data['proj_grenades']}")

    lines.append("# HELP server_proj_total Gesamtanzahl der Projektile")
    lines.append("# TYPE server_proj_total gauge")
    lines.append(f"server_proj_total {data['proj_total']}")

    # streaming
    lines.append("# HELP server_streaming_dynam Anzahl der dynamischen Streaming-Objekte")
    lines.append("# TYPE server_streaming_dynam gauge")
    lines.append(f"server_streaming_dynam {data['streaming_dynam']}")

    lines.append("# HELP server_streaming_static Anzahl der statischen Streaming-Objekte")
    lines.append("# TYPE server_streaming_static gauge")
    lines.append(f"server_streaming_static {data['streaming_static']}")

    lines.append("# HELP server_streaming_disabled Anzahl der deaktivierten Streaming-Objekte")
    lines.append("# TYPE server_streaming_disabled gauge")
    lines.append(f"server_streaming_disabled {data['streaming_disabled']}")

    lines.append("# HELP server_streaming_new Anzahl der neuen Streaming-Objekte")
    lines.append("# TYPE server_streaming_new gauge")
    lines.append(f"server_streaming_new {data['streaming_new']}")

    lines.append("# HELP server_streaming_del Anzahl der gelöschten Streaming-Objekte")
    lines.append("# TYPE server_streaming_del gauge")
    lines.append(f"server_streaming_del {data['streaming_del']}")

    lines.append("# HELP server_streaming_bump Anzahl der Streaming-Bumps")
    lines.append("# TYPE server_streaming_bump gauge")
    lines.append(f"server_streaming_bump {data['streaming_bump']}")

    # connects
    lines.append("# HELP server_disconnects Anzahl der Disconnect-Ereignisse")
    lines.append("# TYPE server_disconnects counter")
    lines.append(f"server_disconnects {total_disconnects}")

    lines.append("# HELP server_disconnect_errors Anzahl der fehlerhaften Disconnects (reason=6)")
    lines.append("# TYPE server_disconnect_errors counter")
    lines.append(f"server_disconnect_errors {disconnect_errors}")

    lines.append("# HELP server_connection_timeouts Anzahl der 'connection timeout'-Fehler")
    lines.append("# TYPE server_connection_timeouts counter")
    lines.append(f"server_connection_timeouts {connection_timeouts}")

    lines.append("# HELP server_connects Anzahl der Connect-Ereignisse")
    lines.append("# TYPE server_connects counter")
    lines.append(f"server_connects {total_connects}")

    lines.append("# HELP server_reservations Anzahl der Reservierungsslots")
    lines.append("# TYPE server_reservations counter")
    lines.append(f"server_reservations {total_reservations}")

    output = "\n".join(lines) + "\n"
    return Response(output, mimetype="text/plain")


@app.route("/")
def index():
    return "Arma Reforger Metrics Python - check /metrics"

# ------------------------------------------------
# start main
# ------------------------------------------------
if __name__ == "__main__":
    # Optional: load offsets (persistent container restarts)
    load_offsets_from_disk()
    # start flask
    logging.info("Starte Arma Reforger Metrics (Python) auf Port 8880")
    app.run(host="0.0.0.0", port=8880)
