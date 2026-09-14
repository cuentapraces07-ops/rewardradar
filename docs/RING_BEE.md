# Ring and Bee variants: honest readiness boundary

The Amazon hackathon accepts multiple submissions only when each submission is
unique and substantially different. The repository therefore keeps separate
runtime boundaries instead of presenting a single fake “all devices” demo.

## Ring

`agent/ring_adapter.py` is a credential-free adapter boundary. It accepts a
Ring access token and HTTPS API base URL only at runtime, never writes either,
and reports `device_or_simulator_evidence: false` until a real Ring simulator or
device run is captured. A Ring developer account and the official API terms are
required before enabling it.

## Bee

`agent/bee_adapter.py` accepts an owner-supplied JSON export and fails closed if
the path is absent or malformed. The track rules require data recorded and
processed by a real Bee device or Apple Watch; a fixture is not substituted for
that evidence. Until such a device export exists, Bee is explicitly not marked
submission-ready.

These boundaries let the Alexa+ project remain fully reproducible while making
the remaining hardware/account gates visible. The tests verify that neither
adapter silently claims runtime evidence it does not possess.
