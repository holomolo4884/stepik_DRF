from uuid import UUID

from rest_framework.exceptions import ValidationError, NotFound
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.common.utils import set_dict_attr
from apps.common.permissions import IsOwner

from apps.profiles.serializers import ProfileSerializer, ShippingAddressSerializer
from apps.profiles.models import ShippingAddress, Order, OrderItem
from apps.shop.serializers import OrderSerializer, CheckItemOrderSerializer

tags = ["Profiles"]


class ProfileView(APIView):
    permission_classes = [IsOwner]
    serializer_class = ProfileSerializer

    @extend_schema(
        summary="Retrieve Profile",
        description="""
                This endpoint allows a user to retrieve his/her profile.
            """,
        tags=tags,
    )
    def get(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update Profile",
        description="""
                    This endpoint allows a user to update his/her profile.
                """,
        tags=tags,
        request={"multipart/form-data": serializer_class},
    )
    def put(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = set_dict_attr(user, serializer.validated_data)
        user.save()
        serializer = self.serializer_class(user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Deactivate account",
        description="""
                This endpoint allows a user to deactivate his/her account.
            """,
        tags=tags,
    )
    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save()
        return Response(data={'message': 'User Account Deactivated'}, status=status.HTTP_200_OK)


class ShippingAddressView(APIView):
    permission_classes = [IsOwner]
    serializer_class = ShippingAddressSerializer

    @extend_schema(
        summary="Shipping Addresses Fetch",
        description="""
                This endpoint returns all shipping addresses associated with a user.
            """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        shipping_addresses = ShippingAddress.objects.filter(user=user)

        serializer = self.serializer_class(shipping_addresses, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create Shipping Address",
        description="""
                This endpoint allows a user to create a shipping address.
            """,
        tags=tags,
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        shipping_address, _ = ShippingAddress.objects.get_or_create(user=user, **data)
        serializer = self.serializer_class(shipping_address)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class ShippingAddressViewID(APIView):
    permission_classes = [IsOwner]
    serializer_class = ShippingAddressSerializer

    def get_object(self, user, shipping_id):
        try:
            shipping_uuid = UUID(shipping_id)
        except ValueError as exc:
            raise ValidationError({"message": "Invalid shipping id UUID format"}) from exc

        shipping_address = ShippingAddress.objects.get_or_none(user=user, id=shipping_uuid)
        if shipping_address is None:
            raise NotFound(detail={"message": "Shipping Address does not exist!"}, code=404)
        self.check_object_permissions(self.request, shipping_address)
        return shipping_address

    @extend_schema(
        summary="Shipping Address Fetch ID",
        description="""
        This endpoint returns a single shipping address associated with a user.
        """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        shipping_address = self.get_object(user, kwargs["id"])
        serializer = self.serializer_class(shipping_address)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update Shipping Address ID",
        description="""
        This endpoint allows a user to update his/her shipping address.
        """,
        tags=tags,
    )
    def put(self, request, *args, **kwargs):
        user = request.user
        shipping_address = self.get_object(user, kwargs["id"])
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        shipping_address = set_dict_attr(shipping_address, data)
        shipping_address.save()
        serializer = self.serializer_class(shipping_address)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Delete Shipping Address ID",
        description="""
        This endpoint allows a user to delete his/her shipping address.
        """,
        tags=tags,
    )
    def delete(self, request, *args, **kwargs):
        user = request.user
        shipping_address = self.get_object(user, kwargs["id"])
        shipping_address.delete()
        return Response(data={"message": "Shipping address deleted successfully"},
                        status=status.HTTP_200_OK)


class OrdersView(APIView):
    permission_classes = [IsOwner]
    serializer_class = OrderSerializer

    @extend_schema(
        operation_id="orders_view",
        summary="Orders Fetch",
        description="""
            This endpoint returns all orders for a particular user.
        """,
        tags=tags
    )
    def get(self, request):
        user = request.user
        orders = (Order.objects.filter(user=user).select_related("user")
                  .prefetch_related("orderitems", "orderitems__product")
                  .order_by("-created_at"))
        serializer = self.serializer_class(orders, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class OrderItemsView(APIView):
    permission_classes = [IsOwner]
    serializer_class = CheckItemOrderSerializer

    @extend_schema(
        operation_id="order_items_view",
        summary="Items Order Fetch",
        description="""
            This endpoint returns all items order for a particular user.
        """,
        tags=tags,
    )
    def get(self, request, **kwargs):
        order = Order.objects.get_or_none(tx_ref=kwargs["tx_ref"])
        if not order or order.user != request.user:
            return Response(data={"message": "Order does not exist!"},
                            status=status.HTTP_404_NOT_FOUND)
        order_items = OrderItem.objects.filter(order=order).select_related(
            "product", "product__seller", "product__seller__user"
        )
        serializer = self.serializer_class(order_items, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)