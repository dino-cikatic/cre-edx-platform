"""
Course API URLs
"""
from django.conf import settings
from django.conf.urls import patterns, url, include

from .views import CourseDetailView, CourseListView, CourseModuleCompletionList

urlpatterns = patterns(
    '',
    url(r'^v1/courses/$', CourseListView.as_view(), name="course-list"),
    url(r'^v1/courses/{0}/completions$'.format(settings.COURSE_KEY_PATTERN),
        CourseModuleCompletionList.as_view(), name='completion-list'),
    url(r'^v1/courses/{}'.format(settings.COURSE_KEY_PATTERN), CourseDetailView.as_view(), name="course-detail"),
    url(r'', include('course_api.blocks.urls'))
)
