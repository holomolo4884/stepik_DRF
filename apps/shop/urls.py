from django.urls import path

from apps.shop.views import (
    CategoriesView,
    ProductView,
    ProductsView,
    ProductsByCategoryView,
    ProductsBySellerView,
    ReviewListView,
    ReviewDetailView
)


urlpatterns = [
    path("categories/", CategoriesView.as_view()),
    path("categories/<slug:slug>/", ProductsByCategoryView.as_view()),
    path("sellers/<slug:slug>/", ProductsBySellerView.as_view()),
    path("products/", ProductsView.as_view()),
    path("products/<slug:slug>/", ProductView.as_view()),
    path('reviews/', ReviewListView.as_view()),
    path('reviews/<int:pk>/', ReviewDetailView.as_view()),
]