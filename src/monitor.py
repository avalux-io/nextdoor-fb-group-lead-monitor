#!/usr/bin/env python3
"""
Main monitoring orchestrator for Nextdoor and Facebook Groups lead detection.

This module coordinates platform monitoring, applies geographic and intent filters,
and triggers notifications for qualified leads.
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .platforms.nextdoor import NextdoorClient
from .platforms.facebook import FacebookGroupsClient
from .scoring.intent_scorer import IntentScorer
from .geo.radius_filter import RadiusFilter
from .notifications.webhook import WebhookNotifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LeadMonitor:
    """Main orchestrator for social platform lead monitoring."""
    
    def __init__(self, config_path: str = "config/"):
        self.config_path = config_path
        self.load_configuration()
        self.setup_clients()
        
    def load_configuration(self):
        """Load monitoring configuration from JSON files."""
        with open(f"{self.config_path}/keywords.json", "r") as f:
            self.keywords = json.load(f)
            
        with open(f"{self.config_path}/scoring_weights.json", "r") as f:
            self.scoring_config = json.load(f)
            
        with open(f"{self.config_path}/geo_boundaries.json", "r") as f:
            self.geo_config = json.load(f)
            
    def setup_clients(self):
        """Initialize platform clients and filters."""
        # Platform clients
        self.nextdoor = NextdoorClient(
            client_id=os.getenv('NEXTDOOR_CLIENT_ID'),
            client_secret=os.getenv('NEXTDOOR_CLIENT_SECRET')
        )
        
        self.facebook = FacebookGroupsClient(
            access_token=os.getenv('FACEBOOK_ACCESS_TOKEN')
        )
        
        # Geographic filter
        self.geo_filter = RadiusFilter(
            center_lat=float(os.getenv('BUSINESS_LATITUDE')),
            center_lng=float(os.getenv('BUSINESS_LONGITUDE')),
            radius_miles=int(os.getenv('DEFAULT_SERVICE_RADIUS_MILES', 15))
        )
        
        # Intent scoring
        self.intent_scorer = IntentScorer(self.scoring_config)
        
        # Notifications
        self.notifier = WebhookNotifier(
            webhook_url=os.getenv('WEBHOOK_URL'),
            webhook_secret=os.getenv('WEBHOOK_SECRET')
        )
        
    def monitor_platforms(self, duration_minutes: int = 60):
        """Run monitoring loop for specified duration."""
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        logger.info(f"Starting lead monitoring for {duration_minutes} minutes")
        
        while datetime.now() < end_time:
            try:
                # Monitor Nextdoor
                nextdoor_posts = self.nextdoor.get_recent_posts(
                    keywords=self.keywords["all_services"],
                    since=datetime.now() - timedelta(minutes=5)
                )
                
                for post in nextdoor_posts:
                    self.process_post(post, "nextdoor")
                
                # Monitor Facebook Groups
                facebook_posts = self.facebook.get_recent_group_posts(
                    group_ids=self.geo_config["facebook_groups"],
                    keywords=self.keywords["all_services"],
                    since=datetime.now() - timedelta(minutes=5)
                )
                
                for post in facebook_posts:
                    self.process_post(post, "facebook")
                
                # Wait before next polling cycle
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)  # Shorter wait on error
                
        logger.info("Monitoring session completed")
        
    def process_post(self, post: Dict, platform: str):
        """Process individual post through filtering and scoring pipeline."""
        try:
            # Geographic filtering
            if not self.is_in_service_area(post):
                return
            
            # Intent scoring
            score_data = self.intent_scorer.score_post(post)
            
            if score_data["total_score"] < int(os.getenv('MIN_LEAD_SCORE', 60)):
                return
            
            # Create lead record
            lead = {
                "lead_id": f"{platform}_{post['id']}",
                "platform": platform,
                "score": score_data["total_score"],
                "post_data": {
                    "text": post["text"],
                    "author": post["author"],
                    "location": post.get("location", "Unknown"),
                    "post_url": post["url"],
                    "timestamp": post["created_at"]
                },
                "scoring_breakdown": score_data["breakdown"],
                "recommended_action": self.get_recommended_action(score_data["total_score"])
            }
            
            # Send notification
            self.notifier.send_lead_notification(lead)
            
            logger.info(f"New lead detected: {lead['lead_id']} (score: {lead['score']})")
            
        except Exception as e:
            logger.error(f"Error processing post {post.get('id', 'unknown')}: {e}")
            
    def is_in_service_area(self, post: Dict) -> bool:
        """Check if post location falls within service area."""
        if "latitude" not in post or "longitude" not in post:
            # If no location data, check if it's from a known local group
            group_id = post.get("group_id")
            return group_id in self.geo_config.get("approved_groups", [])
        
        return self.geo_filter.contains(post["latitude"], post["longitude"])
    
    def get_recommended_action(self, score: int) -> str:
        """Determine recommended response urgency based on score."""
        if score >= int(os.getenv('URGENT_LEAD_THRESHOLD', 80)):
            return "immediate_response"
        elif score >= 70:
            return "respond_within_hour"
        else:
            return "respond_within_day"

def main():
    """CLI entry point for lead monitoring."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor local social platforms for leads")
    parser.add_argument("--duration", type=int, default=60, help="Monitoring duration in minutes")
    parser.add_argument("--test-mode", action="store_true", help="Run in test mode with sample data")
    parser.add_argument("--platform", choices=["nextdoor", "facebook", "both"], default="both")
    
    args = parser.parse_args()
    
    monitor = LeadMonitor()
    
    if args.test_mode:
        logger.info("Running in test mode")
        # Add test mode logic here
    else:
        monitor.monitor_platforms(duration_minutes=args.duration)

if __name__ == "__main__":
    main()