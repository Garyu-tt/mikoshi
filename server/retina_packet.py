"""Accept authentic phase-only R238 photon packets, no reconstructed image."""
import base64
import binascii
import hashlib
from server.retina_sparse import publish


def ingest(runtime, args):
    eye = runtime.sparse
    if eye is None:
        raise ValueError('Genuine original R239 runtime is unavailable')
    if not isinstance(args, dict) or args.get('clock_domain') != 'unix-ns':
        raise ValueError('Explicit unix-ns source clock required')
    frame_ms = args.get('frame_ms', 33)
    if type(frame_ms) is not int or not 1 <= frame_ms <= 250:
        raise ValueError('Invalid retinal phase duration')
    encoded = args.get('photon_packet_b64')
    # The header and checksum are small; byte budget is based on eye geometry.
    maximum = eye.width * eye.height * 2 * 3 + 512
    if not isinstance(encoded, str) or len(encoded) > 4 * ((maximum + 2)//3):
        raise ValueError('Photon packet missing or above size budget')
    try:
        packet = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError('Invalid photon packet base64') from error
    if len(packet) > maximum:
        raise ValueError('Photon packet above retinal geometry budget')
    with eye.lock:
        # Original R238 verifies the source body, schedule, geometry and SHA.
        epoch, phase, when, ids, _ = eye.sampler.decode(packet, eye.body)
        seq = epoch * eye.passes + phase
        if seq != eye.last_step + 1:
            raise ValueError('Missing, stale or duplicated photon phase')
        if when <= eye.circuit.sensor.last_capture_ns:
            raise ValueError('Nonmonotonic original camera timestamp')
        spikes, metadata = eye.circuit.accept(packet, frame_ms)
        if metadata.get('real_fresh_receptors') != len(ids):
            raise ValueError('Retinal source freshness mismatch')
        eye.last_step = seq
    result = {'_spikes_raw':spikes, 'metadata':metadata,
        'source_sequence':seq, 'clock_domain':'unix-ns',
        'sample_at_ns':when, 'spike_bytes':len(spikes),
        'spikes_sha256':hashlib.sha256(spikes).hexdigest(),
        'stream_truncated':False,
        'photon_transport':'r238-verified-sparse-phase'}
    return publish(runtime, result)
