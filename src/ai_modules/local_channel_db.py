# AI Module: Local Advertising Channel Database (Phase 2.2)

"""
This module defines the structure and initial mock data for a database of
local advertising channels in India. This database will be used by the
AI Channel Suggestion Module.

For the prototype, this will be a simple in-memory structure.
In a production system, this would be stored in a proper database (e.g., PostgreSQL)
and managed through an admin interface or automated curation processes.
"""

import json

class LocalChannelDatabase:
    def __init__(self):
        self.channels = [
            # --- Local Social Media Groups/Pages ---
            {
                "channel_id": "chan_sm_mum_foodies_01",
                "channel_name": "Mumbai Food Lovers (Facebook Group)",
                "channel_type": "Social Media Group",
                "platform": "Facebook",
                "location_city": "Mumbai",
                "location_pin_codes": ["400001", "400002", "400050", "400070"], # Covers multiple areas
                "primary_categories": ["Food & Beverage", "Restaurant", "Cafe"],
                "audience_size_estimate": 50000,
                "engagement_level": "High", # e.g., High, Medium, Low
                "posting_cost_estimate_range_inr": "500-2000 per post", # Varies
                "contact_info": "group_admin@example.com",
                "url": "https://facebook.com/groups/mumbaifoodlovers",
                "notes": "Good for restaurants, cafes, food delivery services in Mumbai."
            },
            {
                "channel_id": "chan_sm_del_events_01",
                "channel_name": "Delhi Weekend Events (Instagram Page)",
                "channel_type": "Social Media Page",
                "platform": "Instagram",
                "location_city": "Delhi",
                "location_pin_codes": ["110001", "110006", "110016"],
                "primary_categories": ["Events", "Entertainment", "Lifestyle"],
                "audience_size_estimate": 25000,
                "engagement_level": "Medium",
                "posting_cost_estimate_range_inr": "1000-3000 per story/post",
                "contact_info": "delhievents@example.com",
                "url": "https://instagram.com/delhiweekendevents",
                "notes": "Suitable for promoting local events, workshops, entertainment venues."
            },
            {
                "channel_id": "chan_sm_blr_tech_01",
                "channel_name": "Bangalore Tech Connect (LinkedIn Group)",
                "channel_type": "Social Media Group",
                "platform": "LinkedIn",
                "location_city": "Bangalore",
                "location_pin_codes": ["560001", "560038", "560066", "560095"],
                "primary_categories": ["Technology", "Startups", "Professional Services", "B2B"],
                "audience_size_estimate": 15000,
                "engagement_level": "Medium",
                "posting_cost_estimate_range_inr": "Free (if relevant content) or sponsored post (contact admin)",
                "contact_info": "admin@bltechconnect.com",
                "url": "https://linkedin.com/groups/bloretechconnect",
                "notes": "Good for B2B services, tech product launches, hiring in Bangalore."
            },

            # --- Local Influencers ---
            {
                "channel_id": "chan_inf_mum_fashion_riya_01",
                "channel_name": "Riya Sharma (Mumbai Fashion Blogger)",
                "channel_type": "Influencer",
                "platform": "Instagram",
                "location_city": "Mumbai",
                "location_pin_codes": ["400050", "400053", "400054"], # Focus on Bandra, Juhu, Andheri
                "primary_categories": ["Fashion", "Lifestyle", "Beauty"],
                "audience_size_estimate": 75000,
                "engagement_level": "High",
                "posting_cost_estimate_range_inr": "5000-15000 per post",
                "contact_info": "riya.sharma.fashion@example.com",
                "url": "https://instagram.com/riyasharmafashion",
                "notes": "Targets young, fashion-conscious audience in western Mumbai."
            },
            {
                "channel_id": "chan_inf_del_food_ankit_01",
                "channel_name": "Ankit Kumar (Delhi Food Vlogger)",
                "channel_type": "Influencer",
                "platform": "YouTube",
                "location_city": "Delhi NCR",
                "location_pin_codes": ["110001", "110012", "110016", "122002"], # Delhi & Gurgaon
                "primary_categories": ["Food & Beverage", "Restaurant Review"],
                "audience_size_estimate": 120000, # Subscribers
                "engagement_level": "Very High",
                "posting_cost_estimate_range_inr": "10000-25000 per dedicated video",
                "contact_info": "ankitfoodvlogs@example.com",
                "url": "https://youtube.com/c/ankitfoodvlogs",
                "notes": "Known for street food and fine dining reviews across Delhi NCR."
            },

            # --- Local Classifieds/Directories ---
            {
                "channel_id": "chan_dir_pune_services_01",
                "channel_name": "Pune Local Services (Online Directory)",
                "channel_type": "Local Directory",
                "platform": "Web",
                "location_city": "Pune",
                "location_pin_codes": ["411001", "411007", "411016", "411028"],
                "primary_categories": ["Home Services", "Repairs", "Local Businesses", "Education"],
                "audience_size_estimate": 10000, # Monthly visitors
                "engagement_level": "Low", # Typically for search, not browsing
                "posting_cost_estimate_range_inr": "200-1000 for featured listing per month",
                "contact_info": "support@punelocalservices.com",
                "url": "https://punelocalservices.example.com",
                "notes": "Good for service-based businesses targeting specific Pune localities."
            },

            # --- Community Event Boards/Portals ---
            {
                "channel_id": "chan_event_hyd_community_01",
                "channel_name": "Hyderabad Community Events Portal",
                "channel_type": "Event Portal",
                "platform": "Web",
                "location_city": "Hyderabad",
                "location_pin_codes": ["500001", "500032", "500081"],
                "primary_categories": ["Community Events", "Workshops", "Local Meetups", "Festivals"],
                "audience_size_estimate": 5000, # Active users/subscribers
                "engagement_level": "Medium",
                "posting_cost_estimate_range_inr": "Free for community events, 500-1500 for commercial event promotion",
                "contact_info": "contact@hydevents.org",
                "url": "https://hydevents.example.org",
                "notes": "Platform for promoting local gatherings and events in Hyderabad."
            }
        ]

    def get_all_channels(self):
        return self.channels

    def find_channels(self, city=None, pin_codes=None, categories=None, channel_type=None):
        """
        Finds channels based on specified criteria.
        Args:
            city (str, optional): City to filter by.
            pin_codes (list, optional): List of pin codes to filter by (channel must cover at least one).
            categories (list, optional): List of business categories (channel must match at least one).
            channel_type (str, optional): Specific type of channel.
        Returns:
            list: A list of matching channels.
        """
        results = []
        for channel in self.channels:
            match = True
            if city and channel.get("location_city").lower() != city.lower():
                match = False
            if pin_codes and not any(pc in channel.get("location_pin_codes", []) for pc in pin_codes):
                match = False
            if categories and not any(cat in channel.get("primary_categories", []) for cat in categories):
                match = False
            if channel_type and channel.get("channel_type").lower() != channel_type.lower():
                match = False
            
            if match:
                results.append(channel)
        return results

    def add_channel(self, channel_data):
        """Adds a new channel to the in-memory list. Needs proper ID generation in a real system."""
        # Basic validation
        if not all(k in channel_data for k in ["channel_id", "channel_name", "channel_type", "location_city"]):
            raise ValueError("Required fields missing for new channel.")
        if any(c["channel_id"] == channel_data["channel_id"] for c in self.channels):
            raise ValueError(f"Channel ID {channel_data['channel_id']} already exists.")
        self.channels.append(channel_data)
        return True

# --- Example Usage ---
if __name__ == "__main__":
    channel_db = LocalChannelDatabase()

    print(f"Total channels in DB: {len(channel_db.get_all_channels())}\n")

    print("--- Channels in Mumbai for Food & Beverage ---")
    mumbai_food_channels = channel_db.find_channels(city="Mumbai", categories=["Food & Beverage"])
    for channel in mumbai_food_channels:
        print(f"- {channel['channel_name']} ({channel['channel_type']})")
    print("\n")

    print("--- Influencers in Delhi ---")
    delhi_influencers = channel_db.find_channels(city="Delhi", channel_type="Influencer")
    for channel in delhi_influencers:
        print(f"- {channel['channel_name']} on {channel['platform']}")
    print("\n")

    print("--- Channels covering pin code 560038 (Bangalore - Indiranagar) ---")
    indiranagar_channels = channel_db.find_channels(pin_codes=["560038"])
    for channel in indiranagar_channels:
        print(f"- {channel['channel_name']}")
    print("\n")

    # Example of adding a new channel (in a real app, ID would be auto-generated)
    try:
        new_channel_data = {
            "channel_id": "chan_sm_kol_books_01",
            "channel_name": "Kolkata Book Readers Club (WhatsApp Group)",
            "channel_type": "Social Media Group",
            "platform": "WhatsApp",
            "location_city": "Kolkata",
            "location_pin_codes": ["700001", "700012"],
            "primary_categories": ["Books", "Literature", "Community"],
            "audience_size_estimate": 500,
            "engagement_level": "High",
            "posting_cost_estimate_range_inr": "Free (admin approval needed)",
            "contact_info": "kolkatabooks.admin@example.com",
            "url": "N/A (WhatsApp Group)",
            "notes": "For local book promotions and author meetups in Kolkata."
        }
        channel_db.add_channel(new_channel_data)
        print(f"Successfully added '{new_channel_data['channel_name']}'. New total: {len(channel_db.get_all_channels())}")
    except ValueError as e:
        print(f"Error adding channel: {e}")

