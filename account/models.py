from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from project.models import Province
from django.contrib.auth import get_user_model
from django.db.models import Q

# Create your models here.

class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, role=None):
        if not phone_number:
            raise ValueError('The Phone Number field must be set')

        user = self.model(phone_number=phone_number, role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user


    def create_superuser(self, phone_number, password=None):
        # Create and save a new superuser with the given phone number and password
        user = self.create_user(phone_number, password)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
    
class User(AbstractBaseUser):
    ADMIN = 1
    AGENT = 2
    SUPERADMIN = 3

    ROLE_CHOICES = (
        (ADMIN, 'ADMIN'),
        (AGENT, 'AGENT'),
        (SUPERADMIN,'SUPERADMIN')
    )
    phone_number = models.CharField(max_length=50,unique=True)
    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICES, blank=True, null=True)
    full_name = models.CharField(max_length=50,blank=True)
    email = models.EmailField(max_length=100, unique=False, default="")
    
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)
    date_joined = models.DateTimeField(auto_now=True)
    
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "phone_number"
    objects = UserManager()

    def __str__(self):
        return str(self.full_name)

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    def get_role(self):
        if self.role == 1:
            user_role = 'ADMIN'
        elif self.role == 2:
            user_role = 'AGENT'
        elif self.role == 3:
            user_role = 'SUPERADMIN'
        return user_role
    

User = get_user_model()

class ProvinceAdmin(models.Model):
    admin = models.ManyToManyField(User, limit_choices_to=Q(role=User.ADMIN) | Q(role=User.SUPERADMIN))
    province = models.ForeignKey(Province, on_delete=models.CASCADE)

    def __str__(self):
        return f" {self.province}"




class Action(models.Model):
    company = models.ForeignKey('project.Company', on_delete=models.CASCADE)
    officer = models.ForeignKey('project.Officer', on_delete=models.CASCADE)
    date = models.DateField()
    description = models.TextField()
    admin = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': User.ADMIN}, verbose_name='Admin User')

    def __str__(self):
        return f"{self.date} - {self.company} - {self.officer} - {self.admin}"

    class Meta:
        verbose_name_plural = 'Actions'
