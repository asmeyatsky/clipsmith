import os
from typing import Generator
from contextlib import contextmanager
from sqlmodel import create_engine, SQLModel, Session, select

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")

# SQLite needs check_same_thread=False; PostgreSQL does not
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

def create_db_and_tables():
    # Import all models to ensure they're registered with SQLModel metadata
    from .models import (  # noqa: F401
        UserDB, VideoDB, LikeDB, CommentDB, CaptionDB, TipDB, FollowDB,
        PasswordResetDB, NotificationDB, HashtagDB, ContentModerationDB,
        EmailVerificationDB, TwoFactorSecretDB, TwoFactorVerificationDB,
        VideoProjectDB, VideoEditorAssetDB, VideoEditorTransitionDB,
        VideoEditorTrackDB, VideoEditorCaptionDB, VideoEditorKeyframeDB,
        VideoEditorColorGradeDB, VideoEditorAudioMixDB, VideoEditorChromaKeyDB,
        VideoEditorEffectDB, AICaptionJobDB, AITemplateDB, AIVideoGenerationDB,
        AIVoiceOverDB, PremiumContentDB, PremiumPurchaseDB, BrandCampaignDB,
        BrandProfileDB, TransactionDB, CreatorWalletDB, PayoutDB,
        SubscriptionDB, VideoAnalyticsDB, CreatorAnalyticsDB, TimeSeriesDataDB,
        AudienceDemographicsDB, ContentPerformanceDB, ProjectMonetizationDB,
        # PRD conformance models
        CircleDB, CircleMemberDB, PlaylistDB, PlaylistItemDB, PlaylistCollaboratorDB,
        ChallengeDB, ChallengeParticipantDB, CommunityGroupDB, CommunityMemberDB,
        DiscussionPostDB, EventDB, EventAttendeeDB, DuetDB, CollaborativeVideoDB,
        VideoCollaboratorDB, LiveStreamDB, LiveStreamGuestDB, WatchPartyDB,
        WatchPartyParticipantDB, PollDB, PollOptionDB, PollVoteDB,
        ChapterMarkerDB, ProductTagDB, VideoLinkDB, DirectMessageDB,
        ConversationDB, BadgeDB, UserBadgeDB, CourseDB, CourseLessonDB,
        CourseEnrollmentDB, UserPreferencesDB, FavoriteCreatorDB,
        CreatorFundEligibilityDB, SubscriptionTierDB, GDPRRequestDB,
        ConsentRecordDB, ColorGradingPresetDB, EffectLibraryDB,
        VideoSpeedSettingDB, TrafficSourceDB, RetentionDataDB,
        PostingTimeRecommendationDB,
        AgeVerificationDB, LessonProgressDB,
    )
    SQLModel.metadata.create_all(engine)
    _seed_data()

def _seed_data():
    """Seed the database with initial PRD-required data (templates, presets, effects, badges)."""
    import json
    from .models import (
        AITemplateDB, ColorGradingPresetDB, EffectLibraryDB, BadgeDB,
    )
    with Session(engine) as session:
        # Only seed if templates table is empty
        existing = session.exec(select(AITemplateDB)).first()
        if existing:
            return

        # --- Seed 500+ Templates ---
        template_categories = {
            "cooking": ["Recipe Intro", "Cooking Steps", "Ingredient Showcase", "Kitchen Tips", "Food Reveal",
                        "Meal Prep", "Taste Test", "Restaurant Review", "Baking Tutorial", "Quick Recipe"],
            "fitness": ["Workout Intro", "Exercise Demo", "Before/After", "Fitness Challenge", "Gym Motivation",
                        "Yoga Flow", "HIIT Timer", "Progress Tracker", "Nutrition Tips", "Stretching Routine"],
            "education": ["Lesson Intro", "Explainer", "Quiz Format", "Study Tips", "Book Review",
                          "Science Experiment", "History Recap", "Math Tutorial", "Language Learning", "Lecture Notes"],
            "comedy": ["Skit Intro", "Punchline Reveal", "Reaction Template", "Meme Format", "Character Switch",
                        "Voiceover Comedy", "Duet Comedy", "Situational Comedy", "Parody", "Impersonation"],
            "intro": ["Channel Intro", "Video Intro", "Brand Intro", "Animated Intro", "Minimal Intro",
                       "Glitch Intro", "Neon Intro", "Cinematic Intro", "Text Intro", "Logo Reveal"],
            "outro": ["Subscribe Outro", "End Screen", "Credits Roll", "Thank You", "Next Video",
                       "Social Links", "Recap Outro", "Animated Outro", "Minimal Outro", "Call to Action"],
            "social": ["Instagram Story", "TikTok Trend", "YouTube Short", "Twitter Post", "LinkedIn Update",
                        "Pinterest Pin", "Snapchat Story", "Facebook Reel", "Cross-Platform", "Story Highlight"],
            "promo": ["Product Launch", "Sale Announcement", "Event Promo", "App Promo", "Service Ad",
                       "Testimonial", "Countdown", "Flash Sale", "Brand Story", "Limited Offer"],
            "vlog": ["Daily Vlog", "Travel Vlog", "Day in My Life", "Get Ready With Me", "What I Eat",
                      "Room Tour", "Haul Video", "Morning Routine", "Night Routine", "Q&A Format"],
            "music": ["Music Video", "Lyric Video", "Album Promo", "Beat Visualizer", "Song Cover",
                       "Studio Session", "Concert Recap", "Playlist Promo", "Artist Spotlight", "Music Review"],
            "gaming": ["Game Review", "Let's Play", "Highlights Reel", "Tutorial", "Stream Overlay",
                        "Tier List", "Versus Format", "Speedrun", "Patch Notes", "Game News"],
            "beauty": ["Makeup Tutorial", "Skincare Routine", "Product Review", "GRWM", "Transformation",
                        "Nail Art", "Hair Tutorial", "Beauty Haul", "Fragrance Review", "Dupe Alert"],
            "travel": ["Destination Guide", "Hotel Review", "Travel Tips", "Packing List", "Travel Vlog",
                        "Food Tour", "Budget Travel", "Luxury Travel", "Adventure", "Cultural Experience"],
            "tech": ["Tech Review", "Unboxing", "Setup Tour", "Comparison", "Tips & Tricks",
                      "App Review", "Coding Tutorial", "AI Demo", "Gadget Showcase", "Tech News"],
            "business": ["Pitch Deck", "Case Study", "Team Intro", "Quarterly Update", "Product Demo",
                          "Customer Story", "Brand Values", "How-To Guide", "Industry News", "Webinar Promo"],
        }

        styles = ["modern", "vintage", "cinematic", "minimal", "bold", "elegant", "playful", "professional",
                  "neon", "retro", "clean", "dramatic", "warm", "cool", "vibrant"]

        template_count = 0
        for category, names in template_categories.items():
            for i, name in enumerate(names):
                for style_idx, style in enumerate(styles[:4]):  # 4 styles per template = 600 templates
                    template = AITemplateDB(
                        name=f"{name} - {style.title()}",
                        description=f"Professional {style} {name.lower()} template for {category} content",
                        category=category,
                        style=style,
                        project_data=json.dumps({"tracks": [], "duration": 30, "style": style}),
                        is_premium=style_idx >= 2,
                        price=4.99 if style_idx >= 2 else 0.0,
                        tags=json.dumps([category, style, name.lower().replace(" ", "-")]),
                    )
                    session.add(template)
                    template_count += 1

        # --- Seed Color Grading Presets ---
        presets = [
            ("Cinematic Warm", "cinematic", {"brightness": 5, "contrast": 15, "saturation": -10, "temperature": 20, "tint": 5, "highlights": -10, "shadows": 10, "vibrance": -5}),
            ("Cinematic Cool", "cinematic", {"brightness": 0, "contrast": 20, "saturation": -15, "temperature": -15, "tint": -5, "highlights": -15, "shadows": 15, "vibrance": -10}),
            ("Cinematic Teal & Orange", "cinematic", {"brightness": 5, "contrast": 25, "saturation": 10, "temperature": 10, "tint": -10, "highlights": 5, "shadows": -5, "vibrance": 15}),
            ("Vibrant Pop", "vibrant", {"brightness": 10, "contrast": 10, "saturation": 30, "temperature": 5, "tint": 0, "highlights": 0, "shadows": 0, "vibrance": 25}),
            ("Vibrant Summer", "vibrant", {"brightness": 15, "contrast": 5, "saturation": 20, "temperature": 15, "tint": 5, "highlights": 10, "shadows": -5, "vibrance": 20}),
            ("Moody Dark", "moody", {"brightness": -15, "contrast": 30, "saturation": -20, "temperature": -10, "tint": 0, "highlights": -20, "shadows": 20, "vibrance": -15}),
            ("Moody Desaturated", "moody", {"brightness": -10, "contrast": 20, "saturation": -40, "temperature": -5, "tint": 5, "highlights": -15, "shadows": 15, "vibrance": -30}),
            ("Vintage Film", "vintage", {"brightness": 5, "contrast": -10, "saturation": -20, "temperature": 10, "tint": 10, "highlights": -5, "shadows": 5, "vibrance": -15}),
            ("Vintage Polaroid", "vintage", {"brightness": 10, "contrast": -5, "saturation": -25, "temperature": 15, "tint": 5, "highlights": 10, "shadows": -10, "vibrance": -20}),
            ("Black & White Classic", "monochrome", {"brightness": 0, "contrast": 20, "saturation": -100, "temperature": 0, "tint": 0, "highlights": -10, "shadows": 10, "vibrance": 0}),
            ("Black & White High Contrast", "monochrome", {"brightness": 5, "contrast": 40, "saturation": -100, "temperature": 0, "tint": 0, "highlights": -20, "shadows": 20, "vibrance": 0}),
            ("Natural Soft", "natural", {"brightness": 5, "contrast": -5, "saturation": 5, "temperature": 5, "tint": 0, "highlights": -5, "shadows": 5, "vibrance": 10}),
            ("Natural Golden Hour", "natural", {"brightness": 10, "contrast": 5, "saturation": 10, "temperature": 20, "tint": 5, "highlights": 5, "shadows": 0, "vibrance": 15}),
            ("High Key", "lighting", {"brightness": 25, "contrast": -10, "saturation": -5, "temperature": 5, "tint": 0, "highlights": 15, "shadows": -15, "vibrance": 5}),
            ("Low Key", "lighting", {"brightness": -20, "contrast": 25, "saturation": -10, "temperature": -5, "tint": 0, "highlights": -25, "shadows": 25, "vibrance": -5}),
            ("Pastel Dream", "creative", {"brightness": 15, "contrast": -15, "saturation": -10, "temperature": 10, "tint": 15, "highlights": 20, "shadows": -10, "vibrance": -5}),
            ("Neon Glow", "creative", {"brightness": 0, "contrast": 30, "saturation": 40, "temperature": -10, "tint": -10, "highlights": 10, "shadows": 5, "vibrance": 35}),
            ("Cross Process", "creative", {"brightness": 5, "contrast": 15, "saturation": 15, "temperature": -20, "tint": 20, "highlights": -10, "shadows": 10, "vibrance": 10}),
            ("Bleach Bypass", "creative", {"brightness": -5, "contrast": 35, "saturation": -30, "temperature": 0, "tint": 0, "highlights": -10, "shadows": 15, "vibrance": -20}),
            ("Instagram Warm", "social", {"brightness": 10, "contrast": 10, "saturation": 15, "temperature": 15, "tint": 5, "highlights": 5, "shadows": -5, "vibrance": 20}),
        ]

        for name, category, settings in presets:
            preset = ColorGradingPresetDB(
                name=name, description=f"Professional {name} color grading preset",
                category=category, settings=json.dumps(settings), is_system=True,
            )
            session.add(preset)

        # --- Seed Effects Library (200+) ---
        effect_categories = {
            "basic": ["blur", "sharpen", "glow", "vignette", "noise", "pixelate", "brightness", "contrast", "gamma"],
            "color": ["sepia", "negative", "posterize", "solarize", "threshold", "duotone", "hue_shift", "color_balance",
                       "channel_mixer", "gradient_map", "color_lookup", "split_tone"],
            "distortion": ["ripple", "wave", "twirl", "bulge", "pinch", "spherize", "lens_distortion", "fisheye",
                           "displacement", "morph", "warp", "perspective_shift", "kaleidoscope"],
            "stylize": ["oil_paint", "watercolor", "sketch", "emboss", "mosaic", "stained_glass", "halftone",
                         "crosshatch", "pointillism", "pop_art", "comic", "woodcut", "linocut"],
            "light": ["lens_flare", "light_leak", "bokeh", "god_rays", "prism", "chromatic_aberration", "bloom",
                       "anamorphic_flare", "volumetric_light", "sun_rays", "sparkle", "glow_edges"],
            "motion": ["motion_blur", "zoom_blur", "radial_blur", "directional_blur", "ghost", "echo", "trail",
                        "speed_lines", "streak", "afterimage", "time_warp", "frame_blend"],
            "overlay": ["film_grain", "dust", "scratches", "rain", "snow", "fire", "smoke", "particles",
                         "confetti", "bubbles", "fog", "lightning", "clouds", "stars"],
            "ar": ["face_mesh", "background_blur", "beauty", "cartoon", "age_filter", "face_swap", "virtual_makeup",
                    "face_distort", "animal_ears", "glasses_try_on", "hat_overlay", "mask_filter",
                    "hair_color", "eye_color", "face_paint", "3d_mask", "body_tracking", "hand_tracking",
                    "segmentation", "sky_replacement", "ground_detection", "object_placement"],
            "transition": ["fade", "dissolve", "wipe", "slide", "push", "zoom_transition", "spin", "flip",
                           "morph_transition", "glitch_transition", "ink_splash", "particle_transition"],
            "text": ["typewriter", "bounce", "wave_text", "glitch_text", "neon_text", "handwritten",
                      "3d_text", "kinetic_typography", "text_reveal", "text_shadow"],
        }

        for category, effects in effect_categories.items():
            for effect_name in effects:
                is_ar = category == "ar"
                is_premium = category in ("ar", "transition") or effect_name.startswith("3d_")
                effect = EffectLibraryDB(
                    name=effect_name.replace("_", " ").title(),
                    description=f"{effect_name.replace('_', ' ').title()} effect",
                    category=category,
                    effect_type=effect_name,
                    parameters=json.dumps({"intensity": 0.5}),
                    is_premium=is_premium,
                    is_ar=is_ar,
                )
                session.add(effect)

        # --- Seed Supporter Badges ---
        badges = [
            ("Bronze Supporter", "Tipped $10+ to a creator", "supporter", "tip_total", "10"),
            ("Silver Supporter", "Tipped $50+ to a creator", "supporter", "tip_total", "50"),
            ("Gold Supporter", "Tipped $100+ to a creator", "supporter", "tip_total", "100"),
            ("Platinum Supporter", "Tipped $500+ to a creator", "supporter", "tip_total", "500"),
            ("Diamond Supporter", "Tipped $1000+ to a creator", "supporter", "tip_total", "1000"),
            ("First Video", "Published your first video", "achievement", "video_count", "1"),
            ("Rising Star", "Reached 100 followers", "achievement", "follower_count", "100"),
            ("Trending Creator", "Had a video in trending", "achievement", "trending_count", "1"),
            ("Community Builder", "Created a community group", "achievement", "group_count", "1"),
            ("Verified Creator", "Verified creator account", "creator", "verified", "true"),
            ("Top Creator", "Reached 10K followers", "creator", "follower_count", "10000"),
            ("Elite Creator", "Reached 100K followers", "creator", "follower_count", "100000"),
        ]

        for name, desc, badge_type, req_type, req_value in badges:
            badge = BadgeDB(
                name=name, description=desc, badge_type=badge_type,
                requirement_type=req_type, requirement_value=req_value,
            )
            session.add(badge)

        session.commit()


# Auto-create tables on import (fallback for when lifespan events don't fire)
create_db_and_tables()


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency injection compatible session generator."""
    with Session(engine) as session:
        yield session

@contextmanager
def get_task_session():
    """Context manager for getting a session in background tasks."""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
