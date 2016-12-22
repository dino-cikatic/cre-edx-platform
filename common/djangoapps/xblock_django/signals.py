from django.dispatch import receiver
import logging
from celery.task import task

from xmodule.modulestore.django import modulestore, SignalHandler
from xmodule.modulestore.mixed import MixedModuleStore
from xmodule.modulestore.exceptions import (
    ItemNotFoundError, DuplicateItemError, DuplicateCourseError, InvalidBranchSetting
)
from opaque_keys.edx.keys import CourseKey
from xblock_django.mixins import FileUploadMixin
from student.models import get_user
from contentstore.views.item import StudioEditModuleRuntime
from django.utils.decorators import method_decorator
from util.db import outer_atomic

log = logging.getLogger(__name__)


@receiver(SignalHandler.pre_publish)
def listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Receives publishing signal and performs publishing related workflows, such as
    registering proctored exams, building up credit requirements, and performing
    search indexing
    """
    print '++++++++++++++++++++++++++++++++RADI LI OVO UOPCE++++++++++++++++++++++++++++++++++'
    course_key = CourseKey.from_string(str(course_key))
    update_xblock_resources.delay(course_key)


@task()
@method_decorator(outer_atomic(read_committed=True))
def update_xblock_resources(course_key):

    user = get_user('staff@example.com')
    print '--------------- user ------------------'
    print user

    def _internal_depth_first(item_location, is_root):
        """
        Depth first publishing from the given location
        """
        try:
            # handle child does not exist w/o killing update
            item = modulestore().get_item(item_location)
        except ItemNotFoundError:
            log.warning('Cannot find: %s', item_location)
            return
        except Exception as e:
            log.warning('Error message: %s', e)
            return

        # iterate through the children first
        if item.has_children:
            print str(item.children)
            for child_loc in item.children:
                _internal_depth_first(child_loc, False)

        FileUploadMixin.swap_urls_from_buffer(item)

        print 'TESTINH'

        if hasattr(item, 'thumbnail_url'):
            print item.thumbnail_url

        item = modulestore().update_item(item, user, isPublish=True)
        item.xmodule_runtime = StudioEditModuleRuntime(user)

        print '------------------------ item ---------------------------'
        print dir(item)
        modulestore().publish(item.location, user)
        print str(modulestore().__class__)
        print str(MixedModuleStore.__bases__)
        print 'NAKON UPDATEA'
        return item

    course = modulestore().get_course(course_key)
    if course.has_children:
        for chapter in course.children:
            item = _internal_depth_first(chapter, True)
    print '--------------- course --------------------'
    print str(item.parent)
    modulestore().publish(item.parent.location, user.id)