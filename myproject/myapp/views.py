import os
import json
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Folder, File, UserProfile  # Adjust this to your app's models
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test

@login_required(login_url='login')
def folder_view(request):
    if request.user.is_superuser:
        # Admin can see all folders
        top_level_folders = Folder.objects.filter(parent__isnull=True)
    else:
        # Normal users see only their folders
        top_level_folders = Folder.objects.filter(parent__isnull=True, owner=request.user)

    folders_with_files = [{'folder': folder} for folder in top_level_folders]
    return render(request, 'folder.html', {
        'folders_with_files': folders_with_files,
        'folders': top_level_folders
    })

@login_required
def create_folder(request):
    if request.method == 'POST':
        name = request.POST.get('folder_name')
        parent_id = request.POST.get('parent_id')
        parent = Folder.objects.get(id=parent_id) if parent_id else None
        Folder.objects.create(name=name, parent=parent, owner=request.user)
        return redirect('folder_view')
    return HttpResponse("Invalid request method", status=405)

def delete_folder(request, folder_id):
    if request.method == 'POST':
        folder = get_object_or_404(Folder, id=folder_id)
        folder.delete()
        return JsonResponse({'message': 'Folder deleted successfully'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def cut_folder(request, folder_id):
    if request.method == 'POST':
        request.session['cut_folder_id'] = folder_id
        return JsonResponse({'message': 'Folder is selected to move. Now go to another folder and click Paste.'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def rename_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    data = json.loads(request.body)
    new_name = data.get('new_name')
    if new_name:
        folder.name = new_name
        folder.save()
        return JsonResponse({'message': 'Folder renamed successfully'})
    return JsonResponse({'error': 'New name is required'}, status=400)

def copy_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    new_folder = Folder.objects.create(name=f"{folder.name}_copy")
    for file in UploadedFile.objects.filter(folder=folder):
        UploadedFile.objects.create(folder=new_folder, file=file.file)
    return JsonResponse({'message': 'Folder copied successfully'})

def paste_folder(request, target_folder_id):
    if request.method == 'POST':
        cut_folder_id = request.session.get('cut_folder_id')
        if not cut_folder_id:
            return JsonResponse({'error': 'No folder in clipboard to paste'}, status=400)

        cut_folder = get_object_or_404(Folder, id=cut_folder_id)
        target_folder = get_object_or_404(Folder, id=target_folder_id)

        # Prevent moving into itself or its children
        if cut_folder.id == target_folder.id or target_folder in cut_folder.children.all():
            return JsonResponse({'error': 'Cannot paste folder into itself or its children'}, status=400)

        cut_folder.parent = target_folder
        cut_folder.save()

        del request.session['cut_folder_id']
        return JsonResponse({'message': f'Folder moved to {target_folder.name}'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .models import UserProfile

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        profile_pic = request.FILES.get('profile_pic')
        bio = request.POST.get('bio')
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password1)

        # ✅ Create UserProfile manually
        UserProfile.objects.create(
            user=user,
            bio=bio,
            profile_pic=profile_pic
        )

        messages.success(request, "Registration successful. Please log in.")
        return redirect('login')

    return render(request, 'register.html')

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('folder_view')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')

    return render(request, 'login.html')

from .models import Folder
from django.contrib.auth.decorators import login_required

@login_required
# def create_folder(request):
#     if request.method == 'POST':
#         name = request.POST['name']
#         parent_id = request.POST.get('parent_id')  # optional
#         parent = Folder.objects.get(id=parent_id) if parent_id else None

#         Folder.objects.create(
#             name=name,
#             parent=parent,
#             owner=request.user  # 👈 associate folder with logged-in user
#         )

#         return redirect('folder_view')
#     return render(request, 'create_folder.html')

# def folder_detail(request, folder_id):
#     folder = get_object_or_404(Folder, id=folder_id)
#     files = folder.files.all()  # related_name='files'
    
#     # Include subfolders (or however you define "folders_with_files")
#     folders_with_files = [
#         {'folder': f} for f in Folder.objects.filter(parent=folder)
#     ]
    
#     return render(request, 'folder_detail.html', {
#         'folder': folder,
#         'files': files,
#         'folders_with_files': folders_with_files
#     })

@csrf_exempt
@login_required
def folder_detail(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)

    # Restrict access to owner or admin
    if not request.user.is_superuser and folder.owner != request.user:
        return HttpResponseForbidden("You are not allowed to access this folder.")

    files = folder.files.all()
    folders_with_files = [{'folder': f} for f in Folder.objects.filter(parent=folder)]

    if request.method == 'POST':
        action = request.path.strip('/').split('/')[-1]
        data = json.loads(request.body)

        if action == 'new':
            return handle_new_item(request, folder)
        elif action == 'delete':
            return JsonResponse({'message': 'Deleted successfully'})
        elif action == 'rename':
            return JsonResponse({'message': f"Renamed to {data.get('name')}"})
        elif action in ['cut', 'copy', 'paste']:
            return JsonResponse({'message': f"{action.title()} complete"})

    return render(request, 'folder_detail.html', {
        'folder': folder,
        'files': files,
        'folders_with_files': folders_with_files,
    })


from django.core.files.base import ContentFile

def handle_new_item(request, folder):
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        item_type = data.get('type', 'folder')

        if not name:
            return JsonResponse({'error': 'Name is required'}, status=400)

        folder_path = os.path.join(settings.MEDIA_ROOT, 'folders', str(folder.id))
        os.makedirs(folder_path, exist_ok=True)

        if item_type == 'folder':
            new_folder = Folder.objects.create(name=name, parent=folder, owner=request.user)
            return JsonResponse({'id': new_folder.id, 'name': new_folder.name})

        # Supported extensions
        extension_map = {
            'text': '.txt',
            'word': '.docx',
            'excel': '.xlsx',
            'ppt': '.pptx',
            'pdf': '.pdf',
            'json': '.json'
        }

        if item_type not in extension_map:
            return JsonResponse({'error': 'Unsupported file type'}, status=400)

        filename = f"{name}{extension_map[item_type]}"
        relative_path = f'uploads/folders/{folder.id}/{filename}'
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write("")

        file_record = File.objects.create(name=filename, folder=folder)
        file_record.path.save(relative_path, ContentFile(''), save=True)

        return JsonResponse({
            'id': file_record.id,
            'name': file_record.name,
            'url': file_record.path.url
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import os

@csrf_exempt
@login_required
def delete_item(request, folder_id):
    if request.method == 'POST':
        try:
            folder = get_object_or_404(Folder, id=folder_id)

            # Restrict access
            if not request.user.is_superuser and folder.owner != request.user:
                return HttpResponseForbidden("You are not allowed to delete in this folder.")

            data = json.loads(request.body)
            item_id = data.get('id')
            item_type = data.get('type')

            if item_type == 'file':
                file = get_object_or_404(File, id=item_id, folder=folder)
                file_path = file.path.path
                if os.path.exists(file_path):
                    os.remove(file_path)
                file.delete()
                return JsonResponse({'success': 'File deleted successfully'})

            elif item_type == 'folder':
                sub_folder = get_object_or_404(Folder, id=item_id, parent=folder)
                sub_folder.delete()
                return JsonResponse({'success': 'Folder deleted successfully'})

            else:
                return JsonResponse({'error': 'Invalid item type'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@login_required
def upload_file(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)

    if not request.user.is_superuser and folder.owner != request.user:
        return HttpResponseForbidden("You are not allowed to upload to this folder.")

    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        file_instance = File.objects.create(
            folder=folder,
            name=uploaded_file.name,
            path=uploaded_file  # 👈 use correct field name
        )
        return redirect('folder_detail', folder_id=folder.id)
    return HttpResponseForbidden("Invalid upload request")

# views.py
def folder_detailed(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    
    # files in the current folder
    files = folder.files.all()

    # if you want to show subfolders with files (optional)
    # folders_with_files = [{'folder': f, 'files': f.files.all()} for f in Folder.objects.filter(parent=folder)]
    folders_with_files = []  # if you're not using nested folders yet

    return render(request, 'folder_details.html', {
        'folder': folder,
        'files': files,
        'folders_with_files': folders_with_files,
    })


# Download a file
from django.http import FileResponse, Http404
from .models import File  # or your file model

def download_file(request, file_id):
    try:
        file_obj = File.objects.get(id=file_id)
        response = FileResponse(file_obj.file.open('rb'), as_attachment=False)
        return response
    except File.DoesNotExist:
        raise Http404("File not found")

# # Handle folder creation
# def create_new_folder(request, folder_id):
#     if request.method == 'POST':
#         import json
#         data = json.loads(request.body)
#         name = data.get('name')
#         if name:
#             new_folder = Folder.objects.create(name=name, parent_id=folder_id)
#             return JsonResponse({
#                 'id': new_folder.id,
#                 'name': new_folder.name,
#                 'message': 'Folder created successfully.'
#             })
#         return JsonResponse({'error': 'Name is required.'}, status=400)

# # // sub folder
# def cutted_folder(request, folder_id):
#     if request.method == 'POST':
#         request.session['cut_folder_id'] = folder_id
#         request.session['action'] = 'cut'
#         return JsonResponse({'message': 'Cut ready'})
#     return JsonResponse({'error': 'Invalid request'}, status=400)

# @csrf_exempt
# def copied_folder(request, folder_id):
#     if request.method == 'POST':
#         request.session['copy_folder_id'] = folder_id
#         request.session['action'] = 'copy'
#         return JsonResponse({'message': 'Copy ready'})
#     return JsonResponse({'error': 'Invalid request'}, status=400)

# @csrf_exempt
# def pasted_folder(request, destination_folder_id):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             source_id = data.get('source_id')
#             paste_action = data.get('paste_action')

#             source_folder = get_object_or_404(Folder, id=source_id)
#             destination_folder = get_object_or_404(Folder, id=destination_folder_id)

#             if paste_action == 'copy':
#                 # Duplicate the folder (shallow copy - no children or files)
#                 copied_folder = Folder.objects.create(
#                     name=source_folder.name + ' (Copy)',
#                     parent=destination_folder
#                 )
#                 return JsonResponse({'message': 'Folder copied successfully.', 'id': copied_folder.id})

#             elif paste_action == 'cut':
#                 source_folder.parent = destination_folder
#                 source_folder.save()
#                 return JsonResponse({'message': 'Folder moved successfully.'})

#             else:
#                 return JsonResponse({'error': 'Invalid paste action.'}, status=400)

#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)

#     return JsonResponse({'error': 'Invalid request method.'}, status=405)

# @csrf_exempt
# def deleted_folder(request, folder_id):
#     if request.method == 'POST':
#         Folder.objects.filter(id=folder_id).delete()
#         return JsonResponse({'message': 'Folder deleted', 'reload': True})
#     return JsonResponse({'error': 'Invalid request'}, status=400)

# @csrf_exempt
# def renamed_folder(request, folder_id):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         new_name = data.get('name')
#         Folder.objects.filter(id=folder_id).update(name=new_name)
#         return JsonResponse({'message': 'Folder renamed', 'reload': True})
#     return JsonResponse({'error': 'Invalid request'}, status=400)

# @csrf_exempt
# def new_folder(request, folder_id):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         name = data.get('name')
#         Folder.objects.create(name=name, parent_id=folder_id)
#         return JsonResponse({'message': 'Folder created', 'reload': True})
#     return JsonResponse({'error': 'Invalid request'}, status=400)


