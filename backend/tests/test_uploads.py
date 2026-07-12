"""save_uploaded_image() — тип/размер и что файл реально попадает на диск
под сгенерированным именем (не пользовательским, см. utils/uploads.py)."""
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from app import config as config_module
from app.utils.uploads import save_uploaded_image


def make_upload(data: bytes, content_type: str | None) -> UploadFile:
    headers = Headers({"content-type": content_type}) if content_type else Headers({})
    return UploadFile(file=BytesIO(data), headers=headers)


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(config_module.settings, "upload_dir", str(tmp_path))
    monkeypatch.setattr(config_module.settings, "upload_max_size_mb", 1)
    return tmp_path


class TestSaveUploadedImage:
    def test_rejects_unsupported_content_type(self):
        with pytest.raises(HTTPException) as exc:
            save_uploaded_image(make_upload(b"not-an-image", "text/plain"))
        assert exc.value.status_code == 400

    def test_rejects_missing_content_type(self):
        with pytest.raises(HTTPException) as exc:
            save_uploaded_image(make_upload(b"data", None))
        assert exc.value.status_code == 400

    def test_rejects_empty_file(self):
        with pytest.raises(HTTPException) as exc:
            save_uploaded_image(make_upload(b"", "image/png"))
        assert exc.value.status_code == 400

    def test_rejects_file_over_max_size(self, upload_dir):
        oversized = b"x" * (1024 * 1024 + 1)  # ровно на 1 байт больше лимита (1 МБ)
        with pytest.raises(HTTPException) as exc:
            save_uploaded_image(make_upload(oversized, "image/jpeg"))
        assert exc.value.status_code == 413

    def test_saves_file_and_returns_url(self, upload_dir):
        url = save_uploaded_image(make_upload(b"\x89PNG-fake-bytes", "image/png"))
        assert url.startswith("/api/uploads/")
        assert url.endswith(".png")
        saved_files = list(upload_dir.iterdir())
        assert len(saved_files) == 1
        assert saved_files[0].read_bytes() == b"\x89PNG-fake-bytes"

    def test_generates_server_side_filename_not_user_supplied(self, upload_dir):
        """Имя файла не должно зависеть от filename пользователя (path
        traversal / расширение-маскировка) — только от Content-Type."""
        upload = make_upload(b"data", "image/webp")
        upload.filename = "../../evil.php.png"
        url = save_uploaded_image(upload)
        assert "evil" not in url
        assert ".." not in url
        assert url.endswith(".webp")
