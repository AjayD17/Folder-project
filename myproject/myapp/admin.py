from django.contrib import admin
from .models import Folder, File, UserProfile

admin.site.register(UserProfile)

# admin.py
from django.contrib import admin
from .models import Folder, File

@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'parent')
    readonly_fields = ('owner',)

    def has_change_permission(self, request, obj=None):
        # Only superusers can edit
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete
        return request.user.is_superuser

    def has_add_permission(self, request):
        # Both superusers and normal users can add
        return True

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('name', 'folder')
