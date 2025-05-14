# src/routes/ai_services_routes.py

from flask import Blueprint, request, jsonify
from src.ai_modules.hyperlocal_targeting import HyperlocalTargetingModuleV2
from src.ai_modules.local_channel_db import LocalChannelDatabase
from src.ai_modules.channel_suggestion import ChannelSuggestionModule
import json

ai_bp = Blueprint("ai_services", __name__, url_prefix="/api/v1/ai")

# Initialize AI modules (could be done at app level if preferred for performance)
# For simplicity, we instantiate them per request or globally here if stateless enough.
# The LocalChannelDatabase is read-only for now, so one instance is fine.
channel_db_instance = LocalChannelDatabase()

# Mock SMB profiles as the AI modules expect them. In a real app, this would come from a database.
MOCK_SMB_PROFILES_FOR_ROUTES = {
    "smb_profile_uuid_1": {
        "profile_id": "smb_profile_uuid_1",
        "business_name": "Aroma Cafe",
        "business_category": "Restaurant",
        "business_subcategory": "Cafe",
        "city": "Mumbai",
        "pin_code": "400050",
        "target_customer_profile": {"interests": ["coffee", "fast food", "hangout"], "age_groups": ["18-25", "25-35"], "income_level": ["Medium", "High"]}
    },
    "smb_profile_uuid_2": {
        "profile_id": "smb_profile_uuid_2",
        "business_name": "Tech Gadgets Store",
        "business_category": "Retail",
        "business_subcategory": "Electronics",
        "city": "Bangalore",
        "pin_code": "560001",
        "target_customer_profile": {"interests": ["technology", "gadgets", "gaming"], "age_groups": ["22-40", "40-55"], "income_level": ["High", "Very High"]}
    }
}

@ai_bp.route("/audience-insights", methods=["POST"])
def get_audience_insights_route():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    profile_id = data.get("profile_id")
    target_area_geojson_str = data.get("target_area_geojson_str") # This should be a string representation of GeoJSON
    business_category = data.get("business_category")
    target_radius_km = data.get("target_radius_km", 5) # Default radius if not provided

    if not all([profile_id, target_area_geojson_str]):
        return jsonify({"error": "Missing required fields: profile_id, target_area_geojson_str"}), 400

    # The AI module uses its own MOCK_SMB_PROFILES, so profile_id is used there.
    targeting_module = HyperlocalTargetingModuleV2(smb_profiles_db=MOCK_SMB_PROFILES_FOR_ROUTES)
    
    insights = targeting_module.get_audience_insights(
        profile_id=profile_id,
        target_area_geojson_str=target_area_geojson_str, # Pass it as a string
        business_category=business_category,
        target_radius_km=float(target_radius_km) # Ensure it's a float
    )

    if insights.get("errors"):
        return jsonify({"error": "Failed to generate audience insights", "details": insights["errors"]}), 500
    
    return jsonify(insights), 200

@ai_bp.route("/channel-recommendations", methods=["POST"])
def get_channel_recommendations_route():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    profile_id = data.get("profile_id")
    # For channel recommendations, we need audience insights. 
    # We'll expect target_area_geojson_str and business_category to generate them internally.
    target_area_geojson_str = data.get("target_area_geojson_str")
    business_category = data.get("business_category") # Needed for audience insights
    target_radius_km = data.get("target_radius_km", 5)

    # Campaign details from request
    campaign_budget = data.get("budget")
    campaign_goal = data.get("goal")
    # campaign_id = data.get("campaign_id") # Optional, not used directly by AI modules yet
    # target_audience_description = data.get("target_audience_description") # Not directly used by V2 modules

    if not all([profile_id, target_area_geojson_str]):
        return jsonify({"error": "Missing required fields for recommendation: profile_id, target_area_geojson_str"}), 400

    smb_profile = MOCK_SMB_PROFILES_FOR_ROUTES.get(profile_id)
    if not smb_profile:
        return jsonify({"error": f"SMB Profile with ID {profile_id} not found in mock data."}), 404

    # Construct campaign_details for the suggestion module
    campaign_details = {
        "total_budget": campaign_budget if campaign_budget is not None else 0,
        "goal": campaign_goal
    }

    # 1. Get Audience Insights first
    targeting_module = HyperlocalTargetingModuleV2(smb_profiles_db=MOCK_SMB_PROFILES_FOR_ROUTES)
    audience_insights = targeting_module.get_audience_insights(
        profile_id=profile_id,
        target_area_geojson_str=target_area_geojson_str,
        business_category=business_category if business_category else smb_profile.get("business_category"),
        target_radius_km=float(target_radius_km)
    )

    if audience_insights.get("errors") and not audience_insights.get("target_zones_details"): # Allow proceeding if some insights generated despite minor errors
        return jsonify({"error": "Failed to generate necessary audience insights for recommendations", "details": audience_insights.get("errors")}), 500

    # 2. Get Channel Suggestions
    suggestion_module = ChannelSuggestionModule(channel_db_instance=channel_db_instance)
    
    recommendations = suggestion_module.suggest_channels(
        smb_profile=smb_profile, # Pass the fetched/mocked smb_profile dict
        campaign_details=campaign_details,
        audience_insights=audience_insights,
        top_n=data.get("top_n", 5)
    )

    return jsonify(recommendations), 200

