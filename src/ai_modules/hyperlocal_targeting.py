# AI Module: Hyperlocal Audience Targeting (Continuation - Phase 2.1)

"""
This script extends the ai_hyperlocal_targeting.py module.
It adds placeholder logic for:
1.  Integrating demographic and interest-based targeting (currently relies on mock data or simple assumptions).
2.  Developing logic for identifying potential customer clusters (rudimentary example).

Further enhancements would involve real data integration and more sophisticated ML models.
"""

import json
from math import radians, sin, cos, sqrt, atan2
from collections import Counter

# --- Geospatial Helper Functions (Haversine distance) ---
def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on the earth (specified in decimal degrees)."""
    R = 6371  # Radius of earth in kilometers
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

# --- Mock Database/Data Sources ---
MOCK_PINCODE_DB = {
    "400001": {"lat": 18.9400, "lon": 72.8347, "city": "Mumbai", "area_name": "Fort", "population_density": "High", "avg_income_level": "High", "dominant_age_group": "30-45"},
    "400050": {"lat": 19.0760, "lon": 72.8777, "city": "Mumbai", "area_name": "Bandra", "population_density": "Very High", "avg_income_level": "Very High", "dominant_age_group": "25-40"},
    "400070": {"lat": 19.0728, "lon": 72.8840, "city": "Mumbai", "area_name": "Kurla", "population_density": "High", "avg_income_level": "Medium", "dominant_age_group": "20-35"},
    "110001": {"lat": 28.6358, "lon": 77.2245, "city": "Delhi", "area_name": "Connaught Place", "population_density": "Medium", "avg_income_level": "High", "dominant_age_group": "28-50"},
    "110006": {"lat": 28.6562, "lon": 77.2410, "city": "Delhi", "area_name": "Chandni Chowk", "population_density": "Very High", "avg_income_level": "Medium", "dominant_age_group": "22-45"},
    "560001": {"lat": 12.9716, "lon": 77.5946, "city": "Bangalore", "area_name": "MG Road", "population_density": "High", "avg_income_level": "High", "dominant_age_group": "25-45"},
    "560038": {"lat": 12.9141, "lon": 77.6369, "city": "Bangalore", "area_name": "Indiranagar", "population_density": "Medium", "avg_income_level": "Very High", "dominant_age_group": "28-40"}
}

MOCK_SMB_PROFILES = {
    "smb_profile_uuid_1": {
        "business_name": "Aroma Cafe",
        "business_category": "Restaurant",
        "business_subcategory": "Cafe",
        "pin_code": "400050",
        "target_customer_profile": {"age_groups": ["18-25", "25-35"], "interests": ["coffee", "fast food", "hangout"], "income_level": ["Medium", "High"]}
    },
    "smb_profile_uuid_2": {
        "business_name": "Tech Gadgets Store",
        "business_category": "Retail",
        "business_subcategory": "Electronics",
        "pin_code": "560001",
        "target_customer_profile": {"age_groups": ["22-40", "40-55"], "interests": ["technology", "gadgets", "gaming"], "income_level": ["High", "Very High"]}
    }
}

# Mock interest data for pincodes (highly simplified)
MOCK_PINCODE_INTERESTS = {
    "400050": ["fashion", "foodie", "nightlife", "startups"],
    "110001": ["shopping", "history", "government", "business"],
    "560038": ["pubs", "IT", "luxury", "foodie"]
}

class HyperlocalTargetingModuleV2:
    def __init__(self, pincode_db=MOCK_PINCODE_DB, smb_profiles_db=MOCK_SMB_PROFILES, pincode_interests=MOCK_PINCODE_INTERESTS):
        self.pincode_db = pincode_db
        self.smb_profiles_db = smb_profiles_db
        self.pincode_interests = pincode_interests

    def _get_demographics_for_pincodes(self, pincodes):
        """Helper to aggregate mock demographic data for a list of pincodes."""
        if not pincodes:
            return {"error": "No pincodes provided for demographic analysis."}

        population_density_counts = Counter()
        avg_income_level_counts = Counter()
        dominant_age_group_counts = Counter()
        valid_pincodes_processed = 0

        for pin in pincodes:
            data = self.pincode_db.get(pin)
            if data:
                valid_pincodes_processed += 1
                population_density_counts[data.get("population_density")] += 1
                avg_income_level_counts[data.get("avg_income_level")] += 1
                dominant_age_group_counts[data.get("dominant_age_group")] += 1
        
        if valid_pincodes_processed == 0:
            return {"error": "None of the provided pincodes had demographic data."}

        return {
            "population_density_distribution": dict(population_density_counts),
            "avg_income_level_distribution": dict(avg_income_level_counts),
            "dominant_age_group_distribution": dict(dominant_age_group_counts),
            "pincodes_analyzed_count": valid_pincodes_processed
        }

    def _get_interests_for_pincodes(self, pincodes, smb_target_interests=None):
        """Helper to aggregate mock interest data and match with SMB interests."""
        if not pincodes:
            return {"error": "No pincodes provided for interest analysis."}
        
        aggregated_interests = Counter()
        matched_interests_summary = Counter()
        
        for pin in pincodes:
            interests = self.pincode_interests.get(pin, [])
            for interest in interests:
                aggregated_interests[interest] += 1
                if smb_target_interests and interest in smb_target_interests:
                    matched_interests_summary[interest] +=1

        return {
            "overall_pincode_interests": dict(aggregated_interests),
            "matched_with_smb_target": dict(matched_interests_summary) if smb_target_interests else "No SMB target interests provided"
        }

    def get_audience_insights(self, profile_id, target_area_geojson_str, business_category=None, target_radius_km=5):
        insights = {
            "estimated_reach": 0,
            "demographics": {},
            "interest_analysis": {},
            "potential_customer_clusters": [],
            "target_zones_details": [],
            "errors": [],
            "info": ""
        }

        smb_profile = self.smb_profiles_db.get(profile_id)
        if not smb_profile:
            insights["errors"].append(f"SMB Profile ID {profile_id} not found.")
            return insights
        
        smb_target_customer_profile = smb_profile.get("target_customer_profile", {})
        smb_target_interests = smb_target_customer_profile.get("interests", [])

        try:
            target_area_geojson = json.loads(target_area_geojson_str)
        except json.JSONDecodeError:
            insights["errors"].append("Invalid GeoJSON string for target_area.")
            # Fallback to SMB pincode if GeoJSON is invalid
            smb_pincode = smb_profile.get("pin_code")
            if smb_pincode:
                target_area_geojson = [smb_pincode]
                insights["info"] = "Invalid GeoJSON, falling back to SMB pincode for targeting. "
            else:
                return insights
        
        central_points = []
        if target_area_geojson.get("type") == "Point":
            lon, lat = target_area_geojson["coordinates"]
            central_points.append({"lat": lat, "lon": lon, "radius_km": target_radius_km, "source": "geojson_point"})
        elif isinstance(target_area_geojson, list): # Assuming a list of pin codes
            for pincode_item in target_area_geojson:
                pincode = str(pincode_item) # Ensure pincode is string
                if pincode in self.pincode_db:
                    loc_data = self.pincode_db[pincode]
                    central_points.append({
                        "lat": loc_data["lat"], "lon": loc_data["lon"],
                        "radius_km": target_radius_km, "source": f"pincode_{pincode}",
                        "area_name": loc_data.get("area_name", "N/A")
                    })
                else:
                    insights["errors"].append(f"Pin code {pincode} not found in database.")
        else: # Fallback for other or empty GeoJSON
            smb_pincode = smb_profile.get("pin_code")
            if smb_pincode and smb_pincode in self.pincode_db:
                loc_data = self.pincode_db[smb_pincode]
                central_points.append({
                    "lat": loc_data["lat"], "lon": loc_data["lon"],
                    "radius_km": target_radius_km, "source": f"smb_pincode_{smb_pincode}",
                    "area_name": loc_data.get("area_name", "N/A")
                })
                insights["info"] += "Used SMB pincode as target center due to unspecified/invalid target area."
            else:
                insights["errors"].append("Could not determine a central target point.")
                return insights

        if not central_points:
            insights["errors"].append("No valid central points identified for targeting.")
            return insights

        all_covered_pincodes = set()
        for cp in central_points:
            zone_detail = {
                "center_lat": cp["lat"], "center_lon": cp["lon"],
                "radius_km": cp["radius_km"], "source": cp["source"],
                "covered_pincodes_in_vicinity": []
            }
            if "area_name" in cp: zone_detail["center_area_name"] = cp["area_name"]
            current_zone_pincodes = []
            for pin, loc_data in self.pincode_db.items():
                dist = haversine(cp["lat"], cp["lon"], loc_data["lat"], loc_data["lon"])
                if dist <= cp["radius_km"]:
                    all_covered_pincodes.add(pin)
                    current_zone_pincodes.append(pin)
                    zone_detail["covered_pincodes_in_vicinity"].append({"pincode": pin, "area": loc_data.get("area_name", "N/A"), "distance_km": round(dist,2)})
            insights["target_zones_details"].append(zone_detail)
            
            # Rudimentary Customer Clustering Example (within this zone)
            # This is highly simplified. Real clustering would use more features.
            if current_zone_pincodes:
                cluster_info = {"zone_source": cp["source"], "cluster_type": "High-Income Tech Enthusiasts (Example)", "qualifying_pincodes": []}
                for pin_in_zone in current_zone_pincodes:
                    pin_data = self.pincode_db.get(pin_in_zone)
                    smb_income_targets = smb_target_customer_profile.get("income_level", [])
                    if pin_data and pin_data.get("avg_income_level") in smb_income_targets and 
                       any(interest in self.pincode_interests.get(pin_in_zone, []) for interest in ["technology", "gadgets"]):
                        cluster_info["qualifying_pincodes"].append(pin_in_zone)
                if cluster_info["qualifying_pincodes"]:
                    insights["potential_customer_clusters"].append(cluster_info)

        insights["estimated_reach"] = len(all_covered_pincodes) * 1000 # Simple estimation
        insights["demographics"] = self._get_demographics_for_pincodes(list(all_covered_pincodes))
        insights["interest_analysis"] = self._get_interests_for_pincodes(list(all_covered_pincodes), smb_target_interests)
        
        return insights

# --- Example Usage ---
if __name__ == "__main__":
    targeting_module_v2 = HyperlocalTargetingModuleV2()

    print("--- Test Case V2.1: SMB Pincode Target (Aroma Cafe) ---")
    insights_v2_1 = targeting_module_v2.get_audience_insights(
        profile_id="smb_profile_uuid_1",
        target_area_geojson_str="{}", # Fallback to SMB pincode
        business_category="Restaurant",
        target_radius_km=2
    )
    print(json.dumps(insights_v2_1, indent=2))
    print("\n")

    print("--- Test Case V2.2: GeoJSON Point Target (Tech Gadgets Store) ---")
    geojson_point_target_v2 = {"type": "Point", "coordinates": [77.5946, 12.9716]} # MG Road, Bangalore
    insights_v2_2 = targeting_module_v2.get_audience_insights(
        profile_id="smb_profile_uuid_2",
        target_area_geojson_str=json.dumps(geojson_point_target_v2),
        business_category="Retail",
        target_radius_km=3
    )
    print(json.dumps(insights_v2_2, indent=2))
    print("\n")

    print("--- Test Case V2.3: List of Pincodes (Aroma Cafe, mixed areas) ---")
    pincode_list_target_v2 = ["400001", "110006"] # Fort (Mumbai) & Chandni Chowk (Delhi)
    insights_v2_3 = targeting_module_v2.get_audience_insights(
        profile_id="smb_profile_uuid_1",
        target_area_geojson_str=json.dumps(pincode_list_target_v2),
        business_category="Restaurant",
        target_radius_km=1 # Small radius around each pincode center
    )
    print(json.dumps(insights_v2_3, indent=2))

