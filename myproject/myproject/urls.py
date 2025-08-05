"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from myapp import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.folder_view, name='folder_view'),
    path('create-folder/', views.create_folder, name='create_folder'),
    path('delete-folder/<int:folder_id>/', views.delete_folder, name='delete_folder'),
    path('rename-folder/<int:folder_id>/', views.rename_folder, name='rename_folder'),
    path('copy-folder/<int:folder_id>/', views.copy_folder, name='copy_folder'),
    path('cut-folder/<int:folder_id>/', views.cut_folder, name='cut_folder'),
    path('paste-folder/<int:target_folder_id>/', views.paste_folder, name='paste_folder'),
    path('folder/<int:folder_id>/delete/', views.delete_folder, name='delete_folder'),
    path('folder/<int:folder_id>/', views.folder_detail, name='folder_detail'),
    path('folder/<int:folder_id>/new/', views.folder_detail, name='create_item'),
    path('folder/<int:folder_id>/upload/', views.upload_file, name='upload_file'),
    path('folder_detailed/<int:folder_id>/', views.folder_detailed, name='folder_detailed'),
    path('file/<int:file_id>/download/', views.download_file, name='download_file'),

    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('register/', views.register, name='register'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('folder/<int:folder_id>/delete_item/', views.delete_item, name='delete_item'),


    # path('folder/<int:folder_id>/cut/', views.cutted_folder, name='cut_folder'),
    # path('folder/<int:folder_id>/copy/', views.copied_folder, name='copy_folder'),
    # path('folder/<int:folder_id>/paste/', views.pasted_folder, name='pasted_folder'),
    # path('folder/<int:folder_id>/delete/', views.deleted_folder, name='delete_folder'),
    # path('folder/<int:folder_id>/rename/', views.renamed_folder, name='rename_folder'),
    # path('folder/<int:folder_id>/new/', views.new_folder, name='new_folder'),
    # path('folder/<int:folder_id>/new/', views.create_new_folder, name='create_new_folder'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
