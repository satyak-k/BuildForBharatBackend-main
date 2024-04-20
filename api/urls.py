from rest_framework_simplejwt import views as jwt_views
from django.urls import path
from . import views

urlpatterns = [
    # """ Swagger API documentation """

    # """ Authentication """,
    path('register', views.UserRegisterView.as_view()),
    path('login', views.UserLoginView.as_view()),
    path('token/refresh', jwt_views.TokenRefreshView.as_view()),
    path('verify/otp', views.VerifyOTP.as_view()),
    path('logout', jwt_views.TokenBlacklistView.as_view()),

    # """ Seller Registration """,
    path('upload/gst-certificate', views.UploadGSTCertificateView.as_view()),
    path('update/gst-details', views.UpdateGSTDetailsView.as_view()),
    path('update/business-profile', views.UpdateBusinessView.as_view()),

    # """ Payment Details """
    path('create/bank-details', views.BankDetailsView.as_view()),

    # """ Retrieve Data """
    path('user-details', views.UserDetailsView.as_view()),
    path('business-details', views.GetBusinessView.as_view()),
    path('seller-details', views.SellerDetailsView.as_view()),

    # """"Creating ,Fetching and updating api's product""""
    path('create/product', views.CreateProductView.as_view()),
    path('get/products-lists', views.ProductsListsView.as_view()),
    path('pub-unpub/product', views.PublishProductView.as_view()),
    path('update/product', views.ProductUpdateView.as_view()),
    path('upload/product-image', views.UploadProductImages.as_view()),

    # """" Extract Data from Excel """"
    path('extract/excel', views.ExtractDataFromExcel.as_view()),

    # Catalogue/Categories list
    path('get/catalogue-lists', views.RetrieveCatalogueView.as_view()),
    path('get/categories-lists', views.RetrieveCategoriesView.as_view()),
    path('create/category', views.CreateCategoryView.as_view()),
    path('upload/catalogue-image', views.UploadCatalogueImages.as_view()),
    # path('catalogue/create/', views.CatalogueCreateView.as_view(), name='catalogue-create'),
    # path('catalogue/getDetails/', views.RetrieveCatalogueView.as_view(), name='catalogue-detail'),
    # path('catalogue/uploadExistingCatalogue/', views.CatalogueUploadView.as_view(), name='catalogue-upload'),
]
