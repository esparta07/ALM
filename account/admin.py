from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User,ProvinceAdmin,Action

class CustomUserAdmin(UserAdmin):
    list_display = ('full_name','phone_number','email','role', 'is_active',)
    ordering = ('-date_joined',)
    filter_horizontal = ()
    list_filter = ()
    fieldsets = (
        (None, {'fields': ('phone_number','email','full_name','is_active', 'role',)}),
        ('Permissions', {'fields': ('is_admin', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
    (None, {
        'classes': ('wide',),
        'fields': ('phone_number', 'role', 'password1', 'password2'),
    }),
    )


admin.site.register(ProvinceAdmin)
admin.site.register(Action)
admin.site.register(User, CustomUserAdmin)