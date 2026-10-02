"""Follow-up Agent - Handles post-event surveys, thank-you emails, and lead nurturing."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from event_management.agents.base import AgentContext, BaseAgent


class SurveyQuestion(BaseModel):
    """A survey question for post-event feedback."""

    question_id: str
    question_text: str
    question_type: str  # rating, multiple_choice, open_ended, nps
    options: list[str] = Field(default_factory=list)
    required: bool = True
    category: str = "general"  # content, venue, speakers, overall, logistics


class FollowUpEmail(BaseModel):
    """A follow-up email in the sequence."""

    email_id: str
    subject: str
    body_template: str
    timing: str  # T+1 day, T+3 days, T+7 days, T+14 days
    audience: str  # all_attendees, speakers, sponsors, no_shows
    goal: str
    cta: str = ""


class LeadNurtureAction(BaseModel):
    """A lead nurturing action."""

    action_type: str  # email, call, demo, content_download, meeting
    description: str
    target_segment: str
    timing: str
    priority: str = "medium"  # low, medium, high


class FollowUpInput(BaseModel):
    """Input for the Follow-up Agent."""

    event_name: str
    event_date: str
    attendee_count: int
    speaker_count: int
    sponsor_count: int
    nps_score: float | None = None
    feedback_highlights: list[str] = Field(default_factory=list)
    leads_generated: int = 0
    follow_up_goals: list[str] = Field(default_factory=list)


class FollowUpOutput(BaseModel):
    """Output from the Follow-up Agent."""

    survey: list[SurveyQuestion] = Field(default_factory=list)
    email_sequence: list[FollowUpEmail] = Field(default_factory=list)
    lead_nurture_plan: list[LeadNurtureAction] = Field(default_factory=list)
    content_recommendations: list[str] = Field(default_factory=list)
    follow_up_timeline: list[dict[str, Any]] = Field(default_factory=list)
    success_metrics: dict[str, float] = Field(default_factory=dict)


class FollowUpAgent(BaseAgent[FollowUpInput, FollowUpOutput]):
    """Agent responsible for post-event follow-up and engagement."""

    @property
    def name(self) -> str:
        return "FollowUpAgent"

    async def execute(self, input_data: FollowUpInput, context: AgentContext) -> FollowUpOutput:
        """Generate a comprehensive follow-up plan.

        Args:
            input_data: The follow-up requirements and event data.
            context: Execution context with event and user info.

        Returns:
            A complete follow-up plan with surveys, emails, and lead nurturing.
        """
        self.logger.info(
            "generating_followup_plan",
            event_name=input_data.event_name,
            attendee_count=input_data.attendee_count,
            leads_generated=input_data.leads_generated,
        )

        survey = self._create_survey(input_data)
        email_sequence = self._create_email_sequence(input_data)
        lead_nurture = self._create_lead_nurture_plan(input_data)
        content_recs = self._recommend_content(input_data)
        timeline = self._create_follow_up_timeline(input_data)
        metrics = self._define_success_metrics(input_data)

        return FollowUpOutput(
            survey=survey,
            email_sequence=email_sequence,
            lead_nurture_plan=lead_nurture,
            content_recommendations=content_recs,
            follow_up_timeline=timeline,
            success_metrics=metrics,
        )

    def _create_survey(self, data: FollowUpInput) -> list[SurveyQuestion]:
        """Create a post-event survey."""
        return [
            SurveyQuestion(
                question_id="nps_overall",
                question_text=(
                    "How likely are you to recommend this event to a colleague or friend?"
                ),
                question_type="nps",
                required=True,
                category="overall",
            ),
            SurveyQuestion(
                question_id="content_quality",
                question_text="How would you rate the quality of the content presented?",
                question_type="rating",
                required=True,
                category="content",
            ),
            SurveyQuestion(
                question_id="speaker_quality",
                question_text="How would you rate the speakers and presentations?",
                question_type="rating",
                required=True,
                category="speakers",
            ),
            SurveyQuestion(
                question_id="venue_satisfaction",
                question_text="How satisfied were you with the venue and facilities?",
                question_type="rating",
                required=True,
                category="venue",
            ),
            SurveyQuestion(
                question_id="logistics",
                question_text=(
                    "How would you rate the event logistics (check-in, signage, schedule)?"
                ),
                question_type="rating",
                required=True,
                category="logistics",
            ),
            SurveyQuestion(
                question_id="most_valuable",
                question_text="What was the most valuable part of the event?",
                question_type="multiple_choice",
                options=[
                    "Keynote sessions",
                    "Breakout workshops",
                    "Networking",
                    "Panel discussions",
                    "Exhibitor booths",
                ],
                required=False,
                category="content",
            ),
            SurveyQuestion(
                question_id="improvement",
                question_text="What could we improve for next time?",
                question_type="open_ended",
                required=False,
                category="overall",
            ),
            SurveyQuestion(
                question_id="future_topics",
                question_text="What topics would you like to see at future events?",
                question_type="open_ended",
                required=False,
                category="content",
            ),
            SurveyQuestion(
                question_id="contact_permission",
                question_text="May we contact you about future events and relevant content?",
                question_type="multiple_choice",
                options=["Yes, email me", "Yes, call me", "No, thank you"],
                required=True,
                category="general",
            ),
        ]

    def _create_email_sequence(self, data: FollowUpInput) -> list[FollowUpEmail]:
        """Create a post-event email sequence."""
        return [
            FollowUpEmail(
                email_id="thank_you",
                subject=f"Thank you for attending {data.event_name}!",
                body_template=(
                    f"Dear Attendee,\n\nThank you for being part of {data.event_name}! "
                    f"We hope you had a valuable experience. Please take a moment to "
                    f"share your feedback with us.\n\nBest regards,\nThe Event Team"
                ),
                timing="T+1 day",
                audience="all_attendees",
                goal="Express gratitude and drive survey completion",
                cta="Take the 2-minute survey",
            ),
            FollowUpEmail(
                email_id="recap",
                subject=f"{data.event_name} Event Recap & Resources",
                body_template=(
                    f"Dear Attendee,\n\nMissed a session or want to revisit the content? "
                    f"Check out the event recap, presentation recordings, and resources "
                    f"from {data.event_name}.\n\nBest regards,\nThe Event Team"
                ),
                timing="T+3 days",
                audience="all_attendees",
                goal="Provide value through content and maintain engagement",
                cta="Access event resources",
            ),
            FollowUpEmail(
                email_id="speaker_thanks",
                subject="Thank you for speaking at our event",
                body_template=(
                    f"Dear Speaker,\n\nThank you for your outstanding contribution to "
                    f"{data.event_name}. Your session was highly rated by attendees. "
                    f"We'd love to stay in touch for future events.\n\nBest regards,\n"
                    "The Event Team"
                ),
                timing="T+1 day",
                audience="speakers",
                goal="Thank speakers and maintain relationships",
                cta="Share your session feedback",
            ),
            FollowUpEmail(
                email_id="sponsor_recap",
                subject=f"{data.event_name} Sponsor Impact Report",
                body_template=(
                    f"Dear Sponsor,\n\nThank you for sponsoring {data.event_name}. "
                    f"Here's your impact report with leads generated, brand impressions, "
                    f"and attendee engagement data.\n\nBest regards,\nThe Event Team"
                ),
                timing="T+7 days",
                audience="sponsors",
                goal="Demonstrate ROI and secure future sponsorships",
                cta="Schedule a debrief call",
            ),
            FollowUpEmail(
                email_id="save_date",
                subject="Save the Date: Next Event Announcement",
                body_template=(
                    "Dear Attendee,\n\nBased on your feedback, we're already planning "
                    "our next event. Save the date and be the first to know when "
                    "registration opens.\n\nBest regards,\nThe Event Team"
                ),
                timing="T+14 days",
                audience="all_attendees",
                goal="Build anticipation for future events",
                cta="Save the date",
            ),
        ]

    def _create_lead_nurture_plan(self, data: FollowUpInput) -> list[LeadNurtureAction]:
        """Create a lead nurturing plan."""
        return [
            LeadNurtureAction(
                action_type="email",
                description="Send personalized follow-up based on sessions attended",
                target_segment="high_engagement_leads",
                timing="T+3 days",
                priority="high",
            ),
            LeadNurtureAction(
                action_type="content_download",
                description="Share relevant whitepaper or resource related to event topics",
                target_segment="all_leads",
                timing="T+5 days",
                priority="medium",
            ),
            LeadNurtureAction(
                action_type="meeting",
                description="Schedule demo or consultation call",
                target_segment="qualified_leads",
                timing="T+7 days",
                priority="high",
            ),
            LeadNurtureAction(
                action_type="email",
                description="Invite to exclusive webinar or community event",
                target_segment="nurture_leads",
                timing="T+14 days",
                priority="medium",
            ),
            LeadNurtureAction(
                action_type="call",
                description="Personal outreach to top prospects",
                target_segment="hot_leads",
                timing="T+10 days",
                priority="high",
            ),
        ]

    def _recommend_content(self, data: FollowUpInput) -> list[str]:
        """Recommend content for post-event engagement."""
        return [
            "Blog post: Key takeaways from the event",
            "Video highlights reel of the best moments",
            "Infographic: Event statistics and outcomes",
            "Speaker interview series",
            "Presentation slide decks (with permission)",
            "Photo gallery from the event",
            "LinkedIn article summarizing event insights",
        ]

    def _create_follow_up_timeline(self, data: FollowUpInput) -> list[dict[str, Any]]:
        """Create a follow-up timeline."""
        return [
            {
                "timing": "T+0",
                "action": "Send thank-you emails to all attendees",
                "owner": "Marketing"
            },
            {"timing": "T+1", "action": "Launch post-event survey", "owner": "Marketing"},
            {"timing": "T+3", "action": "Send event recap and resources", "owner": "Content"},
            {"timing": "T+5", "action": "Begin lead nurturing sequence", "owner": "Sales"},
            {"timing": "T+7", "action": "Send sponsor impact reports", "owner": "Sponsorship"},
            {"timing": "T+10", "action": "Personal outreach to hot leads", "owner": "Sales"},
            {"timing": "T+14", "action": "Save the date for next event", "owner": "Marketing"},
            {
                "timing": "T+30",
                "action": "Analyze follow-up metrics and report",
                "owner": "Analytics"
            },
        ]

    def _define_success_metrics(self, data: FollowUpInput) -> dict[str, float]:
        """Define success metrics for follow-up activities."""
        return {
            "survey_response_rate_target": 0.30,
            "email_open_rate_target": 0.35,
            "email_click_rate_target": 0.08,
            "lead_conversion_rate_target": 0.15,
            "sponsor_satisfaction_target": 0.85,
            "attendee_retention_rate_target": 0.60,
        }
