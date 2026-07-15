from django.urls import path

from apps.sellers.views import (SellersView,
                                SellerProductsView,
                                SellerOrdersView,
                                SellerOrderItemsView)

urlpatterns = [
    path('', SellersView.as_view()),
    path('products/', SellerProductsView.as_view()),
    path('products/<slug:slug>/', SellerProductsView.as_view()),
    path("orders/", SellerOrdersView.as_view()),
    path("orders/<str:tx_ref>/", SellerOrderItemsView.as_view()),
]