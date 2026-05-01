"""
Locust Load Testing Suite for Customer Success FTE System
Simulates multi-channel traffic under heavy load
"""

from locust import HttpUser, task, between, events, constant
import random
import string
import json
from datetime import datetime
import hmac
import hashlib
from urllib.parse import urlencode


class WebFormUser(HttpUser):
    """Simulate users submitting web forms"""
    wait_time = between(1, 3)

    @task(3)
    def submit_web_form(self):
        """Submit a web support form"""
        form_data = {
            "customer_name": f"Customer_{random.randint(1000, 9999)}",
            "email": f"user{random.randint(1000, 9999)}@example.com",
            "subject": f"Issue with account {random.randint(100, 999)}",
            "category": random.choice(["general", "technical", "billing", "feedback", "bug_report"]),
            "priority": random.choice(["low", "medium", "high"]),
            "message": f"This is a test message. {random.choice(['Need help with payment', 'System is slow', 'Feature request', 'Bug report'])} {random.randint(1000, 9999)}",
            "channel": "web_form"
        }
        self.client.post("/api/messages/submit", json=form_data)

    @task(1)
    def check_health(self):
        """Check API health status"""
        self.client.get("/api/health")

    @task(1)
    def check_metrics(self):
        """Check channel metrics"""
        self.client.get("/api/metrics/channels")


class WhatsAppUser(HttpUser):
    """Simulate WhatsApp webhook traffic"""
    wait_time = between(2, 5)

    def generate_twilio_signature(self, url, params, auth_token):
        """Generate Twilio X-Twilio-Signature header"""
        s = url
        for key in sorted(params.keys()):
            s += key + params[key]
        mac = hmac.new(
            auth_token.encode(),
            s.encode(),
            hashlib.sha1
        )
        return mac.digest().hex()

    @task(3)
    def send_whatsapp_message(self):
        """Simulate incoming WhatsApp message via Twilio webhook"""
        message_body = random.choice([
            "Hi, I need help with my account",
            "Can you tell me about pricing?",
            "I'm having technical issues",
            "Is there a discount available?",
            "I want to upgrade my plan"
        ])

        params = {
            "MessageSid": f"SM{random.randint(10000000000000000000, 99999999999999999999)}",
            "AccountSid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "From": f"whatsapp:+1234567890",
            "To": "whatsapp:+16075551234",
            "Body": message_body,
            "NumMedia": "0"
        }

        url = "http://localhost:8000/api/whatsapp/webhook"
        auth_token = "your_auth_token_here"
        signature = self.generate_twilio_signature(url, params, auth_token)

        headers = {
            "X-Twilio-Signature": signature,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        self.client.post(
            "/api/whatsapp/webhook",
            data=params,
            headers=headers,
            name="/api/whatsapp/webhook"
        )

    @task(1)
    def check_health(self):
        """Check health status"""
        self.client.get("/health")


class EmailUser(HttpUser):
    """Simulate email webhook traffic"""
    wait_time = between(3, 7)

    @task(2)
    def send_email_webhook(self):
        """Simulate incoming email via Gmail"""
        email_data = {
            "message": {
                "data": "test email data",
                "attributes": {
                    "email": f"user{random.randint(1000, 9999)}@gmail.com",
                    "subject": random.choice([
                        "Question about billing",
                        "Technical support needed",
                        "Feature request",
                        "Feedback on your service",
                        "Account issue"
                    ]),
                    "body": f"This is a test email message {random.randint(1000, 9999)}"
                }
            }
        }

        self.client.post(
            "/api/gmail/webhook",
            json=email_data,
            name="/api/gmail/webhook"
        )

    @task(1)
    def check_kafka_health(self):
        """Check Kafka health"""
        self.client.get("/api/health/kafka")


class ConcurrentMixedUser(HttpUser):
    """Mixed concurrent user simulating multiple channel traffic"""
    wait_time = between(1, 2)

    @task(2)
    def web_form_submission(self):
        """Heavy web form traffic"""
        form_data = {
            "customer_name": f"Concurrent_{random.randint(1000, 9999)}",
            "email": f"test{random.randint(1000, 9999)}@example.com",
            "subject": f"Concurrent test {random.randint(100, 999)}",
            "category": random.choice(["general", "technical", "billing", "feedback", "bug_report"]),
            "priority": random.choice(["low", "medium", "high"]),
            "message": f"Load test message {random.randint(1000, 99999)}. Testing system under stress.",
            "channel": "web_form"
        }
        self.client.post("/api/messages/submit", json=form_data)

    @task(1)
    def customer_lookup(self):
        """Lookup customer information"""
        email = f"customer{random.randint(1, 1000)}@example.com"
        self.client.get(f"/api/customers/lookup?email={email}")

    @task(1)
    def fetch_metrics(self):
        """Fetch metrics during load test"""
        self.client.get("/api/metrics/channels")

    @task(1)
    def health_checks(self):
        """Continuous health checks"""
        self.client.get("/api/health")


class StressTestUser(HttpUser):
    """Aggressive stress testing - maximum load"""
    wait_time = constant(0.1)

    @task(5)
    def rapid_form_submissions(self):
        """Rapid-fire form submissions"""
        form_data = {
            "customer_name": f"Stress_{random.randint(10000, 99999)}",
            "email": f"stress{random.randint(10000, 99999)}@test.com",
            "subject": f"Stress test issue",
            "category": "technical",
            "priority": "high",
            "message": f"Stress test message - iteration {random.randint(1, 10000)}",
            "channel": "web_form"
        }
        self.client.post("/api/messages/submit", json=form_data)

    @task(2)
    def rapid_metrics_check(self):
        """Rapid metrics polling"""
        self.client.get("/api/metrics/channels")


# Event handlers for load test statistics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize load test"""
    print("\n" + "="*80)
    print("LOAD TEST STARTED - Customer Success FTE System")
    print("="*80)
    print(f"Start time: {datetime.now().isoformat()}")
    print(f"Test simulates:")
    print("  - WebFormUser: Standard web form submissions")
    print("  - WhatsAppUser: Twilio webhook traffic (WhatsApp)")
    print("  - EmailUser: Gmail webhook traffic")
    print("  - ConcurrentMixedUser: Mixed multi-channel traffic")
    print("  - StressTestUser: Aggressive stress testing")
    print("="*80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Finalize load test"""
    print("\n" + "="*80)
    print("LOAD TEST COMPLETED")
    print("="*80)
    print(f"End time: {datetime.now().isoformat()}")
    print("\nFinal Statistics:")
    print(f"  Total requests: {environment.stats.total.num_requests}")
    print(f"  Total failures: {environment.stats.total.num_failures}")
    print(f"  Success rate: {((environment.stats.total.num_requests - environment.stats.total.num_failures) / environment.stats.total.num_requests * 100):.2f}%")
    print(f"  Average response time: {environment.stats.total.avg_response_time:.0f}ms")
    print(f"  P95 response time: {environment.stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"  P99 response time: {environment.stats.total.get_response_time_percentile(0.99):.0f}ms")
    print("="*80 + "\n")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Log individual requests for debugging"""
    if exception:
        print(f"[ERROR] {request_type} {name}: {exception}")


# Configuration for load test scenarios
LOAD_TEST_SCENARIOS = {
    "light_load": {
        "description": "Light load - 10 concurrent users",
        "users": 10,
        "spawn_rate": 2,
        "duration": "5m",
        "target_rps": 50
    },
    "moderate_load": {
        "description": "Moderate load - 50 concurrent users",
        "users": 50,
        "spawn_rate": 5,
        "duration": "15m",
        "target_rps": 500
    },
    "heavy_load": {
        "description": "Heavy load - 200 concurrent users",
        "users": 200,
        "spawn_rate": 10,
        "duration": "30m",
        "target_rps": 2000
    },
    "stress_test": {
        "description": "Stress test - maximum load",
        "users": 500,
        "spawn_rate": 25,
        "duration": "20m",
        "target_rps": 5000
    },
    "multi_channel_24h": {
        "description": "24-hour multi-channel test",
        "users": 300,
        "spawn_rate": 15,
        "duration": "24h",
        "target_rps": 3000,
        "notes": "Balanced mix of web forms, WhatsApp, and email"
    }
}


if __name__ == "__main__":
    print("\n" + "="*80)
    print("LOAD TEST SCENARIOS")
    print("="*80)
    for scenario_name, config in LOAD_TEST_SCENARIOS.items():
        print(f"\n{scenario_name.upper()}")
        print(f"  Description: {config['description']}")
        print(f"  Users: {config['users']}")
        print(f"  Spawn rate: {config['spawn_rate']} users/sec")
        print(f"  Duration: {config['duration']}")
        print(f"  Target RPS: {config['target_rps']}")
        if "notes" in config:
            print(f"  Notes: {config['notes']}")
    print("\n" + "="*80)
    print("\nRun with:")
    print("  locust -f production/tests/load_test.py --host=http://localhost:8000")
    print("  locust -f production/tests/load_test.py --host=http://localhost:8000 -u 50 -r 5 -t 15m")
    print("  locust -f production/tests/load_test.py --host=http://api.cloudflow.example.com")
    print("="*80 + "\n")
