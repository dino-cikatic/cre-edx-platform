from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid


class FileUploadMixin(object):

    def __init__(self, **kwargs):
        self._file_types = {
            'THUMBNAIL': '/thumbnails/',
            'BACKGROUND': '/backgrounds/',
            'VIDEO': '/videos/'
        }

    def upload_to_s3(self, file_type, file, xblock_id):
        thumbnail_uuid = str(uuid.uuid1())

        content = ContentFile(file.read())

        relative_path = default_storage.save(
            self._file_types[file_type] + xblock_id + '/' + thumbnail_uuid + '_' + file.name,
            content)
        return settings.AWS_S3_BASE_URL + settings.AWS_STORAGE_BUCKET_NAME + relative_path
