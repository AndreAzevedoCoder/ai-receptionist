import logging
from datetime import datetime, timedelta
from typing import Optional

from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from backend.features.leads.models import Lead
from .models import ScheduledMeeting

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Service for interacting with Google Calendar API."""

    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self):
        self.credentials = None
        self.service = None
        self.calendar_id = settings.GOOGLE_CALENDAR_ID

    def authenticate(self) -> bool:
        """Authenticate with Google Calendar using service account credentials."""
        credentials_path = settings.GOOGLE_CALENDAR_CREDENTIALS_PATH

        if not credentials_path:
            logger.warning("Google Calendar credentials path not configured")
            return False

        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=self.SCOPES,
            )
            self.service = build('calendar', 'v3', credentials=self.credentials)
            return True
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Calendar: {e}")
            return False

    def get_available_slots(
        self,
        date: datetime,
        duration_minutes: int = 30,
        start_hour: int = 9,
        end_hour: int = 17,
    ) -> list[dict]:
        """
        Get available time slots for a given date.

        Args:
            date: The date to check availability for
            duration_minutes: Duration of the meeting in minutes
            start_hour: Start of business hours (24h format)
            end_hour: End of business hours (24h format)

        Returns:
            List of available slots with start and end times
        """
        if not self.service:
            if not self.authenticate():
                return []

        # Set time bounds for the day
        time_min = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        time_max = date.replace(hour=end_hour, minute=0, second=0, microsecond=0)

        try:
            # Get busy times
            body = {
                'timeMin': time_min.isoformat() + 'Z',
                'timeMax': time_max.isoformat() + 'Z',
                'items': [{'id': self.calendar_id}],
            }
            result = self.service.freebusy().query(body=body).execute()
            busy_times = result.get('calendars', {}).get(self.calendar_id, {}).get('busy', [])

            # Calculate available slots
            available_slots = []
            current_time = time_min
            slot_duration = timedelta(minutes=duration_minutes)

            for busy in busy_times:
                busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))

                # Add available slots before this busy period
                while current_time + slot_duration <= busy_start:
                    available_slots.append({
                        'start': current_time.isoformat(),
                        'end': (current_time + slot_duration).isoformat(),
                    })
                    current_time += slot_duration

                # Move current time to after the busy period
                current_time = max(current_time, busy_end)

            # Add remaining slots after all busy periods
            while current_time + slot_duration <= time_max:
                available_slots.append({
                    'start': current_time.isoformat(),
                    'end': (current_time + slot_duration).isoformat(),
                })
                current_time += slot_duration

            return available_slots

        except HttpError as e:
            logger.error(f"Error fetching availability: {e}")
            return []

    def create_meeting(
        self,
        lead: Lead,
        scheduled_time: datetime,
        duration_minutes: int = 30,
        title: str = 'Meeting',
        description: str = '',
    ) -> Optional[ScheduledMeeting]:
        """
        Create a calendar event and store the meeting in the database.

        Args:
            lead: The lead to schedule the meeting with
            scheduled_time: When the meeting should occur
            duration_minutes: Duration in minutes
            title: Meeting title
            description: Meeting description

        Returns:
            ScheduledMeeting instance if successful, None otherwise
        """
        if not self.service:
            if not self.authenticate():
                return None

        end_time = scheduled_time + timedelta(minutes=duration_minutes)

        event = {
            'summary': f"{title} - {lead.name}",
            'description': f"Lead: {lead.name}\nPhone: {lead.phone_number}\n\n{description}",
            'start': {
                'dateTime': scheduled_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            },
            'attendees': [],
        }

        # Add attendee if lead has email
        if lead.email:
            event['attendees'].append({'email': lead.email})

        try:
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event,
            ).execute()

            # Store in database
            meeting = ScheduledMeeting.objects.create(
                lead=lead,
                google_event_id=created_event['id'],
                title=title,
                description=description,
                scheduled_time=scheduled_time,
                duration_minutes=duration_minutes,
                status='scheduled',
            )

            logger.info(f"Created meeting {meeting.id} for lead {lead.id}")
            return meeting

        except HttpError as e:
            logger.error(f"Error creating calendar event: {e}")
            return None

    def cancel_meeting(self, meeting: ScheduledMeeting) -> bool:
        """
        Cancel a scheduled meeting.

        Args:
            meeting: The meeting to cancel

        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            if not self.authenticate():
                return False

        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=meeting.google_event_id,
            ).execute()

            meeting.status = 'cancelled'
            meeting.save()

            logger.info(f"Cancelled meeting {meeting.id}")
            return True

        except HttpError as e:
            logger.error(f"Error cancelling calendar event: {e}")
            return False
