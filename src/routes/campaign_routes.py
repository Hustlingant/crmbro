# src/routes/campaign_routes.py

from flask import Blueprint, request, jsonify
from src.models.models import db, Campaign, SMBProfile, AdCreative, CampaignSuggestedChannel, model_to_dict
from src.models.models import CampaignStatusEnum, AdCreativeTypeEnum, SuggestedChannelStatusEnum # Enums
import uuid
from datetime import datetime
import json # For posting_guidance

campaign_bp = Blueprint("campaign_services", __name__, url_prefix="/api/v1/campaigns")

# --- Helper Functions (Consider moving to a utils file if they grow) ---
def get_smb_profile_by_user_id(user_id_str): # Assuming user_id is passed from auth layer
    # This is a placeholder. In a real app, you"d get user_id from JWT token
    # and then find the associated SMBProfile.
    # For now, let"s assume we can find a profile if one exists.
    # This mock assumes a direct link or that user_id is actually profile_id for simplicity here.
    try:
        profile_uuid = uuid.UUID(user_id_str)
        return SMBProfile.query.filter_by(profile_id=profile_uuid).first() # or filter_by(user_id=...)
    except ValueError:
        # Fallback for testing if user_id_str is not a UUID, try to find first profile
        # REMOVE THIS IN PRODUCTION
        print(f"Warning: Could not parse {user_id_str} as UUID, attempting to get first profile for testing.")
        return SMBProfile.query.first()

def generate_posting_guidance(channel, creative=None):
    """Generates manual posting guidance for a given channel and creative."""
    guidance = {
        "channel_name": channel.channel_name,
        "channel_type": channel.channel_type,
        "channel_url": channel.channel_details_json.get("url", "N/A") if channel.channel_details_json else "N/A",
        "steps": [],
        "tips": [
            "Ensure your message is tailored to the platform and audience.",
            "Check the channel’s specific rules or best practices for posting.",
            "Engage with comments and messages if possible."
        ]
    }
    if creative:
        guidance["creative_to_use"] = {
            "headline": creative.headline,
            "body": creative.body_text,
            "image_url": creative.image_url,
            "landing_page_url": creative.landing_page_url
        }
    else:
        guidance["creative_to_use"] = "No specific creative linked. Use general campaign messaging."

    if channel.channel_type == "Social Media Group" or channel.channel_type == "Social Media Page":
        guidance["steps"].extend([
            f"1. Navigate to the channel: {guidance["channel_url"]}",
            "2. Create a new post.",
            "3. Copy and paste the headline and body text from the creative provided.",
            "4. Upload the image if applicable.",
            "5. Include any relevant hashtags for your business or locality.",
            "6. Post at an optimal time for engagement (e.g., evenings or weekends, depending on audience)."
        ])
    elif channel.channel_type == "Influencer":
        guidance["steps"].extend([
            f"1. Contact the influencer using details: {channel.channel_details_json.get("contact_info", "N/A") if channel.channel_details_json else "N/A"}",
            "2. Discuss your campaign goals and the creative you want them to share.",
            "3. Negotiate terms and timing for their post.",
            "4. Provide them with the creative materials (text, image/video links).",
            "5. Monitor their post for engagement."
        ])
    elif channel.channel_type == "Local Directory" or channel.channel_type == "Event Portal":
        guidance["steps"].extend([
            f"1. Visit the portal: {guidance["channel_url"]}",
            "2. Look for options like \"Submit Listing\", \"Add Event\", or \"Advertise With Us\".",
            "3. Fill out the required forms with your business/event details and the ad creative content.",
            "4. Pay any applicable fees for listing or promotion."
        ])
    else:
        guidance["steps"].append("Generic Guidance: Manually post your content to this channel according to its specific procedures.")
    
    return guidance

# --- Campaign Routes ---
@campaign_bp.route("", methods=["POST"])
def create_campaign():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    profile_id_str = data.get("profile_id")
    if not profile_id_str:
        return jsonify({"error": "profile_id is required"}), 400
    
    try:
        profile_uuid = uuid.UUID(profile_id_str)
        smb_profile = SMBProfile.query.get(profile_uuid)
    except ValueError:
        return jsonify({"error": "Invalid profile_id format"}), 400

    if not smb_profile:
        return jsonify({"error": f"SMB Profile with ID {profile_id_str} not found."}), 404

    try:
        new_campaign = Campaign(
            profile_id=smb_profile.profile_id,
            campaign_name=data.get("campaign_name"),
            goal=data.get("goal"),
            status=CampaignStatusEnum[data.get("status", "DRAFT").upper()],
            start_date=datetime.fromisoformat(data.get("start_date")) if data.get("start_date") else None,
            end_date=datetime.fromisoformat(data.get("end_date")) if data.get("end_date") else None,
            total_budget=data.get("total_budget"),
            target_audience_description=data.get("target_audience_description"),
            target_locations_geojson=data.get("target_locations_geojson")
        )
        db.session.add(new_campaign)
        db.session.commit()
        return jsonify(model_to_dict(new_campaign)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create campaign", "details": str(e)}), 500

@campaign_bp.route("", methods=["GET"])
def get_campaigns():
    profile_id_str = request.args.get("profile_id")
    if profile_id_str:
        try:
            profile_uuid = uuid.UUID(profile_id_str)
            campaigns = Campaign.query.filter_by(profile_id=profile_uuid).all()
        except ValueError:
            return jsonify({"error": "Invalid profile_id format"}), 400
    else:
        campaigns = Campaign.query.all()
    
    return jsonify([model_to_dict(c) for c in campaigns]), 200

@campaign_bp.route("/<campaign_id_str>", methods=["GET"])
def get_campaign_by_id(campaign_id_str):
    try:
        campaign_uuid = uuid.UUID(campaign_id_str)
        campaign = Campaign.query.get(campaign_uuid)
    except ValueError:
        return jsonify({"error": "Invalid campaign_id format"}), 400

    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404
    
    campaign_data = model_to_dict(campaign)
    campaign_data["ad_creatives"] = [model_to_dict(ac) for ac in campaign.ad_creatives.all()]
    campaign_data["suggested_channels"] = []
    for sc_assoc in campaign.suggested_channels_association:
        sc_data = model_to_dict(sc_assoc)
        # If posting guidance is not generated yet, and channel is accepted, generate it.
        # This is just one place to do it; could also be a separate endpoint or on status change.
        if sc_assoc.status == SuggestedChannelStatusEnum.ACCEPTED and not sc_assoc.posting_guidance:
            # Find a relevant creative for this campaign (e.g., the first one)
            first_creative = campaign.ad_creatives.first()
            sc_assoc.posting_guidance = generate_posting_guidance(sc_assoc, first_creative)
            db.session.commit() # Save the generated guidance
            sc_data["posting_guidance"] = sc_assoc.posting_guidance # Update data to return
        campaign_data["suggested_channels"].append(sc_data)

    return jsonify(campaign_data), 200

@campaign_bp.route("/<campaign_id_str>", methods=["PUT"])
def update_campaign(campaign_id_str):
    try:
        campaign_uuid = uuid.UUID(campaign_id_str)
        campaign = Campaign.query.get(campaign_uuid)
    except ValueError:
        return jsonify({"error": "Invalid campaign_id format"}), 400

    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    try:
        for key, value in data.items():
            if hasattr(campaign, key):
                if key == "status" and value:
                    setattr(campaign, key, CampaignStatusEnum[value.upper()])
                elif key in ["start_date", "end_date"] and value:
                    setattr(campaign, key, datetime.fromisoformat(value))
                else:
                    setattr(campaign, key, value)
        db.session.commit()
        return jsonify(model_to_dict(campaign)), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update campaign", "details": str(e)}), 500

@campaign_bp.route("/<campaign_id_str>", methods=["DELETE"])
def delete_campaign(campaign_id_str):
    try:
        campaign_uuid = uuid.UUID(campaign_id_str)
        campaign = Campaign.query.get(campaign_uuid)
    except ValueError:
        return jsonify({"error": "Invalid campaign_id format"}), 400

    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404

    try:
        db.session.delete(campaign)
        db.session.commit()
        return jsonify({"message": "Campaign deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete campaign", "details": str(e)}), 500

@campaign_bp.route("/<campaign_id_str>/creatives", methods=["POST"])
def add_ad_creative_to_campaign(campaign_id_str):
    try:
        campaign_uuid = uuid.UUID(campaign_id_str)
        campaign = Campaign.query.get(campaign_uuid)
    except ValueError:
        return jsonify({"error": "Invalid campaign_id format"}), 400

    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    try:
        new_creative = AdCreative(
            campaign_id=campaign.campaign_id,
            creative_name=data.get("creative_name"),
            type=AdCreativeTypeEnum[data.get("type", "TEXT_AD").upper().replace(" ", "_")],
            headline=data.get("headline"),
            body_text=data.get("body_text"),
            image_url=data.get("image_url"),
            video_url=data.get("video_url"),
            call_to_action=data.get("call_to_action"),
            landing_page_url=data.get("landing_page_url")
        )
        db.session.add(new_creative)
        db.session.commit()
        return jsonify(model_to_dict(new_creative)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to add ad creative", "details": str(e)}), 500

@campaign_bp.route("/<campaign_id_str>/creatives", methods=["GET"])
def get_ad_creatives_for_campaign(campaign_id_str):
    try:
        campaign_uuid = uuid.UUID(campaign_id_str)
        campaign = Campaign.query.get(campaign_uuid)
    except ValueError:
        return jsonify({"error": "Invalid campaign_id format"}), 400

    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404
    
    creatives = campaign.ad_creatives.all()
    return jsonify([model_to_dict(ac) for ac in creatives]), 200

@campaign_bp.route("/<campaign_id_str>/suggested-channels", methods=["POST"])
def add_suggested_channel_to_campaign(campaign_id_str):
    try:
        campaign_uuid = uuid.UUID(campaign_id_str)
        campaign = Campaign.query.get(campaign_uuid)
    except ValueError:
        return jsonify({"error": "Invalid campaign_id format"}), 400

    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404

    data = request.get_json()
    if not data or not data.get("channel_name"):
        return jsonify({"error": "Invalid JSON payload, channel_name is required"}), 400

    try:
        # In a real flow, this data would come from the AI suggestion module output
        new_suggestion = CampaignSuggestedChannel(
            campaign_id=campaign.campaign_id,
            channel_name=data.get("channel_name"),
            channel_type=data.get("channel_type"),
            channel_details_json=data.get("channel_details_json"),
            suggestion_reason=data.get("suggestion_reason"),
            priority_score=data.get("priority_score"),
            status=SuggestedChannelStatusEnum[data.get("status", "PENDING").upper()]
        )
        # Optionally generate posting guidance here if status is ACCEPTED
        if new_suggestion.status == SuggestedChannelStatusEnum.ACCEPTED:
            first_creative = campaign.ad_creatives.first()
            new_suggestion.posting_guidance = generate_posting_guidance(new_suggestion, first_creative)

        db.session.add(new_suggestion)
        db.session.commit()
        return jsonify(model_to_dict(new_suggestion)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to add suggested channel", "details": str(e)}), 500

@campaign_bp.route("/<campaign_id_str>/suggested-channels", methods=["GET"])
def get_suggested_channels_for_campaign(campaign_id_str):
    try:
        campaign_uuid = uuid.UUID(campaign_id_str)
        campaign = Campaign.query.get(campaign_uuid)
    except ValueError:
        return jsonify({"error": "Invalid campaign_id format"}), 400

    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404
    
    suggestions_data = []
    for sc_assoc in campaign.suggested_channels_association:
        sc_data = model_to_dict(sc_assoc)
        if sc_assoc.status == SuggestedChannelStatusEnum.ACCEPTED and not sc_assoc.posting_guidance:
            first_creative = campaign.ad_creatives.first()
            sc_assoc.posting_guidance = generate_posting_guidance(sc_assoc, first_creative)
            db.session.commit()
            sc_data["posting_guidance"] = sc_assoc.posting_guidance
        suggestions_data.append(sc_data)
    return jsonify(suggestions_data), 200

@campaign_bp.route("/suggested-channels/<suggestion_id_str>/update-status", methods=["PUT"])
def update_suggested_channel_status(suggestion_id_str):
    try:
        suggestion_uuid = uuid.UUID(suggestion_id_str)
        suggested_channel = CampaignSuggestedChannel.query.get(suggestion_uuid)
    except ValueError:
        return jsonify({"error": "Invalid suggestion_id format"}), 400

    if not suggested_channel:
        return jsonify({"error": "Suggested channel not found"}), 404

    data = request.get_json()
    new_status_str = data.get("status")
    if not new_status_str:
        return jsonify({"error": "New status is required"}), 400

    try:
        new_status_enum = SuggestedChannelStatusEnum[new_status_str.upper()]
        suggested_channel.status = new_status_enum
        
        # If status changed to ACCEPTED and no guidance yet, generate it
        if new_status_enum == SuggestedChannelStatusEnum.ACCEPTED and not suggested_channel.posting_guidance:
            campaign = Campaign.query.get(suggested_channel.campaign_id)
            if campaign:
                first_creative = campaign.ad_creatives.first()
                suggested_channel.posting_guidance = generate_posting_guidance(suggested_channel, first_creative)
            else:
                # This case should ideally not happen if data integrity is maintained
                return jsonify({"error": "Associated campaign not found for generating guidance"}), 500

        db.session.commit()
        return jsonify(model_to_dict(suggested_channel)), 200
    except KeyError:
        return jsonify({"error": f"Invalid status value: {new_status_str}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update suggested channel status", "details": str(e)}), 500

