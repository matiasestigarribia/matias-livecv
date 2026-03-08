import io
from typing import Any

from sqladmin import Admin
from starlette.datastructures import FormData, UploadFile
from starlette.requests import Request


class UrlAwareAdmin(Admin):
    """
    Admin subclass that fixes sqladmin's _handle_form_data crash when a FileField
    column stores a plain URL string in the database instead of a file-like object.

    Stock sqladmin behaviour (application.py line 732-733):
        f = getattr(obj, key)                                  # URL string, e.g. "https://..."
        form_data.append((key, UploadFile(filename=f.name, file=f.open())))  # AttributeError

    The str type has no `.name` or `.open()` attributes, so the edit POST crashes.

    This override detects that case: when the stored value is a plain string and the
    upload was left empty, it passes the URL string through as-is (not wrapped in
    UploadFile). `on_model_change` on each affected ModelView then checks whether the
    received value is a string (preserve existing URL) or an UploadFile with content
    (upload the new file to R2 and store the resulting URL).

    The FileInputWidget shipped with sqladmin already renders:
        <p>Currently: {field.data}</p>
    when field.data is truthy on GET — so the admin user always sees the current URL.
    """

    async def _handle_form_data(self, request: Request, obj: Any = None) -> FormData:
        form = await request.form()
        form_data: list[tuple[str, str | UploadFile]] = []

        for key, value in form.multi_items():
            if not isinstance(value, UploadFile):
                form_data.append((key, value))
                continue

            should_clear = form.get(key + "_checkbox")
            empty_upload = len(await value.read(1)) != 1
            await value.seek(0)

            if should_clear:
                form_data.append((key, UploadFile(io.BytesIO(b""))))
            elif empty_upload and obj and getattr(obj, key):
                existing = getattr(obj, key)
                if isinstance(existing, str):
                    # Column stores a URL string, not a file object.
                    # Pass the URL through unchanged so on_model_change can
                    # detect it and skip the upload, preserving the current value.
                    form_data.append((key, existing))
                else:
                    # Original sqladmin behaviour for real file-backed columns.
                    form_data.append(
                        (key, UploadFile(filename=existing.name, file=existing.open()))
                    )
            else:
                form_data.append((key, value))

        return FormData(form_data)
