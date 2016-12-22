import logging
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid

log = logging.getLogger(__name__)


class FileUploadMixin(object):
    file_types = {
        'THUMBNAIL': '/thumbnails/',
        'BACKGROUND': '/backgrounds/',
        'VIDEO': '/videos/',
        'JSON': '/json/',
        'PDF': '/pdf/'
    }

    AWS_S3_BASE_URL = settings.AWS_S3_BASE_URL
    AWS_STORAGE_BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME
    BUFFER_ITEM_NAME = "field_name"
    BUFFER_ITEM_URL = "url"

    def upload_to_s3(self, field_name, file_type, file, xblock_id, upload_buffer={}):
        file_uuid = str(uuid.uuid1())
        content = ContentFile(file.read())
        hashed_xblock_id = str(hash(xblock_id))

        # upload the new file to S3
        relative_path = default_storage.save(
            self.file_types[file_type] + hashed_xblock_id + '/' + file_uuid + '_' + file.name,
            content)

        absolute_path = self.create_absolute_path(relative_path)

        # check if there already is an uploaded file of this type in the buffer
        if file_type in upload_buffer:
            # delete the temporary file and replace it with this one
            existing_url = upload_buffer[file_type][self.BUFFER_ITEM_NAME]
            self.delete_from_s3(existing_url)

        # save the new URL to the buffer
        buffer_item = {self.BUFFER_ITEM_NAME: field_name, self.BUFFER_ITEM_URL: absolute_path}
        upload_buffer[file_type] = buffer_item

        return upload_buffer

    @classmethod
    def swap_urls_from_buffer(cls, xblock):
        print str(xblock.uploaded_files)
        for key, value in xblock.uploaded_files.items():
            print str(key)
            print str(value)
            print 'STA ME JEBESs'

            field_name = value[cls.BUFFER_ITEM_NAME]
            old_url = getattr(xblock, field_name)
            print field_name
            print old_url
            cls.delete_from_s3(old_url)
            print 'after delete'
            new_url = value[cls.BUFFER_ITEM_URL]
            print new_url
            try:
                setattr(xblock, field_name, new_url)
            except Exception as e:
                print 'puklo majke ti ' + str(e)
            print 'je li puklo'
        print str(xblock)
        xblock.uploaded_files = {}

    @classmethod
    def create_absolute_path(cls, relative_path):
        return cls.AWS_S3_BASE_URL + cls.AWS_STORAGE_BUCKET_NAME + relative_path

    @classmethod
    def delete_from_s3(cls, url):
        try:
            # delete the previously uploaded file if it exists on S3
            if url and cls.AWS_STORAGE_BUCKET_NAME in url:
                name_to_delete = url.split(cls.AWS_STORAGE_BUCKET_NAME, 1)[1]
                if default_storage.exists(name_to_delete):
                    default_storage.delete(name_to_delete)
        except Exception as e:
            log.exception(e.message)
