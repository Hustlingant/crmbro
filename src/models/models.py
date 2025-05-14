# Database Models for Hyperlocal SMB Platform

import enum
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.schema import FetchedValue
from sqlalchemy.ext.hybrid import hybrid_property
import uuid # For default UUID generation if not handled by DB

# It's conventional to initialize db in the main app file or an extensions file
# and then import it here. For now, we'll define it and assume it's configured
# in main.py. If main.py uses `db = SQLAlchemy(app)`, this file would typically
# just import that `db` instance.
# For the template structure, models are usually defined and then db is imported from main or an extensions file.
# Let's assume db will be initialized in main.py and we can define models that will use it.

db = SQLAlchemy() # This will be replaced by the app's db instance in practice

class SMBUser(db.Model):
    __tablename__ = "smb_users"

    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    verification_token = db.Column(db.String(100), nullable=True)
    password_reset_token = db.Column(db.String(100), nullable=True)
    password_reset_expires = db.Column(db.TIMESTAMP(timezone=True), nullable=True)
    last_login_at = db.Column(db.TIMESTAMP(timezone=True), nullable=True)
    created_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    # Relationship to SMBProfile
    smb_profile = db.relationship("SMBProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SMBUser {self.email}>"

class SMBProfile(db.Model):
    __tablename__ = "smb_profiles"

    profile_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("smb_users.user_id"), nullable=False)
    business_name = db.Column(db.String(255), nullable=False)
    business_category = db.Column(db.String(100), nullable=False)
    business_subcategory = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    address_line1 = db.Column(db.String(255), nullable=True)
    address_line2 = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    pin_code = db.Column(db.String(10), nullable=False)
    country = db.Column(db.String(50), nullable=False, default="India")
    # For PostGIS: from geoalchemy2 import Geometry
    # location_coordinates = db.Column(Geometry(geometry_type=\"POINT\", srid=4326), nullable=True)
    # For now, using JSONB for coordinates as PostGIS setup is more involved for prototype
    location_coordinates_json = db.Column(JSONB, nullable=True) # Store as {"type": "Point", "coordinates": [lon, lat]}
    website_url = db.Column(db.String(255), nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)
    operating_hours = db.Column(JSONB, nullable=True)
    created_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    # Relationship back to SMBUser
    user = db.relationship("SMBUser", back_populates="smb_profile")
    # Relationship to Campaigns
    campaigns = db.relationship("Campaign", back_populates="smb_profile", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SMBProfile {self.business_name}>"

class CampaignStatusEnum(enum.Enum):
    DRAFT = "Draft"
    ACTIVE = "Active"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"
    SCHEDULED = "Scheduled"

class Campaign(db.Model):
    __tablename__ = "campaigns"

    campaign_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = db.Column(UUID(as_uuid=True), db.ForeignKey("smb_profiles.profile_id"), nullable=False)
    campaign_name = db.Column(db.String(255), nullable=False)
    goal = db.Column(db.String(100), nullable=True)
    status = db.Column(db.Enum(CampaignStatusEnum), nullable=False, default=CampaignStatusEnum.DRAFT)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    total_budget = db.Column(db.Numeric(10, 2), nullable=True)
    target_audience_description = db.Column(db.Text, nullable=True)
    target_locations_geojson = db.Column(JSONB, nullable=True)
    created_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    smb_profile = db.relationship("SMBProfile", back_populates="campaigns")
    ad_creatives = db.relationship("AdCreative", back_populates="campaign", lazy="dynamic", cascade="all, delete-orphan")
    suggested_channels_association = db.relationship("CampaignSuggestedChannel", back_populates="campaign", cascade="all, delete-orphan")
    performance_metrics = db.relationship("CampaignPerformance", back_populates="campaign", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Campaign {self.campaign_name}>"

class AdCreativeTypeEnum(enum.Enum):
    TEXT_AD = "Text Ad"
    IMAGE_AD = "Image Ad"
    VIDEO_SNIPPET = "Video Snippet"

class AdCreative(db.Model):
    __tablename__ = "ad_creatives"

    creative_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = db.Column(UUID(as_uuid=True), db.ForeignKey("campaigns.campaign_id"), nullable=False)
    creative_name = db.Column(db.String(255), nullable=True)
    type = db.Column(db.Enum(AdCreativeTypeEnum), nullable=False)
    headline = db.Column(db.String(255), nullable=True)
    body_text = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    video_url = db.Column(db.String(255), nullable=True)
    call_to_action = db.Column(db.String(100), nullable=True)
    landing_page_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    campaign = db.relationship("Campaign", back_populates="ad_creatives")

    def __repr__(self):
        return f"<AdCreative {self.creative_name}>"

# This is an association object for the many-to-many relationship between Campaign and a potential CuratedChannel table
# For now, suggested_channels from the schema is more like a direct log of suggestions for a campaign.
# If we had a master `curated_channels` table, this would be more relevant.
# Let's adapt `suggested_channels` from the schema directly first.

class SuggestedChannelStatusEnum(enum.Enum):
    PENDING = "Pending"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    USED = "Used"

class CampaignSuggestedChannel(db.Model):
    __tablename__ = "campaign_suggested_channels"
    # This table stores the suggestions made by the AI for a specific campaign.
    # It is not a master list of all possible channels.

    suggestion_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = db.Column(UUID(as_uuid=True), db.ForeignKey("campaigns.campaign_id"), nullable=False)
    channel_name = db.Column(db.String(255), nullable=False) # Name of the suggested channel, e.g., "XYZ Facebook Group"
    channel_type = db.Column(db.String(100), nullable=True) # E.g., "Social Media Group", "Influencer"
    channel_details_json = db.Column(JSONB, nullable=True) # Store URL, contact, estimated reach, cost from AI module
    suggestion_reason = db.Column(db.Text, nullable=True)
    priority_score = db.Column(db.Float, nullable=True)
    status = db.Column(db.Enum(SuggestedChannelStatusEnum), default=SuggestedChannelStatusEnum.PENDING)
    posting_guidance = db.Column(JSONB, nullable=True) # ADDED: To store manual posting guidance
    created_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, server_default=db.func.now())

    campaign = db.relationship("Campaign", back_populates="suggested_channels_association")

    def __repr__(self):
        return f"<CampaignSuggestedChannel {self.channel_name} for campaign {self.campaign_id}>"

class CampaignPerformance(db.Model):
    __tablename__ = "campaign_performance"

    metric_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = db.Column(UUID(as_uuid=True), db.ForeignKey("campaigns.campaign_id"), nullable=False)
    # If metrics are per channel used in a campaign:
    # suggested_channel_id = db.Column(UUID(as_uuid=True), db.ForeignKey("campaign_suggested_channels.suggestion_id"), nullable=True)
    metric_date = db.Column(db.Date, nullable=False)
    impressions = db.Column(db.Integer, nullable=True)
    clicks = db.Column(db.Integer, nullable=True)
    conversions = db.Column(db.Integer, nullable=True)
    cost_spent = db.Column(db.Numeric(10, 2), nullable=True)
    custom_metrics_json = db.Column(JSONB, nullable=True)
    created_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, server_default=db.func.now())

    campaign = db.relationship("Campaign", back_populates="performance_metrics")
    # suggested_channel = db.relationship("CampaignSuggestedChannel") # If linking to specific suggested channel

    def __repr__(self):
        return f"<CampaignPerformance metric {self.metric_id} for campaign {self.campaign_id}>"

# Example of a curated master channel table (if we build this out)
# class CuratedLocalChannel(db.Model):
#     __tablename__ = "curated_local_channels"
#     channel_master_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     name = db.Column(db.String(255), nullable=False, unique=True)
#     platform = db.Column(db.String(100), nullable=True)
#     category = db.Column(db.String(100), nullable=True)
#     primary_location_city = db.Column(db.String(100), nullable=True)
#     # primary_location_pin_codes = db.Column(ARRAY(db.String), nullable=True)
#     # ... other fields from ai_local_channel_db.py
#     created_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, server_default=db.func.now())
#     updated_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())


# Helper function to convert model instance to dictionary
def model_to_dict(instance, exclude=None):
    if exclude is None:
        exclude = []
    data = {}
    for column in instance.__table__.columns:
        if column.name in exclude:
            continue
        value = getattr(instance, column.name)
        if isinstance(value, enum.Enum):
            data[column.name] = value.value
        elif isinstance(value, uuid.UUID):
            data[column.name] = str(value)
        elif isinstance(value, (db.Numeric)):
             data[column.name] = float(value) if value is not None else None
        elif isinstance(value, (db.Date, db.TIMESTAMP)):
            data[column.name] = value.isoformat() if value is not None else None
        else:
            data[column.name] = value
    return data

