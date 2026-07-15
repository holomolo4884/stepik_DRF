from django.urls import path

from apps.profiles.views import ProfileView, ShippingAddressView, OrdersView, OrderItemsView

urlpatterns = [
    path('', ProfileView.as_view()),
    path('shipping_addresses/', ShippingAddressView.as_view()),
    path("orders/", OrdersView.as_view()),
    path("orders/<str:tx_ref>/", OrderItemsView.as_view()),
]