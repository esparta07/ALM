from celery import shared_task
from django.core.mail import EmailMessage
from django.db.models import Count, Sum
from django.urls import reverse
from .models import Advs
from account.models import ProvinceAdmin
from django.contrib.auth import get_user_model
from django.conf import settings
import logging
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from datetime import datetime
import subprocess
import os
from datetime import datetime, timedelta
from datetime import datetime



logger = logging.getLogger(__name__)
User = get_user_model()



@shared_task(bind=True)
def generate_and_send_html_tables(self):
    today = datetime.now()
    try:
        # Get all objects of Advs
        advs_data = Advs.objects.values(
            'company__id',
            'company__name',
            'company__province__name',
        ).annotate(
            publish_frequency=Count('company'),
            budget_spent=Sum('balance'),
            size=Sum('size')
        ).filter(publish_date=today)

        # Create a dictionary of DataFrames for each province
        province_tables = {}
        for row in advs_data:
            company_link = reverse('company_profile', kwargs={'company_id': row['company__id']})
            company_link = f"{settings.BASE_URL}{company_link}"
            province_name = row['company__province__name']

            # Append the row with the link to province_tables
            if province_name not in province_tables:
                province_tables[province_name] = []

            row_with_link = {'company_link': company_link, **row}
            province_tables[province_name].append(row_with_link)

        # Fetch admin province objects
        admin_provinces = ProvinceAdmin.objects.all()

        # Create a dictionary to store combined tables for each admin
        combined_tables_dict = {}

        # Combine tables for each admin
        for admin_province in admin_provinces:
            province_name = admin_province.province.name
            admins = admin_province.admin.all()  # Fetch all admin users associated with this province
            for admin in admins:
                admin_email = admin.email
                if admin_email not in combined_tables_dict:
                    combined_tables_dict[admin_email] = []
                if province_name in province_tables:
                    combined_tables_dict[admin_email].extend(province_tables[province_name])

        # Create a list to store the context for each admin
        email_contexts = []

        # Iterate over each admin and their associated tables
        for admin_email, combined_tables in combined_tables_dict.items():
            # Prepare the data for rendering in the template
            context = {
                'all_tables': [{'province_name': '', 'table_data': combined_tables}],
            }
            email_contexts.append((admin_email, context))

        # Render the HTML content using a template for each admin
        for admin_email, context in email_contexts:
            html_content = render_to_string('emails/admin_template.html', context)
            
            # Email content
            subject = 'Combined Daily Digest'
            message = 'Here is the combined daily digest.'

            # Create an EmailMultiAlternatives object
            from_email = settings.DEFAULT_FROM_EMAIL
            email = EmailMultiAlternatives(subject, message, from_email, [admin_email])
            
            # Attach the HTML content
            email.attach_alternative(html_content, "text/html")
            
            # Send the email
            email.send()

    except Exception as e:
        logger.error(f"Error in generate_and_send_html_tables: {e}")
        raise


@shared_task(bind=True)
def generate_and_send_compiled_excel(self):
    today = datetime.now()
    try:
        # Get all objects of Advs
        advs_data = Advs.objects.values(
            'company__id',
            'company__name',
            'company__province__name',
        ).annotate(
            publish_frequency=Count('company'),
            budget_spent=Sum('balance'),
            size=Sum('size')
        ).filter(publish_date = today)

        # Create a list of dictionaries containing the data
        table_content = []
        for row in advs_data:
            company_link = reverse('company_profile', kwargs={'company_id': row['company__id']})
            # Adjust the URL to match 
            company_link = f"{settings.BASE_URL}{company_link.replace('/lead/company/', '/lead/company/')}"
            table_content.append({
                'customer_name': row['company__name'],
                'customer_link': company_link,
                'province': row['company__province__name'],
                'publish_frequency': row['publish_frequency'],
                'budget_spent': row['budget_spent'],
                'size': row['size'],
            })

        # Email content
        subject = 'Daily Digest - All Provinces'
        message = render_to_string('emails/email_template.html', {
            'table_content': table_content
        })

        # Send the email
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = ['amail2manoj@gmail.com', 'advertisingjpmail@gmail.com']
        email = EmailMessage(subject, message, from_email, to_email)
        email.content_subtype = 'html'
        email.send()
        
        return "Email sent successfully"

    except Exception as e:
        logger.error(f"Error in generate_and_send_compiled_excel: {e}", exc_info=True)
        return f"Error: {e}"


@shared_task(bind=True)
def backup_postgres(self):
    # Get database configuration from environment variables
    db_name = os.environ.get('DB_NAME')
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')
    db_host = os.environ.get('DB_HOST')
    sender_email = os.environ.get('SENDER_EMAIL')
    receiver_email = 'amail2manoj@gmail.com'

    # Construct the backup file name with the current date
    backup_filename = datetime.now().strftime('%Y%m%d') + '-backup.sql'

    # Construct the pg_dump command
    pg_dump_cmd = [
        'pg_dump',
        '-U', db_user,
        '-d', db_name,
        '-h', db_host,
        '-p', '5432',  # Assuming default PostgreSQL port
        '-w',  # Suppress password prompts
    ]

    try:
        # Set the PGPASSWORD environment variable to pass the password
        os.environ['PGPASSWORD'] = db_password
        
        # Execute the pg_dump command and capture the output
        backup_output = subprocess.check_output(pg_dump_cmd)
        print("Backup successful")

        # Send email with backup content as attachment
        send_email(sender_email, receiver_email, backup_output, backup_filename)

    except subprocess.CalledProcessError as e:
        print(f"Backup failed: {e}")

def send_email(sender_email, receiver_email, backup_content, backup_filename):
    # Create email message
    subject = "Database Backup"
    current_date = datetime.now().strftime('%Y-%m-%d')
    body = f"Please find attached the latest database backup on Date: {current_date}"
    email = EmailMessage(subject, body, sender_email, [receiver_email])

    # Attach backup content as attachment
    email.attach(backup_filename, backup_content, "application/octet-stream")

    # Set email configuration from Django settings
    email.host = settings.EMAIL_HOST
    email.port = settings.EMAIL_PORT
    email.username = settings.EMAIL_HOST_USER
    email.password = settings.EMAIL_HOST_PASSWORD

    # Send email
    email.send()


