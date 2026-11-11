from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
)

from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
)


# Register View Documentation
register_docs = extend_schema_view(
    post=extend_schema(
        summary="Register a new user",
        description=(
            "Create a customer account using username, email, "
            "and password."
        ),
        request=RegisterSerializer,
        responses={
            201: RegisterSerializer,
            400: OpenApiResponse(
                description="Invalid registration data."
            ),
        },
        tags=["Accounts"],
    )
)


# User Profile View Documentation
user_profile_docs = extend_schema_view(
    get=extend_schema(
        summary="Retrieve user profile",
        description=(
            "Returns the profile of the currently authenticated user."
        ),
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
        },
        tags=["Accounts"],
    )
)


# Change Password View Documentation
change_password_docs = extend_schema_view(
    post=extend_schema(
        summary="Change password",
        description=(
            "Change the authenticated user's password "
            "after verifying the current password."
        ),
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(
                description="Password changed successfully."
            ),
            400: OpenApiResponse(
                description="Invalid current password or password data."
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
        },
        tags=["Accounts"],
    )
)


# User List View Documentation
user_list_docs = extend_schema_view(
    get=extend_schema(
        summary="List all users",
        description=(
            "Retrieve all registered users. "
            "Staff access is required."
        ),
        responses={
            200: UserProfileSerializer(many=True),
            403: OpenApiResponse(
                description="Staff permissions are required."
            ),
        },
        tags=["Accounts"],
    )
)