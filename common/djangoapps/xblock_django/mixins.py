import logging
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid
import re

log = logging.getLogger(__name__)


class FileUploadMixin(object):
    def __init__(self, **kwargs):
        self._file_types = {
            'THUMBNAIL': '/thumbnails/',
            'BACKGROUND': '/backgrounds/',
            'VIDEO': '/videos/',
            'JSON': '/json/',
            'SUBTITLES': '/subtitles/',
            'PDF': '/pdf/'
        }

    def upload_to_s3(self, file_type, file, xblock_id, file_url_to_delete=None):
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        file_uuid = str(uuid.uuid1())
        content = ContentFile(file.read())
        hashed_xblock_id = str(hash(xblock_id))
        safe_file_name = re.sub(r"(?![a-zA-Z-_0-9\.]).?", "", file.name)

        relative_path = default_storage.save(
            self._file_types[file_type] + hashed_xblock_id + '/' + file_uuid + '_' + safe_file_name,
            content)

        return settings.AWS_S3_BASE_URL + bucket_name + relative_path

        # try:
        #     # delete the previously uploaded file if it exists on S3
        #     if file_url_to_delete and bucket_name in file_url_to_delete:
        #         name_to_delete = file_url_to_delete.split(bucket_name, 1)[1]
        #         if default_storage.exists(name_to_delete):
        #             default_storage.delete(name_to_delete)
        # except Exception as e:
        #     log.exception(e.message)
        # finally:
        #     return settings.AWS_S3_BASE_URL + bucket_name + relative_path
