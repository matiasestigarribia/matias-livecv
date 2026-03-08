import asyncio

from sqladmin import ModelView
from wtforms import FileField

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


class UserAdmin(ModelView, model=User):
    name = 'User'
    name_plural = 'Users'
    icon = 'fa-solid fa-users'
    can_delete = True

    column_list = [User.id, User.username, User.email, User.created_at]

    column_searchable_list = [User.username, User.email]


class ProfileAdmin(ModelView, model=Profile):
    name = 'Profile'
    name_plural = 'Profile Data'
    icon = 'fa-solid fa-user-tie'
    can_delete = True

    column_list = [Profile.id, Profile.full_name, Profile.updated_at]

    # CV file fields are included in both create and edit forms.
    # UrlAwareAdmin._handle_form_data (see app/admin/admin.py) passes the stored
    # URL string through unchanged when the user leaves the file input empty,
    # so on_model_change can detect it and skip the upload, preserving the value.
    # FileInputWidget renders <p>Currently: {url}</p> on the edit GET automatically.
    form_create_rules = [
        'full_name', 'headline', 'about_text', 'summary_text',
        'cv_english', 'cv_spanish', 'cv_portuguese',
        'social_links', 'terminal_theme',
    ]
    form_edit_rules = [
        'full_name', 'headline', 'about_text', 'summary_text',
        'cv_english', 'cv_spanish', 'cv_portuguese',
        'social_links', 'terminal_theme',
    ]

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
            value = data.get(field_name)

            if value is None:
                # Field absent from form (shouldn't happen but guard it).
                continue

            if isinstance(value, str):
                # UrlAwareAdmin passed the existing URL string through unchanged
                # (empty upload on edit). Leave it as-is so the DB value is preserved.
                continue

            # It's an UploadFile — check whether the user actually sent bytes.
            if not hasattr(value, 'read'):
                continue

            content = await value.read()
            if not content:
                # Empty file input on create — store None.
                data[field_name] = None
                continue

            public_url = await upload_file_to_r2(
                file_bytes=content,
                folder='documents',
                file_name=value.filename,
                content_type='application/pdf'
            )

            data[field_name] = public_url


class ExperienceAdmin(ModelView, model=Experience):
    name = 'Experience'
    name_plural = 'Experiences'
    icon = 'fa-solid fa-briefcase'
    can_delete = True

    column_list = [Experience.id, Experience.company_name, Experience.is_current, Experience.updated_at]

    form_widget_args = {
        'role': {'rows': 5},
        'description': {'rows': 10},
    }

    form_excluded_columns = [Experience.created_at, Experience.updated_at]


class SpokenLanguageAdmin(ModelView, model=SpokenLanguage):
    name = 'Spoken Language'
    name_plural = 'Spoken Languages'
    icon = 'fa-solid fa-language'
    can_delete = True

    column_list = [SpokenLanguage.id, SpokenLanguage.language_name, SpokenLanguage.proficiency_level]

    form_widget_args = {
        'language_name': {'rows': 5},
        'proficiency_level': {'rows': 5},
    }

    form_excluded_columns = [SpokenLanguage.created_at, SpokenLanguage.updated_at]


class ContactMessageAdmin(ModelView, model=ContactMessage):
    name = 'Contact Message'
    name_plural = 'Contact Messages'
    icon = 'fa-solid fa-envelope'
    can_delete = True

    column_list = [ContactMessage.id, ContactMessage.name, ContactMessage.email,
                   ContactMessage.is_read]

    form_excluded_columns = [ContactMessage.created_at, ContactMessage.updated_at]


class ProjectAdmin(ModelView, model=Project):
    name = 'Project'
    name_plural = 'Projects'
    icon = 'fa-solid fa-laptop-code'
    can_delete = True

    column_list = [Project.id, Project.title, Project.featured, Project.updated_at]

    form_widget_args = {
        'title': {'rows': 5},
        'short_description': {'rows': 5},
        'long_description': {'rows': 10},
    }

    form_excluded_columns = [Project.created_at, Project.updated_at]


class ProjectImageAdmin(ModelView, model=ProjectImage):
    name = 'Project Image'
    name_plural = 'Project images'
    icon = 'fa-solid fa-images'
    can_delete = True

    column_list = [
        ProjectImage.id,
        ProjectImage.project_id,
        ProjectImage.image_url,
        ProjectImage.is_cover,
        ProjectImage.display_order
    ]

    form_overrides = {'image_url': FileField}
    # image_url is stored as a URL string. UrlAwareAdmin._handle_form_data passes
    # it through as a plain string on empty upload (edit), so on_model_change can
    # distinguish "no new file" (str) from "new file uploaded" (UploadFile).
    form_create_rules = ['project_id', 'image_url', 'is_cover', 'is_video', 'display_order']
    form_edit_rules = ['project_id', 'image_url', 'is_cover', 'is_video', 'display_order']

    async def on_model_change(self, data, model, is_created, request):
        value = data.get('image_url')

        if value is None or isinstance(value, str):
            # No new file uploaded (str = existing URL passed through by UrlAwareAdmin).
            return

        if not hasattr(value, 'read'):
            return

        webp_bytes, new_filename = await optimize_image_bytes(value)

        public_url = await upload_file_to_r2(
            file_bytes=webp_bytes,
            folder='projects',
            file_name=new_filename,
            content_type='image/webp'
        )

        data['image_url'] = public_url


class SkillAdmin(ModelView, model=Skill):
    name = 'Skill'
    name_plural = 'Skills'
    icon = 'fa-solid fa-code'
    can_delete = True

    column_list = [Skill.id, Skill.name, Skill.category]

    form_excluded_columns = [Skill.created_at, Skill.updated_at]


class RagDocumentAdmin(ModelView, model=RagDocument):
    name = 'RAG Document'
    name_plural = 'Rag Documents'
    icon = 'fa-solid fa-file'
    can_delete = True

    column_list = [RagDocument.id, RagDocument.source, RagDocument.language, RagDocument.created_at]

    form_columns = [
        RagDocument.source,
        RagDocument.content,
        RagDocument.language,
        RagDocument.active
    ]


class ChatLogAdmin(ModelView, model=ChatLog):
    name = 'Chat Log'
    name_plural = 'Chat logs'
    icon = 'fa-solid fa-comments'
    can_delete = True

    column_list = [ChatLog.id, ChatLog.user_message, ChatLog.bot_reply, ChatLog.created_at]


class UploadedDocumentAdmin(ModelView, model=UploadedDocument):
    name = 'RAG Upload'
    name_plural = 'Upload Rag Docs'
    icon = 'fa-solid fa-file-arrow-up'
    can_delete = True

    form_overrides = {'file_path': FileField}

    column_list = [UploadedDocument.id, UploadedDocument.filename, UploadedDocument.language]

    # file_path stored as a URL string. UrlAwareAdmin._handle_form_data passes the
    # URL through as a plain string on empty upload, so on_model_change can detect
    # whether a new file was provided (UploadFile) or not (str, skip upload).
    form_create_rules = ['filename', 'file_path', 'language']
    form_edit_rules = ['filename', 'file_path', 'language']

    async def on_model_change(self, data, model, is_created, request):
        value = data.get("file_path")

        if value is None or isinstance(value, str):
            # No new file uploaded (str = existing URL passed through by UrlAwareAdmin).
            return

        if not hasattr(value, "filename"):
            return

        content = await value.read()
        if not content:
            return

        public_url = await upload_file_to_r2(
            file_bytes=content,
            folder='ragdocs',
            file_name=value.filename,
            content_type=value.content_type or 'application/pdf'
        )

        data['file_path'] = public_url
        data['filename'] = value.filename

        asyncio.create_task(
            process_and_embed_document(
                file_bytes=content,
                filename=value.filename,
                language=data.get('language', 'en')
            )
        )
