import base64
import logging
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class GmailScraper:
    def __init__(self, max_results=5):
        logging.info("Initializing GmailScraper...")

        # Gmail API scope for read-only access
        SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
        creds = None
        path = "/Users/peter/ExperienceFlow/company-intelligence-agent/Gmail/"

        try:
            # Load credentials (use token.json for the saved credentials)
            creds = Credentials.from_authorized_user_file(path + "token.json", SCOPES)
            self.service = build("gmail", "v1", credentials=creds)
            self.max_results = max_results
            logging.info("Gmail API authentication successful.")
        except Exception as e:
            logging.error(f"Failed to authenticate Gmail API: {e}")
            raise

    def fetch_emails(self):
        """Fetches emails from Gmail."""
        logging.info(f"Fetching up to {self.max_results} latest emails...")
        try:
            results = (
                self.service.users()
                .messages()
                .list(userId="me", maxResults=self.max_results, q="")
                .execute()
            )
            messages = results.get("messages", [])

            if not messages:
                logging.info("No new emails found.")
            else:
                logging.info(f"Retrieved {len(messages)} email(s).")

            return messages

        except HttpError as error:
            logging.error(f"Error fetching emails: {error}")
            return []

    def get_email_body(self, messages):
        """Extracts and decodes the email body."""
        logging.info("Extracting email bodies...")
        bodies = {}

        for msg in messages:
            try:
                body = None
                ID = msg.get("id", "unknown_id")
                logging.info(f"Fetching full content for email ID: {ID}")

                # Fetch full email content using message ID
                message = (
                    self.service.users().messages().get(userId="me", id=ID).execute()
                )

                # Extract payload (full email content)
                payload = message.get("payload", {})
                parts = payload.get("parts", [])

                # Some emails contain both plain text and HTML parts
                for part in parts:
                    mime_type = part.get("mimeType", "")
                    body = part.get("body", {}).get("data", "")

                    # Decode plain text email
                    if mime_type == "text/plain":
                        body = base64.urlsafe_b64decode(body).decode("utf-8")
                        logging.info(f"Decoded text/plain content for {ID}")
                        break

                    # Decode HTML email and convert to plain text
                    elif mime_type == "text/html":
                        html = base64.urlsafe_b64decode(body).decode("utf-8")
                        body = BeautifulSoup(html, "html.parser").get_text()
                        logging.info(f"Decoded text/html content for {ID}")
                        break

                # If not split into parts; stored directly in payload.body
                if not body:
                    payload_body = payload.get("body", {}).get("data", "")
                    body = (
                        base64.urlsafe_b64decode(payload_body).decode("utf-8")
                        if body
                        else "No content available."
                    )
                    logging.warning(f"No parts found, using fallback for {ID}")

                # Store email bodies in dictionary
                bodies[ID] = body

            except Exception as e:
                logging.error(f"Error decoding email ID {ID}: {e}")
                bodies[ID] = f"Error decoding email: {e}"

        return bodies


if __name__ == "__main__":
    scraper = GmailScraper(max_results=2)
    messages = scraper.fetch_emails()

    if messages:
        bodies = scraper.get_email_body(messages)
        for ID, body in bodies.items():
            logging.info(f"\nMessage ID: {ID}\nBody:\n{body}\n" + "-" * 50)
    else:
        logging.info("No messages to process.")
