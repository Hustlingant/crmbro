# AI Module: Local Advertising Channel Suggestion (Phase 2.2)

"""
This module provides the AI logic for suggesting optimal local advertising channels.
For the prototype, it will use a rule-based or scoring approach based on:
1.  SMB business category and subcategory.
2.  Target audience characteristics (derived from Hyperlocal Audience Targeting module - simplified for now).
3.  Campaign budget (simple tiering).
4.  Match with channel characteristics (location coverage, primary categories, audience size, cost).

It will use the LocalChannelDatabase curated previously.
"""

import json
from src.ai_modules.local_channel_db import LocalChannelDatabase
# from src.ai_modules.hyperlocal_targeting import HyperlocalTargetingModuleV2 # For audience insights, if needed directly

class ChannelSuggestionModule:
    def __init__(self, channel_db_instance):
        self.channel_db = channel_db_instance
        # self.targeting_module = HyperlocalTargetingModuleV2() # If deeper integration is needed

    def _calculate_match_score(self, channel, smb_profile, campaign_details, audience_insights):
        """Calculates a simple match score for a channel based on SMB and campaign criteria."""
        score = 0
        reasons = []

        # 1. Category Match (Major Factor)
        smb_cat = smb_profile.get("business_category", "").lower()
        smb_subcat = smb_profile.get("business_subcategory", "").lower()
        channel_cats = [c.lower() for c in channel.get("primary_categories", [])]

        if smb_cat and smb_cat in channel_cats:
            score += 30
            reasons.append(f"Strong category match: SMB category \'{smb_cat}\' is primary for channel.")
        elif smb_subcat and smb_subcat in channel_cats:
            score += 20
            reasons.append(f"Good sub-category match: SMB sub-category \'{smb_subcat}\' is relevant for channel.")
        elif any(cat_part in cc for cat_part in smb_cat.split() for cc in channel_cats if smb_cat):
            score += 10 # Partial match
            reasons.append(f"Partial category match for \'{smb_cat}\'.")

        # 2. Location Match (Pincode Overlap - Crucial)
        # This requires audience_insights to provide covered pincodes by the campaign target area
        campaign_target_pincodes = set()
        if audience_insights and "target_zones_details" in audience_insights:
            for zone in audience_insights["target_zones_details"]:
                for pc_info in zone.get("covered_pincodes_in_vicinity", []):
                    campaign_target_pincodes.add(pc_info["pincode"])
        
        channel_pincodes = set(channel.get("location_pin_codes", []))
        overlap_pincodes = campaign_target_pincodes.intersection(channel_pincodes)

        if not campaign_target_pincodes: # If campaign target area is not defined, match with SMB city
            if smb_profile.get("city", "").lower() == channel.get("location_city", "").lower():
                score += 25 # General city match
                reasons.append(f"Channel is in the same city as SMB: {smb_profile.get("city")}.")
        elif overlap_pincodes:
            overlap_percentage = (len(overlap_pincodes) / len(campaign_target_pincodes)) * 100 if campaign_target_pincodes else 0
            score += min(50, int(overlap_percentage * 0.5)) # Max 50 points for location
            reasons.append(f"Geographic overlap: {len(overlap_pincodes)} pincodes match campaign target area ({overlap_percentage:.1f}% coverage of target)." )
        else:
            # If no direct pincode overlap, but in the same city, give some points
            if smb_profile.get("city", "").lower() == channel.get("location_city", "").lower():
                score += 10
                reasons.append(f"Channel is in the same city ({channel.get("location_city")}) but no direct pincode overlap with target area.")
            else:
                return 0, ["No significant geographic match."] # No match if no geo overlap

        # 3. Budget Fit (Simplified)
        campaign_budget = campaign_details.get("total_budget", 0)
        # Assuming posting_cost_estimate_range_inr is like "500-2000 per post"
        cost_str = channel.get("posting_cost_estimate_range_inr", "0-0")
        try:
            min_cost_str, max_cost_str = cost_str.split(" per ")[0].split("-")
            min_channel_cost = float(min_cost_str) if min_cost_str.lower() != "free" else 0
            # max_channel_cost = float(max_cost_str) # Not used for now, focus on min cost
            if campaign_budget == 0: # No budget specified, assume all are fine
                 score += 5
            elif min_channel_cost == 0: # Free channel
                score += 15
                reasons.append("Budget-friendly: Channel offers free posting options.")
            elif campaign_budget >= min_channel_cost * 5: # Can afford multiple posts
                score += 10
                reasons.append("Good budget fit: Campaign budget allows for multiple engagements.")
            elif campaign_budget >= min_channel_cost:
                score += 5
                reasons.append("Budget fit: Campaign budget covers minimum channel cost.")
            else:
                score -= 10 # Penalize if budget is too low
                reasons.append("Potential budget mismatch: Minimum channel cost might be high for campaign budget.")
        except ValueError:
            reasons.append("Could not parse channel cost estimate.")
            pass # Could not parse cost

        # 4. Audience Size & Engagement (Simple bonus)
        audience_size = channel.get("audience_size_estimate", 0)
        engagement = channel.get("engagement_level", "").lower()

        if audience_size > 10000:
            score += 5
        if engagement == "high" or engagement == "very high":
            score += 10
            reasons.append(f"Good audience potential: Size {audience_size}, Engagement \'{engagement}\'.")
        elif engagement == "medium":
            score += 5

        # 5. Match with SMB Target Audience Interests (from audience_insights)
        if audience_insights and "interest_analysis" in audience_insights:
            smb_target_interests = audience_insights.get("interest_analysis", {}).get("matched_with_smb_target", {})
            if isinstance(smb_target_interests, dict) and smb_target_interests:
                score += len(smb_target_interests) * 2 # 2 points per matched interest
                reasons.append(f"Interest match: Channel aligns with {len(smb_target_interests)} of SMB target interests.")

        return max(0, score), reasons # Ensure score is not negative

    def suggest_channels(self, smb_profile, campaign_details, audience_insights, top_n=5):
        """
        Suggests top N local advertising channels.

        Args:
            smb_profile (dict): SMB profile details.
            campaign_details (dict): Campaign specific details (budget, goals etc.).
            audience_insights (dict): Insights from the HyperlocalTargetingModule.
            top_n (int): Number of top suggestions to return.

        Returns:
            list: A list of suggested channel dictionaries, with score and reasons.
        """
        all_channels = self.channel_db.get_all_channels()
        scored_channels = []

        for channel in all_channels:
            score, reasons = self._calculate_match_score(channel, smb_profile, campaign_details, audience_insights)
            if score > 0: # Only consider channels with a positive score
                scored_channels.append({
                    "channel_id": channel["channel_id"],
                    "channel_name": channel["channel_name"],
                    "channel_type": channel["channel_type"],
                    "platform": channel.get("platform"),
                    "location_city": channel.get("location_city"),
                    "audience_size_estimate": channel.get("audience_size_estimate"),
                    "posting_cost_estimate_range_inr": channel.get("posting_cost_estimate_range_inr"),
                    "url": channel.get("url"),
                    "match_score": score,
                    "reasons_for_suggestion": reasons
                })
        
        # Sort by score in descending order
        sorted_channels = sorted(scored_channels, key=lambda x: x["match_score"], reverse=True)
        return sorted_channels[:top_n]

# --- Example Usage (for testing) ---
if __name__ == "__main__":
    # Mock SMB Profile and Campaign Details (would come from DB/user input)
    mock_smb_profile_cafe = {
        "profile_id": "smb_cafe_01",
        "business_name": "The Cozy Corner Cafe",
        "business_category": "Restaurant",
        "business_subcategory": "Cafe",
        "city": "Mumbai",
        "pin_code": "400050", # Bandra
        "target_customer_profile": {"interests": ["coffee", "books", "live music"]}
    }
    mock_campaign_details_cafe = {
        "campaign_id": "camp_cafe_01",
        "campaign_name": "New Winter Menu Launch",
        "total_budget": 10000,
        "goal": "Increase footfall for new menu"
    }
    # Mock Audience Insights (would come from HyperlocalTargetingModuleV2)
    mock_audience_insights_cafe = {
        "estimated_reach": 15000,
        "target_zones_details": [
            {"source": "pincode_400050", "covered_pincodes_in_vicinity": [{"pincode": "400050"}]},
            {"source": "pincode_400001", "covered_pincodes_in_vicinity": [{"pincode": "400001"}] }
        ],
        "interest_analysis": {"matched_with_smb_target": {"coffee": 1, "books": 1}}
    }

    channel_db_instance = LocalChannelDatabase()
    suggestion_module = ChannelSuggestionModule(channel_db_instance)

    print("--- Channel Suggestions for Cozy Corner Cafe (Mumbai) ---")
    suggestions_cafe = suggestion_module.suggest_channels(
        smb_profile=mock_smb_profile_cafe,
        campaign_details=mock_campaign_details_cafe,
        audience_insights=mock_audience_insights_cafe,
        top_n=3
    )
    for i, suggestion in enumerate(suggestions_cafe):
        print(f"\nSuggestion #{i+1}:")
        print(f"  Name: {suggestion["channel_name"]} ({suggestion["platform"]})")
        print(f"  Type: {suggestion["channel_type"]}")
        print(f"  Score: {suggestion["match_score"]}")
        print(f"  Reasons: {'; '.join(suggestion['reasons_for_suggestion'])}")
        print(f"  Est. Cost: {suggestion['posting_cost_estimate_range_inr']}")

    mock_smb_profile_tech = {
        "profile_id": "smb_tech_01",
        "business_name": "Bangalore Gadget Hub",
        "business_category": "Retail",
        "business_subcategory": "Electronics",
        "city": "Bangalore",
        "pin_code": "560001", # MG Road
        "target_customer_profile": {"interests": ["technology", "gaming"]}
    }
    mock_campaign_details_tech = {
        "campaign_id": "camp_tech_01",
        "campaign_name": "Latest Smartwatch Launch",
        "total_budget": 25000,
        "goal": "Drive online sales for new smartwatch"
    }
    mock_audience_insights_tech = {
        "estimated_reach": 20000,
        "target_zones_details": [
            {"source": "pincode_560001", "covered_pincodes_in_vicinity": [{"pincode": "560001"}]},
            {"source": "pincode_560038", "covered_pincodes_in_vicinity": [{"pincode": "560038"}]}
        ],
        "interest_analysis": {"matched_with_smb_target": {"technology": 1, "gaming": 1}}
    }
    print("\n--- Channel Suggestions for Bangalore Gadget Hub ---")
    suggestions_tech = suggestion_module.suggest_channels(
        smb_profile=mock_smb_profile_tech,
        campaign_details=mock_campaign_details_tech,
        audience_insights=mock_audience_insights_tech,
        top_n=3
    )
    for i, suggestion in enumerate(suggestions_tech):
        print(f"\nSuggestion #{i+1}:")
        print(f"  Name: {suggestion["channel_name"]} ({suggestion["platform"]})")
        print(f"  Type: {suggestion["channel_type"]}")
        print(f"  Score: {suggestion["match_score"]}")
        print(f"  Reasons: {'; '.join(suggestion['reasons_for_suggestion'])}")
        print(f"  Est. Cost: {suggestion['posting_cost_estimate_range_inr']}")


