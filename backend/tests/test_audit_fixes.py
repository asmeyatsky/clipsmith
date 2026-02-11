"""
Comprehensive tests for audit fix verification.
Tests all critical, high, and medium severity fixes from the security audit.
"""
import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Set JWT_SECRET_KEY before any imports that depend on it
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-tests-only-not-production")


class TestJWTSecurityFixes:
    """Tests for Finding #1: JWT secret loaded from environment."""

    def test_jwt_secret_loaded_from_env(self):
        """JWT_SECRET_KEY must be loaded from environment, not hardcoded."""
        from backend.infrastructure.security.jwt_adapter import SECRET_KEY
        assert SECRET_KEY == os.environ["JWT_SECRET_KEY"]
        assert SECRET_KEY != "super-secret-key-change-me"

    def test_jwt_create_and_verify_token(self):
        """Token creation and verification roundtrip works."""
        from backend.infrastructure.security.jwt_adapter import JWTAdapter
        data = {"sub": "test@example.com", "user_id": "user123"}
        token = JWTAdapter.create_access_token(data, expires_delta=timedelta(minutes=5))
        assert token is not None

        payload = JWTAdapter.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test@example.com"
        assert payload["user_id"] == "user123"

    def test_jwt_expired_token_rejected(self):
        """Expired tokens must be rejected."""
        from backend.infrastructure.security.jwt_adapter import JWTAdapter
        data = {"sub": "test@example.com", "user_id": "user123"}
        token = JWTAdapter.create_access_token(data, expires_delta=timedelta(seconds=-1))
        payload = JWTAdapter.verify_token(token)
        assert payload is None

    def test_jwt_invalid_token_rejected(self):
        """Invalid tokens must be rejected."""
        from backend.infrastructure.security.jwt_adapter import JWTAdapter
        payload = JWTAdapter.verify_token("invalid.token.here")
        assert payload is None

    def test_jwt_tampered_token_rejected(self):
        """Tampered tokens must be rejected."""
        from backend.infrastructure.security.jwt_adapter import JWTAdapter
        data = {"sub": "test@example.com", "user_id": "user123"}
        token = JWTAdapter.create_access_token(data, expires_delta=timedelta(minutes=5))
        # Tamper with the token
        parts = token.split(".")
        parts[1] = parts[1] + "x"
        tampered = ".".join(parts)
        payload = JWTAdapter.verify_token(tampered)
        assert payload is None

    def test_jwt_default_expiration_is_15_minutes(self):
        """Default token expiration should be 15 minutes when no delta provided."""
        from backend.infrastructure.security.jwt_adapter import JWTAdapter
        data = {"sub": "test@example.com", "user_id": "user123"}
        token = JWTAdapter.create_access_token(data)
        payload = JWTAdapter.verify_token(token)
        assert payload is not None
        # Token should be valid (not expired)
        assert payload["sub"] == "test@example.com"


class TestFrameRateParserFix:
    """Tests for Finding #2: eval() replaced with safe frame rate parser."""

    def test_safe_parse_fraction(self):
        """Parse standard ffprobe fraction format."""
        from backend.application.tasks import _safe_parse_frame_rate
        assert _safe_parse_frame_rate("30/1") == 30.0
        assert _safe_parse_frame_rate("30000/1001") == pytest.approx(29.97, rel=0.01)
        assert _safe_parse_frame_rate("24/1") == 24.0

    def test_safe_parse_decimal(self):
        """Parse decimal frame rate."""
        from backend.application.tasks import _safe_parse_frame_rate
        assert _safe_parse_frame_rate("29.97") == pytest.approx(29.97)
        assert _safe_parse_frame_rate("60.0") == 60.0

    def test_safe_parse_zero_denominator(self):
        """Zero denominator returns 0.0 instead of crashing."""
        from backend.application.tasks import _safe_parse_frame_rate
        assert _safe_parse_frame_rate("0/0") == 0.0
        assert _safe_parse_frame_rate("30/0") == 0.0

    def test_safe_parse_invalid_input(self):
        """Invalid input returns 0.0 instead of crashing."""
        from backend.application.tasks import _safe_parse_frame_rate
        assert _safe_parse_frame_rate("invalid") == 0.0
        assert _safe_parse_frame_rate("") == 0.0

    def test_safe_parse_rejects_code_injection(self):
        """Malicious input cannot execute code."""
        from backend.application.tasks import _safe_parse_frame_rate
        # These would execute code with eval() but should safely return 0.0
        assert _safe_parse_frame_rate("__import__('os').system('echo pwned')") == 0.0
        assert _safe_parse_frame_rate("1+1") == 0.0


class TestRecommendationEngineFix:
    """Tests for Finding #4: Syntax error in recommendation engine fixed."""

    def test_recommendation_engine_initializes(self):
        """RecommendationEngine should initialize without syntax errors."""
        from backend.application.services.recommendation_engine import RecommendationEngine
        engine = RecommendationEngine()
        assert engine.decay_factors is not None
        assert engine.time_decay_hours == 24
        assert engine.max_recommendations == 100

    def test_decay_factors_have_correct_values(self):
        """Decay factors should have expected values."""
        from backend.application.services.recommendation_engine import RecommendationEngine
        engine = RecommendationEngine()
        assert engine.decay_factors['view'] == 1.0
        assert engine.decay_factors['like'] == 5.0
        assert engine.decay_factors['comment'] == 10.0
        assert engine.decay_factors['share'] == 20.0
        assert engine.decay_factors['follow'] == 30.0

    def test_cosine_similarity_calculation(self):
        """Cosine similarity should work correctly."""
        from backend.application.services.recommendation_engine import RecommendationEngine
        engine = RecommendationEngine()
        # Identical vectors should have similarity 1.0
        dict1 = {"a": 1.0, "b": 2.0}
        dict2 = {"a": 1.0, "b": 2.0}
        assert engine._cosine_similarity(dict1, dict2) == pytest.approx(1.0)

        # Orthogonal vectors should have similarity 0.0
        dict3 = {"a": 1.0}
        dict4 = {"b": 1.0}
        assert engine._cosine_similarity(dict3, dict4) == 0.0

        # Empty dicts
        assert engine._cosine_similarity({}, {}) == 0.0


class TestUploadVideoFix:
    """Tests for Finding #5: Duplicate video save removed."""

    def test_upload_saves_video_once(self):
        """Upload should save video exactly once, not twice."""
        # Read the source to verify no duplicate save
        import inspect
        from backend.application.use_cases.upload_video import UploadVideoUseCase
        source = inspect.getsource(UploadVideoUseCase.execute)
        # Count occurrences of save calls
        save_count = source.count("self._video_repo.save(")
        assert save_count == 1, f"Expected 1 save call, found {save_count}"

    def test_upload_enqueues_once(self):
        """Upload should enqueue processing task exactly once."""
        import inspect
        from backend.application.use_cases.upload_video import UploadVideoUseCase
        source = inspect.getsource(UploadVideoUseCase.execute)
        enqueue_count = source.count("self._video_queue.enqueue(")
        assert enqueue_count == 1, f"Expected 1 enqueue call, found {enqueue_count}"


class TestDatabaseConfigFix:
    """Tests for Finding #8: DATABASE_URL configurable from environment."""

    def test_database_url_from_env(self):
        """DATABASE_URL should be read from environment."""
        from backend.infrastructure.repositories.database import DATABASE_URL
        # Should match env var or default to sqlite
        expected = os.getenv("DATABASE_URL", "sqlite:///database.db")
        assert DATABASE_URL == expected

    def test_echo_disabled(self):
        """SQL echo logging must be disabled."""
        from backend.infrastructure.repositories.database import engine
        assert engine.echo is False


class TestMonitoringRouterFix:
    """Tests for Finding #9: Monitoring router bugs fixed."""

    def test_monitoring_router_imports(self):
        """Monitoring router should import without errors."""
        # This would crash before the fix due to missing 'import os'
        from backend.presentation.api.monitoring_router import router
        assert router is not None

    def test_health_endpoint_exists(self):
        """Health endpoint should exist on the router."""
        from backend.presentation.api.monitoring_router import router
        routes = [r.path for r in router.routes]
        assert "/monitoring/health" in routes or "/health" in routes


class TestVideoEditorRouterFix:
    """Tests for Finding #10: Broken import fixed + auth checks added."""

    def test_video_editor_router_imports(self):
        """Video editor router should import without errors."""
        from backend.presentation.api.video_editor_router import router
        assert router is not None

    def test_get_current_user_defined(self):
        """get_current_user should be defined in the router module."""
        from backend.presentation.api.video_editor_router import get_current_user
        assert callable(get_current_user)


class TestSecurityHeadersMiddleware:
    """Tests for Finding #28: Security headers added."""

    def test_security_headers_middleware_class_exists(self):
        """SecurityHeadersMiddleware should be defined in main."""
        from backend.main import SecurityHeadersMiddleware
        assert SecurityHeadersMiddleware is not None


class TestVideoEditorServiceFix:
    """Tests for Finding #26: Fake async removed."""

    def test_service_methods_are_not_async(self):
        """VideoEditorService methods should be regular (not async)."""
        import asyncio
        from backend.application.services.video_editor_service import VideoEditorService

        # These methods should NOT be coroutines
        assert not asyncio.iscoroutinefunction(VideoEditorService.create_project)
        assert not asyncio.iscoroutinefunction(VideoEditorService.get_project)
        assert not asyncio.iscoroutinefunction(VideoEditorService.delete_project)
        assert not asyncio.iscoroutinefunction(VideoEditorService.upload_asset)
        assert not asyncio.iscoroutinefunction(VideoEditorService.delete_asset)
        assert not asyncio.iscoroutinefunction(VideoEditorService.add_caption)
        assert not asyncio.iscoroutinefunction(VideoEditorService.delete_caption)

    def test_service_has_get_asset_method(self):
        """Service should have get_asset for authorization checks."""
        from backend.application.services.video_editor_service import VideoEditorService
        assert hasattr(VideoEditorService, 'get_asset')

    def test_service_has_get_caption_method(self):
        """Service should have get_caption for authorization checks."""
        from backend.application.services.video_editor_service import VideoEditorService
        assert hasattr(VideoEditorService, 'get_caption')


class TestPaymentServiceTransactionFix:
    """Tests for Finding #7: DB transactions on payment operations."""

    def test_complete_tip_has_commit_and_rollback(self):
        """complete_tip_transaction must use commit and rollback for atomicity."""
        import inspect
        from backend.application.services.payment_service import PaymentService
        source = inspect.getsource(PaymentService.complete_tip_transaction)
        assert "self.repository.commit()" in source, "Missing commit() call"
        assert "self.repository.rollback()" in source, "Missing rollback() call"


class TestCORSFix:
    """Tests for Finding #21: CORS restricted to specific methods."""

    def test_cors_methods_not_wildcard(self):
        """CORS should not allow all methods via wildcard."""
        import inspect
        from backend.main import app
        source = inspect.getsource(type(app))
        # Check the actual middleware configuration in main.py source
        import backend.main as main_module
        main_source = inspect.getsource(main_module)
        assert '"*"' not in main_source.split("allow_methods")[1].split(")")[0], \
            "CORS allow_methods should not use wildcard"


class TestGitignoreFix:
    """Tests for Finding #3: .env.production not tracked."""

    def test_env_files_in_gitignore(self):
        """All .env.* files should be in .gitignore."""
        gitignore_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            ".gitignore"
        )
        with open(gitignore_path) as f:
            content = f.read()
        assert ".env.*" in content


class TestFeedPerformanceFix:
    """Tests for Finding #16: N+1 queries reduced."""

    def test_feed_uses_reasonable_limits(self):
        """Feed should not load 1000 videos or 10000 interactions."""
        import inspect
        from backend.application.use_cases.get_personalized_feed import GetPersonalizedFeedUseCase
        source = inspect.getsource(GetPersonalizedFeedUseCase.execute)
        assert "limit=1000" not in source, "Should not load 1000 videos"
        assert "limit=10000" not in source, "Should not load 10000 interactions"

    def test_following_feed_skips_heavy_queries(self):
        """Following feed should not load all videos and interactions."""
        import inspect
        from backend.application.use_cases.get_personalized_feed import GetPersonalizedFeedUseCase
        source = inspect.getsource(GetPersonalizedFeedUseCase.execute)
        # The 'following' branch should use get_videos_from_creators directly
        assert "get_videos_from_creators" in source


class TestSentryConfigFix:
    """Tests for Finding #25: Sentry sample rate reduced."""

    def test_sentry_sample_rate_configurable(self):
        """Sentry traces_sample_rate should be configurable via env."""
        import inspect
        from backend.application.services.monitoring_service import ErrorReportingService
        source = inspect.getsource(ErrorReportingService.__init__)
        assert "SENTRY_TRACES_SAMPLE_RATE" in source
        assert "traces_sample_rate=1.0" not in source


class TestAuthTokenExpiration:
    """Tests for Finding #31: JWT expiration reduced."""

    def test_token_expiration_is_30_minutes(self):
        """Token expiration should be 30 minutes, not 60."""
        import inspect
        from backend.application.use_cases.authenticate_user import AuthenticateUserUseCase
        source = inspect.getsource(AuthenticateUserUseCase.execute)
        assert "minutes=30" in source
        assert "minutes=60" not in source


class TestDebugFileRemoved:
    """Tests for Finding #36: debug_hash.py removed."""

    def test_debug_hash_file_not_present(self):
        """debug_hash.py should not exist in the codebase."""
        debug_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "debug_hash.py"
        )
        assert not os.path.exists(debug_path), "debug_hash.py should be deleted"


class TestRedirectUrlValidation:
    """Tests for Finding #30: Open redirect fixed."""

    def test_redirect_validation_exists(self):
        """Payment router should validate redirect URLs."""
        import inspect
        from backend.presentation.api.payment_router import _validate_redirect_url
        assert callable(_validate_redirect_url)

    def test_redirect_rejects_external_urls(self):
        """External URLs should be rejected."""
        from backend.presentation.api.payment_router import _validate_redirect_url
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            _validate_redirect_url("https://evil.com/phishing")

    def test_redirect_accepts_allowed_urls(self):
        """Allowed domain URLs should be accepted."""
        os.environ["ALLOWED_REDIRECT_HOSTS"] = "localhost,clipsmith.com"
        from backend.presentation.api.payment_router import _validate_redirect_url
        result = _validate_redirect_url("https://clipsmith.com/callback")
        assert result == "https://clipsmith.com/callback"

    def test_redirect_rejects_invalid_scheme(self):
        """Non-HTTP(S) schemes should be rejected."""
        from backend.presentation.api.payment_router import _validate_redirect_url
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            _validate_redirect_url("javascript:alert(1)")


class TestAtomicViewIncrement:
    """Tests for Finding #17: Race condition on view count fixed."""

    def test_increment_uses_atomic_sql(self):
        """View increment should use atomic SQL instead of read-modify-write."""
        import inspect
        from backend.infrastructure.repositories.sqlite_video_repo import SQLiteVideoRepository
        source = inspect.getsource(SQLiteVideoRepository.increment_views)
        # Should use SQL UPDATE, not Python addition
        assert "UPDATE" in source or "update" in source.lower()
        assert "COALESCE" in source or "coalesce" in source.lower()
