"""
Course API Views
"""

from django.core.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView

from openedx.core.lib.api.paginators import NamespacedPageNumberPagination
from openedx.core.lib.api.view_utils import view_auth_classes, DeveloperErrorViewMixin
from .api import course_detail, list_courses
from .forms import CourseDetailGetForm, CourseListGetForm
from .serializers import CourseSerializer, CourseDetailSerializer
from .courseware_access import get_course_child, get_course_key, course_exists, get_ids_from_list_param
from django.http import Http404
from progress.models import CourseModuleCompletion
from progress.serializers import CourseModuleCompletionSerializer


@view_auth_classes(is_authenticated=False)
class CourseDetailView(DeveloperErrorViewMixin, RetrieveAPIView):
    """
    **Use Cases**

        Request details for a course

    **Example Requests**

        GET /api/courses/v1/courses/{course_key}/

    **Response Values**

        Body consists of the following fields:

        * effort: A textual description of the weekly hours of effort expected
            in the course.
        * end: Date the course ends, in ISO 8601 notation
        * enrollment_end: Date enrollment ends, in ISO 8601 notation
        * enrollment_start: Date enrollment begins, in ISO 8601 notation
        * id: A unique identifier of the course; a serialized representation
            of the opaque key identifying the course.
        * media: An object that contains named media items.  Included here:
            * course_image: An image to show for the course.  Represented
              as an object with the following fields:
                * uri: The location of the image
        * name: Name of the course
        * number: Catalog number of the course
        * org: Name of the organization that owns the course
        * overview: A possibly verbose HTML textual description of the course.
            Note: this field is only included in the Course Detail view, not
            the Course List view.
        * short_description: A textual description of the course
        * start: Date the course begins, in ISO 8601 notation
        * start_display: Readably formatted start of the course
        * start_type: Hint describing how `start_display` is set. One of:
            * `"string"`: manually set by the course author
            * `"timestamp"`: generated from the `start` timestamp
            * `"empty"`: no start date is specified
        * pacing: Course pacing. Possible values: instructor, self

        Deprecated fields:

        * blocks_url: Used to fetch the course blocks
        * course_id: Course key (use 'id' instead)

    **Parameters:**

        username (optional):
            The username of the specified user for whom the course data
            is being accessed. The username is not only required if the API is
            requested by an Anonymous user.

    **Returns**

        * 200 on success with above fields.
        * 400 if an invalid parameter was sent or the username was not provided
          for an authenticated request.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the course is not available or cannot be seen.

        Example response:

            {
                "blocks_url": "/api/courses/v1/blocks/?course_id=edX%2Fexample%2F2012_Fall",
                "media": {
                    "course_image": {
                        "uri": "/c4x/edX/example/asset/just_a_test.jpg",
                        "name": "Course Image"
                    }
                },
                "description": "An example course.",
                "end": "2015-09-19T18:00:00Z",
                "enrollment_end": "2015-07-15T00:00:00Z",
                "enrollment_start": "2015-06-15T00:00:00Z",
                "course_id": "edX/example/2012_Fall",
                "name": "Example Course",
                "number": "example",
                "org": "edX",
                "overview: "<p>A verbose description of the course.</p>"
                "start": "2015-07-17T12:00:00Z",
                "start_display": "July 17, 2015",
                "start_type": "timestamp",
                "pacing": "instructor"
            }
    """

    serializer_class = CourseDetailSerializer

    def get_object(self):
        """
        Return the requested course object, if the user has appropriate
        permissions.
        """
        requested_params = self.request.query_params.copy()
        requested_params.update({'course_key': self.kwargs['course_key_string']})
        form = CourseDetailGetForm(requested_params, initial={'requesting_user': self.request.user})
        if not form.is_valid():
            raise ValidationError(form.errors)

        return course_detail(
            self.request,
            form.cleaned_data['username'],
            form.cleaned_data['course_key'],
        )


@view_auth_classes(is_authenticated=False)
class CourseListView(DeveloperErrorViewMixin, ListAPIView):
    """
    **Use Cases**

        Request information on all courses visible to the specified user.

    **Example Requests**

        GET /api/courses/v1/courses/

    **Response Values**

        Body comprises a list of objects as returned by `CourseDetailView`.

    **Parameters**

        username (optional):
            The username of the specified user whose visible courses we
            want to see. The username is not required only if the API is
            requested by an Anonymous user.

        org (optional):
            If specified, visible `CourseOverview` objects are filtered
            such that only those belonging to the organization with the
            provided org code (e.g., "HarvardX") are returned.
            Case-insensitive.

        mobile (optional):
            If specified, only visible `CourseOverview` objects that are
            designated as mobile_available are returned.

    **Returns**

        * 200 on success, with a list of course discovery objects as returned
          by `CourseDetailView`.
        * 400 if an invalid parameter was sent or the username was not provided
          for an authenticated request.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the specified user does not exist, or the requesting user does
          not have permission to view their courses.

        Example response:

            [
              {
                "blocks_url": "/api/courses/v1/blocks/?course_id=edX%2Fexample%2F2012_Fall",
                "media": {
                  "course_image": {
                    "uri": "/c4x/edX/example/asset/just_a_test.jpg",
                    "name": "Course Image"
                  }
                },
                "description": "An example course.",
                "end": "2015-09-19T18:00:00Z",
                "enrollment_end": "2015-07-15T00:00:00Z",
                "enrollment_start": "2015-06-15T00:00:00Z",
                "course_id": "edX/example/2012_Fall",
                "name": "Example Course",
                "number": "example",
                "org": "edX",
                "start": "2015-07-17T12:00:00Z",
                "start_display": "July 17, 2015",
                "start_type": "timestamp"
              }
            ]
    """

    pagination_class = NamespacedPageNumberPagination
    serializer_class = CourseSerializer

    def get_queryset(self):
        """
        Return a list of courses visible to the user.
        """
        form = CourseListGetForm(self.request.query_params, initial={'requesting_user': self.request.user})
        if not form.is_valid():
            raise ValidationError(form.errors)

        return list_courses(
            self.request,
            form.cleaned_data['username'],
            org=form.cleaned_data['org'],
            filter_=form.cleaned_data['filter_'],
        )


# @view_auth_classes(is_authenticated=False)
class CourseModuleCompletionList(ListAPIView):
    """
    ### The CourseModuleCompletionList allows clients to view user's course module completion entities
    to monitor a user's progression throughout the duration of a course,
    - URI: ```/api/courses/{course_id}/completions```
    - GET: Returns a JSON representation of the course, content and user and timestamps
    - GET Example:
        {
            "count":"1",
            "num_pages": "1",
            "previous": null
            "next": null
            "results": [
                {
                    "id": 2,
                    "user_id": "3",
                    "course_id": "32fgdf",
                    "content_id": "324dfgd",
                    "stage": "First",
                    "created": "2014-06-10T13:14:49.878Z",
                    "modified": "2014-06-10T13:14:49.914Z"
                }
            ]
        }
    Filters can also be applied
    ```/api/courses/{course_id}/completions/?user_id={user_id}```
    ```/api/courses/{course_id}/completions/?content_id={content_id}&stage={stage}```
    ```/api/courses/{course_id}/completions/?user_id={user_id}&content_id={content_id}```
    - POST: Creates a Course-Module completion entity
    - POST Example:
        {
            "content_id":"i4x://the/content/location",
            "user_id":4,
            "stage": "First"
        }
    ### Use Cases/Notes:
    * Use GET operation to retrieve list of course completions by user
    * Use GET operation to verify user has completed specific course module
    """
    serializer_class = CourseModuleCompletionSerializer

    def get_queryset(self):
        """
        GET /api/courses/{course_id}/completions/
        """
        content_id = self.request.query_params.get('content_id', None)
        stage = self.request.query_params.get('stage', None)
        course_id = self.kwargs['course_key_string']
        if not course_exists(self.request, self.request.user, course_id):
            raise Http404
        course_key = get_course_key(course_id)
        queryset = CourseModuleCompletion.objects.filter(course_id=course_key)
        # user_ids = get_ids_from_list_param(self.request, 'user_id')
        #user_ids = map(int, [self.request.query_params.get('user_id')])
        print dir(self.request.user)
        user_ids = [self.request.user.id]
        print '--- nakon user IDs ---'
        if user_ids:
            queryset = queryset.filter(user__in=user_ids)
            print '++++++' + str(queryset)

        print '_____ nakon' + str(queryset)

        if content_id:
            content_descriptor, content_key, existing_content = get_course_child(self.request, self.request.user,
                                                                                 course_key,
                                                                                 content_id)  # pylint: disable=W0612,C0301
            print 'SSSSSSSSSSSSSSSS' + str(dir(content_descriptor))
            if not content_descriptor:
                raise Http404
            queryset = queryset.filter(content_id=content_key)

        if stage:
            queryset = queryset.filter(stage=stage)

        return queryset
