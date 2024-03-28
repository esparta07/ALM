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
        ).filter(publish_date = today)

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

        # Combine all tables in one list
        all_tables = []
        all_emails = []
        for admin_province in admin_provinces:
            province_name = admin_province.province.name

            if province_name in province_tables:
                # Extract the corresponding table for the admin province
                province_table = province_tables[province_name]

                # Log the content of the first row of the table
                logger.info(f"Province Table for {province_name}: {province_table[0]}")

                # Retrieve an actual admin instance from the manager
                admin_instance = admin_province.admin.first()

                if admin_instance:
                    admin_email = admin_instance.email if hasattr(admin_instance, 'email') else None

                    if admin_email:
                        all_tables.append({'province_name': province_name, 'table_data': province_table, 'admin_email': admin_email})

        if all_tables:
            # Prepare the data for rendering in the template
            context = {
                'all_tables': all_tables,
            }

            # Render the HTML content using a template
            html_content = render_to_string('emails/admin_template.html', context)

            # Email content
            subject = 'Combined Daily Digest'
            message = 'Here is the combined daily digest.'

            # Create an EmailMultiAlternatives object
            from_email = settings.DEFAULT_FROM_EMAIL
            for table in all_tables:
                admin_email = table['admin_email']
                email = EmailMultiAlternatives(subject, message, from_email, [admin_email])
                
                # Attach the HTML content
                email.attach_alternative(html_content, "text/html")
                
                # Send the email
                email.send()

    except Exception as e:
        logger.error(f"Error in generate_and_send_combined_html_tables: {e}")
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

