import base64
import os.path
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


class GmailScraper:
    def __init__(self):
        self.gmail_path = (
            "/Users/peter/ExperienceFlow/company-intelligence-agent/Gmail/"
        )

    def authenticate_gmail(self):
        """Authenticate and return Gmail API service instance."""
        creds = None

        # Gmail API scope for read-only access
        SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

        # Check if token.json exists for saved credentials
        if os.path.exists(self.gmail_path + "token.json"):
            creds = Credentials.from_authorized_user_file(
                self.gmail_path + "token.json", SCOPES
            )

        return build("gmail", "v1", credentials=creds)

    def fetch_emails(self, service, max_results=5):
        """Fetch emails from Gmail."""
        try:
            results = (
                service.users()
                .messages()
                .list(userId="me", maxResults=max_results, q="")
                .execute()
            )
            messages = results.get("messages", [])

            if not messages:
                print("No emails found.")
                return

            print("\nLatest Emails:\n")
            for msg in messages:
                msg_data = (
                    service.users().messages().get(userId="me", id=msg["id"]).execute()
                )

                # Extract headers
                headers = msg_data["payload"]["headers"]
                subject = next(
                    (h["value"] for h in headers if h["name"] == "Subject"),
                    "No Subject",
                )
                sender = next(
                    (h["value"] for h in headers if h["name"] == "From"),
                    "Unknown Sender",
                )

                # Extract snippet (preview of email body)
                snippet = msg_data.get("snippet", "No snippet available.")

                print(f"From: {sender}")
                print(f"Subject: {subject}")
                print(f"Snippet: {snippet[:150]}...")
                print("-" * 50)

        except HttpError as error:
            print(f"An error occurred: {error}")

    def get_email_body(self, message):
        """Extract and decode the email body."""
        try:
            parts = message.get("payload", {}).get("parts", [])

            for part in parts:
                mime_type = part.get("mimeType", "")
                body = part.get("body", {}).get("data", "")

                if mime_type == "text/plain":  # Plain text email
                    return base64.urlsafe_b64decode(body).decode("utf-8")

                elif mime_type == "text/html":  # HTML email
                    decoded_html = base64.urlsafe_b64decode(body).decode("utf-8")
                    return BeautifulSoup(
                        decoded_html, "html.parser"
                    ).get_text()  # Convert HTML to plain text

            # If email is not split into parts (fallback)
            body = message.get("payload", {}).get("body", {}).get("data", "")
            return (
                base64.urlsafe_b64decode(body).decode("utf-8")
                if body
                else "No content available."
            )

        except Exception as e:
            return f"Error decoding email: {e}"


if __name__ == "__main__":
    # Authenticate and fetch the latest emails
    scraper = GmailScraper()
    gmail_service = scraper.authenticate_gmail()
    scraper.fetch_emails(gmail_service, max_results=1)
