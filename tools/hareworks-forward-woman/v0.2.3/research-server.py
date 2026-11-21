"""Phone-local no-cache research viewer and evidence receiver. No remote services."""
import csv
import datetime
import hashlib
import http.server
import io
import json
import os
import pathlib
import sys
import tempfile
import urllib.parse

MODEL_SHA = 'a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
SCRIPT_PATH = '/tools/hareworks-forward-woman/v0.2.3/research-report'
CSV_FIELDS = ['bone', 'group', 'sampledAlignedPhases', 'staticPoseOffsetDeg',
              'meanRawPoseDifferenceDeg', 'motionDeltaRmsDeg', 'motionDeltaMaxDeg',
              'phaseOfMaxDynamicDifference', 'normalMotionFromAnchorRmsDeg',
              'womanMotionFromAnchorRmsDeg', 'motionFromAnchorRmsRatio',
              'hipRelativePositionDifferenceRmsUnits', 'localTranslationMotionDeltaRmsUnits']


def validate_report(obj):
    assert isinstance(obj, dict)
    assert obj.get('schema') == 'hareworks-forward-style-research-v0.2.3'
    assert obj.get('sourceModelSHA256') == MODEL_SHA
    assert obj.get('sourceClipNames') == ['Walking', 'Walking_Woman']
    assert obj.get('analysisOnly') is True and obj.get('createdNewAnimation') is False
    assert obj.get('modelJoints') == 74
    assert obj.get('sourceClipsUnchanged') is True
    assert obj.get('ownerApprovedForwardUntouched') is True
    assert obj.get('ownerApprovedBackwardUntouched') is True
    assert obj.get('sampledMatchedPhases', 0) >= 150
    assert len(obj.get('perBone', [])) == 74
    assert len(set(x.get('bone') for x in obj['perBone'])) == 74
    for entry in obj['perBone']:
        assert isinstance(entry.get('bone'), str) and 1 <= len(entry['bone']) <= 128
        assert 0 <= float(entry['motionDeltaRmsDeg']) <= 360
        assert 0 <= float(entry['motionDeltaMaxDeg']) <= 360
        assert 0 <= float(entry['staticPoseOffsetDeg']) <= 360
    return obj


def write_atomic(path, data):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.tmp-v023-', delete=False) as f:
        temporary = pathlib.Path(f.name)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, path)


def store_report(raw, state):
    if len(raw) > 3_000_000:
        raise ValueError('OVERSIZED_REPORT')
    report = validate_report(json.loads(raw))
    payload = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False).encode('utf-8') + b'\n'
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(report['perBone'])
    write_atomic(pathlib.Path(state) / 'research-report.json', payload)
    write_atomic(pathlib.Path(state) / 'research-report.csv', buffer.getvalue().encode())
    digest = hashlib.sha256(payload).hexdigest()
    receipt = {
        'campaign': 'hareworks-walking-style-research-v0.2.3',
        'status': 'REAL_BROWSER_74_BONE_SOURCE_RESEARCH_SAVED',
        'sourceModelSha256': MODEL_SHA,
        'sources': ['Walking', 'Walking_Woman'],
        'sourceBones': 74,
        'pairsMeasured': report['sampledMatchedPhases'],
        'reportPath': str(pathlib.Path(state) / 'research-report.json'),
        'csvPath': str(pathlib.Path(state) / 'research-report.csv'),
        'reportSha256': digest,
        'receivedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'sourceClipsModified': False,
        'ownerAcceptedForwardAndBackwardPreserved': True,
        'newAnimationCreated': False,
    }
    write_atomic(pathlib.Path(state) / 'measurement-receipt.json',
                 (json.dumps(receipt, indent=2) + '\n').encode())
    return {'saved': True, 'sha256': digest, 'path': receipt['reportPath'],
            'csvPath': receipt['csvPath']}


def make_handler(root, state, ready):
    class Handler(http.server.SimpleHTTPRequestHandler):
        extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                          '.mjs': 'text/javascript', '.js': 'text/javascript',
                          '.glb': 'model/gltf-binary', '.json': 'application/json'}

        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=root, **kwargs)

        def end_headers(self):
            self.send_header('Cache-Control', 'no-store, no-cache, max-age=0, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('X-Content-Type-Options', 'nosniff')
            super().end_headers()

        def do_POST(self):
            path = urllib.parse.urlsplit(self.path).path
            if path != SCRIPT_PATH:
                self.send_error(404, 'Unknown research endpoint')
                return
            origin = self.headers.get('Origin', '')
            expected = 'http://127.0.0.1:' + str(self.server.server_address[1])
            if origin and origin != expected:
                self.send_error(403, 'Origin not authorized')
                return
            try:
                n = int(self.headers.get('Content-Length', '0'))
                if not 0 < n <= 3_000_000:
                    self.send_error(413, 'Bad evidence size')
                    return
                result = store_report(self.rfile.read(n), state)
                data = json.dumps(result).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except (ValueError, AssertionError, KeyError, TypeError) as ex:
                self.send_error(422, 'Invalid source research payload: ' + str(ex)[:120])

    return Handler


def main():
    root, state, ready = sys.argv[1:]
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), make_handler(root, state, ready))
    write_atomic(ready, json.dumps({'pid': os.getpid(),
                                    'port': server.server_address[1],
                                    'root': root}).encode())
    server.serve_forever()


if __name__ == '__main__':
    main()
