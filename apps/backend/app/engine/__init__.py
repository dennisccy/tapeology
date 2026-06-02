"""The tape engine: market state, aggressor, features, classifier, snapshot, wiring.

Every module here depends ONLY on ``app.providers.base`` (the provider interface) and
``app.config`` — never on a concrete provider. This keeps the engine provider-agnostic.
"""
