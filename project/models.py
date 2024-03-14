from django.db import models
from django.db.models import Count


class Province(models.Model):
    name = models.CharField(max_length=100 )

    def __str__(self):
        return self.name

class District(models.Model):
    name = models.CharField(max_length=100)
    province = models.ForeignKey(Province, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name}"

class Municipality(models.Model):
    name = models.CharField(max_length=100)
    district = models.ForeignKey(District, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name}"

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Company(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    sub_category = models.ForeignKey(SubCategory, on_delete=models.CASCADE)
    province = models.ForeignKey(Province, on_delete=models.CASCADE)
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE)
    website = models.URLField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    @classmethod
    def remove_duplicates(cls):
        # Get all fields excluding the primary key
        fields = [field.name for field in cls._meta.get_fields() if field.name != 'id']
        # Identify duplicate records
        duplicates = cls.objects.values(*fields).annotate(Count('id')).filter(id__count__gt=1)
        # Loop through duplicate records and delete all but one instance
        for duplicate in duplicates:
            company_instances = cls.objects.filter(**duplicate)
            first_instance = company_instances.first()
            company_instances.exclude(pk=first_instance.pk).delete()

class Officer(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='officers')
    designation = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    office = models.CharField(max_length=100)
    email = models.EmailField()
    is_active=models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name}, {self.designation}"
    
class PhoneNumber(models.Model):
    officer = models.ForeignKey(Officer, on_delete=models.CASCADE, related_name='phone_numbers')
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.officer.name

class Newspaper(models.Model):
    name = models.CharField(max_length=100)
    TYPE_CHOICES = (
        ('National', 'National'),
        ('Provincial', 'Provincial'),
        ('Local', 'Local'),
    )
    type = models.CharField(max_length=100, choices=TYPE_CHOICES)
    
    LEVEL_CHOICES =(
        ('A','A'),
        ('B','B'),
        ('C','C')
    ) 
    level = models.CharField(max_length=100, choices=LEVEL_CHOICES)
    front_bw = models.FloatField(default=0.0)
    front_color = models.FloatField(default=0.0)
    inside_bw = models.FloatField(default=0.0)
    inside_color = models.FloatField(default=0.0)
    back_bw = models.FloatField(default=0.0)
    back_color = models.FloatField(default=0.0)
    
    def __str__(self):
        return self.name
    
class Advs(models.Model):
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    newspaper = models.ForeignKey('Newspaper', on_delete=models.CASCADE)
    publish_date = models.DateField()
    size = models.FloatField()
    caption = models.CharField(max_length=255)  
    adv_type = models.CharField(max_length=255) 
    balance = models.FloatField(default=False , null=True)
    
    def __str__(self):
        return f"{self.company} - {self.newspaper} - {self.publish_date}"








    

