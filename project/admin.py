from import_export import resources, fields , widgets
from django.contrib import admin
from .models import Province, District, Municipality, Company, Officer, Newspaper,Category,SubCategory,Advs,PhoneNumber
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget

class PhoneResource(resources.ModelResource):
    class Meta:
        model = PhoneNumber
        
class ProvinceResource(resources.ModelResource):
    class Meta:
        model = Province
        fields = ('id', 'name')  # Add the fields you want to include in the search

class DistrictResource(resources.ModelResource):
    class Meta:
        model = District
        fields = ('id', 'name', 'province__name')  # Add the fields you want to include in the search

class MunicipalityResource(resources.ModelResource):
    class Meta:
        model = Municipality
        fields = ('id', 'name', 'district__name', 'district__province__name')  # Add the fields you want to include in the search

class CompanyResource(resources.ModelResource):
    class Meta:
        model = Company
        fields = ('id', 'name', 'category__name', 'sub_category__name', 'province__name', 'district__name', 'municipality__name', 'website', 'address')

class OfficerResource(resources.ModelResource):
    class Meta:
        model = Officer
         

class NewspaperResource(resources.ModelResource):
    class Meta:
        model = Newspaper

class CategoryResource(resources.ModelResource):
    class Meta:
        model = Category

class SubCategoryResource(resources.ModelResource):
    class Meta:
        model = SubCategory

class AdvsResource(resources.ModelResource):
    class Meta:
        model = Advs
        
@admin.register(Province)
class ProvinceAdmin(ImportExportModelAdmin):
    resource_class = ProvinceResource
    search_fields = ['name'] 

@admin.register(District)
class DistrictAdmin(ImportExportModelAdmin):
    resource_class = DistrictResource
    search_fields = ['name', 'province__name']  

@admin.register(Municipality)
class MunicipalityAdmin(ImportExportModelAdmin):
    resource_class = MunicipalityResource
    search_fields = ['name', 'district__name', 'district__province__name']  

@admin.register(Company)
class CompanyAdmin(ImportExportModelAdmin):
    resource_class = CompanyResource
    search_fields = ['name', 'category__name', 'sub_category__name', 'province__name', 'district__name', 'municipality__name', 'website', 'address']  

@admin.register(Officer)
class OfficerAdmin(ImportExportModelAdmin):
    resource_class = OfficerResource
    search_fields = ['name']

@admin.register(Newspaper)
class NewspaperAdmin(ImportExportModelAdmin):
    resource_class = NewspaperResource

@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    resource_class = CategoryResource
    
@admin.register(SubCategory)
class SubCategoryAdmin(ImportExportModelAdmin):
    resource_class = SubCategoryResource
    
@admin.register(Advs)
class AdvsAdmin(ImportExportModelAdmin):
    resource_class = AdvsResource
    
@admin.register(PhoneNumber)
class PhoneAdmin(ImportExportModelAdmin):
    resource_class = PhoneResource