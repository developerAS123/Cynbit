import logging

logger = logging.getLogger("cynbit.notification")

class NotificationService:
    """
    Simulates / integrates email dispatch via transactional providers (e.g. Resend, AWS SES).
    Decoupled from request-response cycles to avoid blocking HTTP workers.
    """
    @staticmethod
    async def send_onboarding_magic_link(email: str, candidate_name: str, magic_token: str):
        """
        Dispatches a secure, single-use, time-limited magic onboarding link to the candidate.
        CRITICAL: Never dispatches or returns plaintext passwords!
        """
        onboarding_url = f"https://bitelevate.cynbit.in/onboard?token={magic_token}"
        logger.info(
            f"EMAIL_DISPATCH: [Account Onboarding] To={email} Candidate={candidate_name} "
            f"Link={onboarding_url} (Expires in 24 hours)"
        )
        return True

    @staticmethod
    async def send_application_receipt(email: str, candidate_name: str, job_id: str):
        """Dispatches generic application submission confirmation."""
        logger.info(
            f"EMAIL_DISPATCH: [Application Received] To={email} Candidate={candidate_name} Job={job_id}"
        )
        return True

    @staticmethod
    async def send_password_reset_link(email: str, reset_token: str):
        """Dispatches password recovery link."""
        reset_url = f"https://bitelevate.cynbit.in/reset-password?token={reset_token}"
        logger.info(f"EMAIL_DISPATCH: [Password Reset] To={email} Link={reset_url}")
        return True

