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

from .docs import (
    register_docs,
    user_profile_docs,
    change_password_docs,
    user_list_docs,
)


User = get_user_model()


@register_docs
class RegisterView(CreateAPIView):

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

   
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@user_profile_docs
class UserProfileView(RetrieveAPIView):

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        return self.request.user


@change_password_docs
class ChangePasswordView(GenericAPIView):

    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(
            {"message": "Password changed successfully."},
            status=status.HTTP_200_OK
        )


@user_list_docs
class UserListView(ListAPIView):

    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminUser]

    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)