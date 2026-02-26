import os
import asyncio

from sqladmin import ModelView
from wtforms import FileField
from starlette.datastructures import UploadFile

from app.models.contact_messages import ContactMessage
from app.models.experiences import Experience
from app.models.profile import Profile
from app.models.projects import Project
from app.models.project_images import ProjectImage
from app.models.skills import Skill
from app.models.spoken_languages import SpokenLanguage
from app.models.users import User
from app.models.uploaded_documents import UploadedDocument
from app.models.rag_documents import RagDocument
from app.models.chat_logs import ChatLog
from app.services.ai_service import process_and_embed_document
from app.services.image_service import optimize_image_bytes
from app.services.storage_service import upload_file_to_r2


class CustomFileField(FileField):
    def process_data(self, value):
        self.data = None


class UserAdmin(ModelView, model=User):
    name_plural = 'Users'
    icon = 'fa-solid fa-users'
    
    column_list = [User.id, User.username, User.email, User.created_at]
    
    column_searchable_list = [User.username, User.email]


class ProfileAdmin(ModelView, model=Profile):
    name_plural = 'Profile Data'
    icon = 'fa-solid fa-user-tie'
    
    column_list = [Profile.id, Profile.full_name, Profile.updated_at]
    form_excluded_columns = [Profile.created_at, Profile.updated_at]
    
    form_overrides = {
        'cv_spanish': FileField,
        'cv_portuguese': FileField,
        'cv_english': FileField,
    }
    
    form_widget_args = {
        'headline': {'rows': 5},
        'about_text': {'rows': 10},
        'summary_text': {'rows': 10},
        'social_links': {'rows': 5},
    }

    async def on_model_change(self, data, model, is_created, request):
        cv_fields = ['cv_english', 'cv_portuguese', 'cv_spanish']
        
        for field_name in cv_fields:
            if data.get(field_name) and hasattr(data[field_name], 'filename'):
                upload_file = data[field_name]
                content = await upload_file.read()
                
                public_url = await upload_file_to_r2(
                    file_bytes=content,
                    folder='documents',
                    file_name=upload_file.filename,
                    content_type='application/pdf'
                )
                
                data[field_name] = public_url

class ExperienceAdmin(ModelView, model=Experience):
    
    name_plural = 'Experiences'
    icon = 'fa-solid fa-briefcase'
    
    column_list = [Experience.id, Experience.company_name, Experience.is_current, Experience.updated_at]

    form_widget_args = {
        'role': {'rows': 5},
        'description': {'rows': 10},
    }

    form_excluded_columns = [Experience.created_at, Experience.updated_at]

class SpokenLanguageAdmin(ModelView, model=SpokenLanguage):
    name_plural = 'Spoken Languages'
    icon = 'fa-solid fa-language'
    
    column_list = [SpokenLanguage.id, SpokenLanguage.language_name, SpokenLanguage.proficiency_level]

    form_widget_args = {
        'language_name': {'rows': 5},
        'proficiency_level': {'rows': 5},
    }

    form_excluded_columns = [SpokenLanguage.created_at, SpokenLanguage.updated_at]

class ContactMessageAdmin(ModelView, model=ContactMessage):
    name_plural = 'Contact Messages'
    
    icon = 'fa-solid fa-envelope'
    
    column_list = [ContactMessage.id, ContactMessage.name, ContactMessage.email,
                   ContactMessage.is_read]
    
    form_excluded_columns = [ContactMessage.created_at, ContactMessage.updated_at]


class ProjectAdmin(ModelView, model=Project):
    name_plural = 'Projects'
    
    icon = 'fa-solid fa-laptop-code'
    
    column_list = [Project.id, Project.title, Project.featured, Project.updated_at]
    
    form_widget_args = {
        'title': {'rows': 5},
        'short_description': {'rows': 5},
        'long_description': {'rows': 10},
    }

    form_excluded_columns = [Project.created_at, Project.updated_at]

class ProjectImageAdmin(ModelView, model=ProjectImage):
    name_plural = 'Project images'
    icon = 'fa-solid fa-images'
    
    column_list = [
        ProjectImage.id,
        ProjectImage.project_id,
        ProjectImage.image_url,
        ProjectImage.is_cover,
        ProjectImage.display_order
    ]

    form_overrides = {'image_url': FileField}
    form_excluded_columns = [ProjectImage.id, ProjectImage.created_at, ProjectImage.updated_at]
    
    async def on_model_change(self, data, model, is_created, request):
        if data.get('image_url') and hasattr(data['image_url'], 'filename'):
            upload_file = data['image_url']
            
            webp_bytes, new_filename = await optimize_image_bytes(upload_file)

            public_url = await upload_file_to_r2(
                file_bytes=webp_bytes,
                folder='projects',
                file_name=new_filename,
                content_type='image/webp'
            )
            
            data['image_url'] = public_url

class SkillAdmin(ModelView, model=Skill):
    name_plural = 'Skills'
    
    icon = 'fa-solid fa-code'
    
    column_list = [Skill.id, Skill.name, Skill.category]
    
    form_excluded_columns = [Skill.created_at, Skill.updated_at]


class RagDocumentAdmin(ModelView, model=RagDocument):
    name_plural = 'Rag Documents'
    
    icon = 'fa-solid fa-file'
    
    column_list = [RagDocument.id, RagDocument.source, RagDocument.language, RagDocument.created_at]

    form_columns = [
        RagDocument.source, 
        RagDocument.content, 
        RagDocument.language, 
        RagDocument.active
    ]

class ChatLogAdmin(ModelView, model=ChatLog):
    name_plural = 'Chat logs'
    
    icon = 'fa-solid fa-comments'
    
    column_list = [ChatLog.id, ChatLog.user_message, ChatLog.bot_reply, ChatLog.created_at]


class UploadedDocumentAdmin(ModelView, model=UploadedDocument):
    name_plural = 'Upload Rag Docs'
    icon = 'fa-solid fa-file-arrow-up'
    
    form_overrides = {'file_path': FileField}
    
    column_list = [UploadedDocument.id, UploadedDocument.filename, UploadedDocument.language]
    
    form_columns = [
        UploadedDocument.filename,
        UploadedDocument.file_path,
        UploadedDocument.language
    ]
    
    async def on_model_change(self, data, model, is_created, request):
        if is_created and data.get("file_path") and hasattr(data["file_path"], "filename"):
            upload_file = data["file_path"]
            content = await upload_file.read()
            
            public_url = await upload_file_to_r2(
                file_bytes=content,
                folder='ragdocs',
                file_name=upload_file.filename,
                content_type=upload_file.content_type or 'application/pdf'
            )
            
            data['file_path'] = public_url
            data['filename'] = upload_file.filename
            
            
            asyncio.create_task(
                process_and_embed_document(
                    file_bytes=content,
                    filename=upload_file.filename,
                    language=data.get('language', 'en')
                )
            )
            