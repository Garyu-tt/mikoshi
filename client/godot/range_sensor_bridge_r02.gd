extends Node
# Optional transport for the existing R86 physics-ray sensor.
# Does not generate rays, fabricate observations, or actuate motors.
# Invoke send_existing_r86_scan(scan) from an R86 physics-frame callback.
@export var api_url: String = "http://127.0.0.1:8768/api/v1/action"
@export var source_id: String = "godot.range.r86"
var _request: HTTPRequest
var _in_flight: bool = false

func _ready() -> void:
    _request = HTTPRequest.new()
    add_child(_request)
    _request.request_completed.connect(_finished)

func send_existing_r86_scan(scan: Dictionary) -> bool:
    if not bool(scan.get("valid", false)) or _in_flight:
        return false
    if not scan.has("tick") or not scan.has("observations"):
        return false
    var token: String = OS.get_environment("MIKOSHI_API_TOKEN")
    if token.is_empty():
        return false
    var observations: Array = []
    for obj in scan["observations"]:
        if not (obj is Dictionary):
            return false
        observations.append({
            "local_object_key": str(obj.get("id", "")).sha256_text(),
            "range_m": obj.get("range_m"),
            "point": obj.get("point"),
            "ray_hits": obj.get("ray_hits"),
            "confidence": obj.get("confidence"),
        })
    var envelope: Dictionary = {
        "action": "nervous.publish",
        "args": {
            "source": source_id,
            "topic": "range.scan.r86",
            "source_sequence": int(scan["tick"]),
            "at_ns": int(Time.get_unix_time_from_system() * 1000000000.0),
            "clock_domain": "unix-ns",
            "payload": {"rays": scan.get("rays", 0),
                "origin": scan.get("origin", []),
                "direction": scan.get("direction", []),
                "sample_time_basis": "post_scan_bridge_wall_clock",
                "hits": observations},
        },
    }
    var raw: String = JSON.stringify(envelope)
    if raw.to_utf8_buffer().size() > 16000:
        return false
    var headers := PackedStringArray([
        "Content-Type: application/json",
        "Authorization: Bearer " + token,
    ])
    var status: Error = _request.request(api_url, headers, HTTPClient.METHOD_POST, raw)
    if status != OK:
        return false
    _in_flight = true
    return true

func _finished(_result: int, _code: int, _headers: PackedStringArray, _body: PackedByteArray) -> void:
    _in_flight = false
