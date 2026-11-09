from django.contrib.auth import get_user_model

from rest_framework.generics import (
    CreateAPIView,
    RetrieveAPIView,
    GenericAPIView,
    ListAPIView
)
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAdminUser
)
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema

from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer
)


User = get_user_model()


class RegisterView(CreateAPIView):
    """Register a new customer account."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register a new user",
        description="Create a customer account using username, email and password.",
        tags=["Accounts"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserProfileView(RetrieveAPIView):
    """Retrieve the profile of the authenticated user."""

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve user profile",
        description="Returns the profile of the currently authenticated user.",
        tags=["Accounts"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        return self.request.user


class ChangePasswordView(GenericAPIView):
    """Allow authenticated users to change their passwords."""

    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Change password",
        description="Change the authenticated user's password after verifying the current password.",
        tags=["Accounts"],
        responses={200: None}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(
            {"message": "Password changed successfully."},
            status=status.HTTP_200_OK
        )


class UserListView(ListAPIView):
    """Allow staff users to retrieve the user list."""

    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="List all users",
        description="Retrieve all registered users. Staff access required.",
        tags=["Accounts"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)