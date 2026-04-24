import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from backend.app.enums.enums import AdminDetails
from backend.app.schemas.schemas import MailHandlerRequest, MailHandlerResponse
from backend.app.services.base_mail import SentMail


class GmailMailSent(SentMail):

    def __init__(self, user_name, user_email):
        self.user_name = user_name
        self.user_email = user_email


    def sent_mail(self, data: MailHandlerRequest):
        print(f"Sending Message {data.message} to user {data.receiver_email_address}")
        ## Logic to sent
        try:
            ## Code
            msg = self.create_message(data)
            server = self.setup_smtp_server()

            # sending mail
            server.sendmail(self.user_email, data.receiver_email_address, msg.as_string())
            server.quit()

            print("Email sent successfully")
            return MailHandlerResponse(
                success=True,
                code=200,
                status="Success"
            )
        except Exception as err:
            print(f"Failed to sent message")
            return MailHandlerResponse(
                success=False,
                code=200,
                status="Failed",
                error_message=str(err)
            )

    def create_message(self, data):
        msg = MIMEMultipart()
        msg["From"] = self.user_email
        msg["To"] = data.receiver_email_address
        msg["Subject"] = "subject"

        msg.attach(MIMEText(data.message, "plain"))
        return msg

    def setup_smtp_server(self):
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(self.user_email, AdminDetails.SECRET_KEY.value)
        return server
