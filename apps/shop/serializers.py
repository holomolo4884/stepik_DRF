from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.profiles.serializers import ShippingAddressSerializer
from apps.shop.models import Product, Review


class CategorySerializer(serializers.Serializer):
    name = serializers.CharField()
    slug = serializers.SlugField(read_only=True)
    image = serializers.ImageField()


class SellerShopSerializer(serializers.Serializer):
    name = serializers.CharField(source="business_name")
    slug = serializers.SlugField()
    avatar = serializers.CharField(source="user.avatar")


class ProductSerializer(serializers.Serializer):
    seller = SellerShopSerializer()
    name = serializers.CharField()
    slug = serializers.SlugField()
    desc = serializers.CharField()
    price_old = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_current = serializers.DecimalField(max_digits=10, decimal_places=2)
    category = CategorySerializer()
    in_stock = serializers.IntegerField()
    image1 = serializers.ImageField()
    image2 = serializers.ImageField(required=False)
    image3 = serializers.ImageField(required=False)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2,
                                              read_only=True)
    reviews_count = serializers.SerializerMethodField()

    def get_reviews_count(self, obj):
        return obj.reviews.filter(is_deleted=False).count()


class CreateProductSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    desc = serializers.CharField()
    price_current = serializers.DecimalField(max_digits=10, decimal_places=2)
    category_slug = serializers.SlugField()
    in_stock = serializers.IntegerField()
    image1 = serializers.ImageField()
    image2 = serializers.ImageField(required=False)
    image3 = serializers.ImageField(required=False)


class OrderItemProductSerializer(serializers.Serializer):
    seller = SellerShopSerializer()
    name = serializers.CharField()
    slug = serializers.SlugField()
    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, source="price_current"
    )


class OrderItemSerializer(serializers.Serializer):
    product = OrderItemProductSerializer()
    quantity = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=10, decimal_places=2, source="get_total")


class ToggleCartItemSerializer(serializers.Serializer):
    slug = serializers.SlugField()
    quantity = serializers.IntegerField(min_value=0)


class CheckoutSerializer(serializers.Serializer):
    shipping_id = serializers.UUIDField()


class OrderSerializer(serializers.Serializer):
    tx_ref = serializers.CharField()
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.EmailField(source="user.email")
    delivery_status = serializers.CharField()
    payment_status = serializers.CharField()
    date_delivered = serializers.DateTimeField()
    shipping_details = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(
        max_digits=100, decimal_places=2, source="get_cart_subtotal"
    )
    total = serializers.DecimalField(
        max_digits=100, decimal_places=2, source="get_cart_total"
    )

    @extend_schema_field(ShippingAddressSerializer)
    def get_shipping_details(self, obj):
        return ShippingAddressSerializer(obj).data


class CheckItemOrderSerializer(serializers.Serializer):
    product = ProductSerializer()
    quantity = serializers.IntegerField()
    total = serializers.FloatField(source="get_total")


class ReviewSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    user_full_name = serializers.CharField(source="user.fullname", read_only=True)
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_deleted=False)
    )
    product_name = serializers.CharField(source="product.name", read_only=True)
    rating = serializers.IntegerField(min_value=1, max_value=5)
    text = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate(self, data):
        request = self.context.get("request")
        user = request.user
        product = data.get("product")

        if not user:
            raise serializers.ValidationError("User is not authenticated")
        if not product:
            raise serializers.ValidationError("Product is required")

        if self.instance:
            if self.instance.user != user:
                raise serializers.ValidationError(
                    "You can't edit someone else's review"
                )

            if product != self.instance.product:
                if Review.objects.filter(
                        user=user,
                        product=product,
                        is_deleted=False
                        ).exists():
                    raise serializers.ValidationError(
                        "You have already left a review about this product"
                    )
        else:
            if Review.objects.filter(
                    user=user,
                    product=product,
                    is_deleted=False
                    ).exists():
                raise serializers.ValidationError(
                    "You have already left a review about this product"
                )

        return data

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["user"] = request.user
        return Review.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.product = validated_data.get('product', instance.product)
        instance.rating = validated_data.get('rating', instance.rating)
        instance.text = validated_data.get('text', instance.text)
        instance.save()
        return instance