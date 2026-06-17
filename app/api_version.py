# Single source of truth for the API version prefix.
#
# Every API blueprint builds its url_prefix from this, so the whole surface
# lives under /api/v1/... . When the contract changes incompatibly, bump this
# to /api/v2 (or register a second set of blueprints under a new prefix while
# keeping v1 alive for old clients).
#
# Note: /health is intentionally NOT versioned — it's an infra/liveness probe,
# not part of the API contract.
API_PREFIX = "/api/v1"
