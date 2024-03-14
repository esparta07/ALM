from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from .models import Advs,Newspaper,Province,District,Municipality,Company,Officer,PhoneNumber,Category,SubCategory
from account.models import ProvinceAdmin,Action
from .forms import NewspaperForm,CompanyForm,PaperForm,ActionForm,OfficerForm,BulkUploadForm
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from .filters import CompanyFilter
from django.http import JsonResponse,HttpResponse
from datetime import date
from account.utils import check_role_admin, check_role_user
from django.contrib.auth.decorators import login_required, user_passes_test
import pandas as pd

def calculate_adv_spend(company_id):
    # Filter Advs by the given company_id and annotate with the spend of type * size
    queryset = Advs.objects.filter(company_id=company_id).annotate(
        spend=Coalesce(F('adv_type') * F('size'), 1.0)
    )

    # Aggregate the spends to get the total spend
    total_spend = queryset.aggregate(total_spend=Sum('spend'))['total_spend']

    return total_spend

@login_required(login_url='login')
def add_lead(request):
    if request.method == 'POST':
        company_id = request.POST.get('company')
        newspaper_id = request.POST.get('newspaper')
        publish_date = request.POST.get('publish_date')
        caption = request.POST.get('caption')
        size = request.POST.get('size')
        page=request.POST.get('page')
        color_bw=request.POST.get('color_bw')
        
        
        selected_newspaper = Newspaper.objects.get(pk=newspaper_id)
        if page == 'front':
            front_value = selected_newspaper.front_bw if color_bw == 'bw' else selected_newspaper.front_color
            sum_amount=front_value

        elif page == 'inside':
            inside_value = selected_newspaper.inside_bw if color_bw == 'bw' else selected_newspaper.inside_color
            sum_amount=inside_value
            
        elif page == 'back':
            back_value = selected_newspaper.back_bw if color_bw == 'bw' else selected_newspaper.back_color
            sum_amount=back_value
                    
        balance = sum_amount * float(size)
        adv_type= page+color_bw
        
        # Create Advs instance and save to the database
        advs = Advs.objects.create(
            company_id=company_id,
            newspaper_id=newspaper_id,
            publish_date=publish_date,
            caption=caption,
            size=float(size),
            adv_type=adv_type,
            balance=balance
        )
        

        return redirect('add_lead')  

    # Render the form page with an instance of the NewspaperForm
    context = {
        'form': NewspaperForm(),
    }
    return render(request, 'add_lead.html', context)

@login_required(login_url='login')
def add_company(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        officer_form = OfficerForm(request.POST)
        bulkupload_form =BulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the form data if it's valid
            form.save()
            messages.success(request, 'Company was added Succesfully')
            
            return redirect('add_company')
    else:
        # If the request method is not POST, create an instance of the form
        form = CompanyForm()
        officer_form = OfficerForm()
        bulkupload_form =BulkUploadForm()
        
    context = {
        'form': form,
        'officer_form': officer_form,
        'bulkupload_form':bulkupload_form,
    }
    return render(request, 'add_company.html', context)

@login_required(login_url='login')
def add_newspaper(request):
    if request.method == 'POST':
        form = PaperForm(request.POST)
        if form.is_valid():
            # Save the form data if it's valid
            form.save()
            
            
            return redirect('add_newspaper')
    else:
        # If the request method is not POST, create an instance of the form
        form = PaperForm()

    context = {
        'form': form,
    }
    return render(request, 'add_newspaper.html', context)

@login_required(login_url='login')
@user_passes_test(check_role_admin)
def company(request):
    admin = request.user

    try:
        # Fetch all ProvinceAdmin objects related to the admin
        province_admins = ProvinceAdmin.objects.filter(admin=admin)

        # Extract provinces from ProvinceAdmin objects
        provinces = [province_admin.province for province_admin in province_admins]

        # Fetch all companies
        all_companies = Company.objects.all()

        # Filter all companies based on the list of provinces
        company_filter = CompanyFilter(request.GET, queryset=all_companies)
        all_companies_filtered = company_filter.qs

        # Fetch my companies and apply the same filters
        mycompany = Company.objects.filter(province__in=provinces)
        mycompany_filter = CompanyFilter(request.GET, queryset=mycompany)
        mycompany_filtered = mycompany_filter.qs

    except ProvinceAdmin.DoesNotExist:
        # Handle the case where ProvinceAdmin does not exist for the admin
        all_companies_filtered = Company.objects.none()
        mycompany_filtered = Company.objects.none()

    context = {
        'company': all_companies_filtered,
        'mycompany': mycompany_filtered,
        'filter': company_filter,
    }

    return render(request, 'company_list.html', context)

@login_required(login_url='login')
@user_passes_test(check_role_admin)
def company_profile(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    advs = Advs.objects.filter(company=company).order_by('-publish_date')
    total_spend = int(advs.aggregate(total_balance=Sum('balance'))['total_balance'] or 0)
    officers = Officer.objects.filter(company=company)
    actions = Action.objects.filter(company=company).order_by('-date')
    phone_numbers = PhoneNumber.objects.filter(officer__in=officers)
    user = request.user
    today = date.today()

    if request.method == 'POST':
        form = ActionForm(company, request.POST)
        officer_form = OfficerForm(request.POST, initial={'company': company})  # Initialize officer_form with POST data
            
        if form.is_valid() :
            action = form.save(commit=False)
            action.company = company
            action.date = today
            action.admin = user
            form.save()

            

            return redirect('company_profile', company_id=company.id)
    else:
        form = ActionForm(company)
        officer_form = OfficerForm(initial={'company': company})  # Initialize officer_form with default values

    context = {
        'company': company,
        'officers': officers,
        'actions': actions,
        'form': form,
        'officer_form': officer_form,
        'advs':advs,
        'total_spend': total_spend,
        'phone_numbers':phone_numbers
    }
    return render(request, 'company_profile.html', context)

def get_districts(request):
    province_id = request.GET.get('province_id')
    districts = District.objects.filter(province_id=province_id).order_by('name')
    options = '<option value="">Select District</option>'
    
    for district in districts:
        options += f'<option value="{district.id}">{district.name}</option>'
    
    return HttpResponse(options)

# views.py
def get_municipalities(request):
    district_id = request.GET.get('district_id')
    municipalities = Municipality.objects.filter(district_id=district_id).order_by('name')
    options = '<option value=""> Select Municiplaity</option>'

    for municipality in municipalities:
        options += f'<option value="{municipality.id}">{municipality.name}</option>'

    return HttpResponse(options)

@login_required(login_url='login')
def profile(request):
    
    return render(request , 'profile.html')

@login_required(login_url='login')
@user_passes_test(check_role_admin)
def submit_officer_form(request):
    if request.method == 'POST':
        form = OfficerForm(request.POST)

        if form.is_valid():
            officer = form.save()

            # Process additional phone numbers
            additional_phones = request.POST.get('additional_phones', '')
            additional_phone_list = additional_phones.split(',')

            # Save additional phone numbers to PhoneNumber model
            for additional_phone in additional_phone_list:
                PhoneNumber.objects.create(officer=officer, phone=additional_phone.strip())
            
            return JsonResponse({'status': 'success', 'message': 'Officer was added successfully'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors.as_json()}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

def bulk_upload(request):
    if request.method == 'POST':
        form = BulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            if not uploaded_file.name.endswith('.xlsx'):
                messages.error(request, "Invalid file format. Please upload a .xlsx file.")
                return redirect('add_company')

            try:
                excel_data = pd.read_excel(uploaded_file)

                company_count = 0
                officer_count = 0
                error_list = []

                for index, row in excel_data.iterrows():
                    try:
                        province_name = row['Province']
                        district_name = row['District']
                        municipality_name = row['Municipality']

                        try:
                            # Get existing Province
                            province = Province.objects.get(name__iexact=province_name)
                        except Province.DoesNotExist:
                            # Create new Province if it doesn't exist
                            province = Province.objects.create(name=province_name)

                        try:
                            # Get existing District within the Province
                            district = District.objects.get(name__iexact=district_name, province=province)
                        except District.DoesNotExist:
                            # Create new District if it doesn't exist
                            district = District.objects.create(name=district_name, province=province)

                        try:
                            # Get existing Municipality within the District
                            municipality = Municipality.objects.get(name__iexact=municipality_name, district=district)
                        except Municipality.DoesNotExist:
                            # Create new Municipality if it doesn't exist
                            municipality = Municipality.objects.create(name=municipality_name, district=district)

                        # Get Category and SubCategory (case-insensitive)
                        category = Category.objects.get(name__iexact=row['Category'])
                        sub_category = SubCategory.objects.get(name__iexact=row['Sub Category'])

                        # Create Company instance with foreign key relations
                        company = Company.objects.create(
                            name=row['Company'],
                            category=category,
                            sub_category=sub_category,
                            province=province,
                            district=district,
                            municipality=municipality,
                            website=row['Website'],
                            address=row['Address'],
                        )
                        company_count += 1

                        # Create Officer instances
                        for i in range(1, 5):
                            officer_name = row[f'Officer{i} Name']
                            if officer_name:
                                officer = Officer.objects.create(
                                    company=company,
                                    designation=row[f'Officer{i} Designation'],
                                    name=officer_name,
                                    office=row[f'Officer{i} Office'],
                                    email=row[f'Officer{i} Email'],
                                    is_active=True,  # You may want to change this based on your logic
                                )

                                # Create PhoneNumber instance if phone number exists
                                phone_number = row[f'Officer{i} Phone']
                                if phone_number:
                                    PhoneNumber.objects.create(officer=officer, phone=phone_number)
                                officer_count += 1

                    except Province.DoesNotExist:
                        error_message = f"Error processing row {index + 2}: Province '{row['Province']}' not found."
                        error_list.append(error_message)
                        print(error_message)
                        continue  # Continue to the next iteration

                    except District.DoesNotExist:
                        error_message = f"Error processing row {index + 2}: District '{row['District']}' not found in {row['Province']}."
                        error_list.append(error_message)
                        print(error_message)
                        continue  # Continue to the next iteration

                    except Municipality.DoesNotExist:
                        error_message = f"Error processing row {index + 2}: Municipality '{row['Municipality']}' not found in {row['District']}, {row['Province']}."
                        error_list.append(error_message)
                        print(error_message)
                        continue  # Continue to the next iteration

                    except (Category.DoesNotExist, SubCategory.DoesNotExist) as e:
                        error_message = f"Error processing row {index + 2}: {e}"
                        error_list.append(error_message)
                        print(error_message)
                        continue  # Continue to the next iteration

                messages.success(request, f"Bulk upload successful. {company_count} companies and {officer_count} officers added.")
                if error_list:
                    messages.warning(request, "Some rows encountered errors. Check the error list.")
                    print("Error List:", error_list)  # Print the list of errors in the terminal

                return redirect('add_company')

            except Exception as e:
                messages.error(request, f"Error processing the file: {e}")
                return redirect('add_company')

    # Handle GET request or invalid form
    return redirect('add_company')


from django.http import JsonResponse
from project.models import Company
from django.db.models import Count



def remove_duplicates(request):
    if request.method == 'GET':
        try:
            # Get a list of all duplicate records based on all field values
            duplicate_records = Company.objects.values('name', 'category', 'sub_category', 'province', 'district', 'municipality', 'website', 'address').annotate(record_count=Count('id')).filter(record_count__gt=1)

            # Iterate through the duplicate records and keep one record, delete the rest
            for record in duplicate_records:
                # Get all duplicate records
                duplicates = Company.objects.filter(name=record['name'], category=record['category'], sub_category=record['sub_category'], province=record['province'], district=record['district'], municipality=record['municipality'], website=record['website'], address=record['address'])
                
                # Keep the first record and delete the rest
                for duplicate in duplicates[1:]:
                    duplicate.delete()
            
            return JsonResponse({'status': 'success', 'message': 'Duplicate records removed successfully.'})
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method. Only GET requests are allowed.'})

# from project.tasks import generate_and_send_html_tables
# def test_email_view(request):
#     try:
#         # Call the Celery task
#         generate_and_send_html_tables.delay()

#         # You can customize the response message if needed
#         return HttpResponse("Email task is being processed. Check your email.")

#     except Exception as e:
#         # Handle exceptions appropriately
#         return HttpResponse(f"Error: {e}")













