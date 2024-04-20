import json
import os

import pandas as pd

from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.exceptions import ObjectDoesNotExist

from . import models
from . import serializers
from .mailservice import SendMail
from .pagination import OnBoardUPagination
from .util import generate_unique_id

mail = SendMail()


# Create your views here.
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class UserRegisterView(generics.CreateAPIView):
    serializer_class = serializers.UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = serializers.UserRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            messages: dict = {}
            for key, value in dict(serializer.errors).items():
                messages[key] = value[0]
            return Response(data={'messages': messages, 'status': {'msg': 'failed', 'code': 220}})
        user = serializer.save()
        token = get_tokens_for_user(user)
        return Response({'token': token, 'message': 'Registration Successful.',
                         'status': {'code': 200, 'msg': 'success'}}, status=status.HTTP_200_OK)


class UserLoginView(generics.CreateAPIView):
    serializer_class = serializers.UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = serializers.UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            messages: dict = {}
            for key, value in dict(serializer.errors).items():
                messages[key] = value[0]
            return Response(data={'messages': messages, 'status': {'msg': 'failed', 'code': 220}})
        email = serializer.data.get('email')
        password = serializer.data.get('password')
        user = authenticate(email=email, password=password)
        if user is not None:
            token = get_tokens_for_user(user)
            return Response(
                {'token': token, 'message': 'Login Successful.', 'status': {'msg': 'success', 'code': 200}},
                status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Email or Password is not Valid',
                             'status': {'msg': 'success', 'code': 230}}, status=status.HTTP_404_NOT_FOUND)


class VerifyOTP(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        of = request.data.get('of')
        otp = request.data.get('otp')

        user = get_object_or_404(models.User, id=request.user.id)
        if otp is None or otp == "":
            return Response(data={'message': 'Enter otp.', 'status': {'code': 220, 'msg': 'failed'}},
                            status=status.HTTP_400_BAD_REQUEST)
        if of is None or of == "":
            return Response(
                data={'message': 'Submit which otp should verify.', 'status': {'code': 220, 'msg': 'failed'}},
                status=status.HTTP_400_BAD_REQUEST)
        if of == "gst":
            # print('user.user_gst.otp ', user.user_gst.otp)
            if user.user_gst.otp != otp:
                return Response(data={'message': 'Enter correct otp.', 'status': {'code': 220, 'msg': 'failed'}},
                                status=status.HTTP_400_BAD_REQUEST)
            user.user_gst.is_otp_used = True
            user.user_gst.gst_verified = True
            user.user_details.is_seller = True
            user.user_details.save()
            user.user_gst.save()
        else:
            if user.user_otp_verification.otp != otp:
                return Response(data={'message': 'Enter correct otp.', 'status': {'code': 220, 'msg': 'failed'}},
                                status=status.HTTP_404_NOT_FOUND)
            user.user_otp_verification.is_otp_used = True
            user.user_details.email_verified = True
            user.user_details.save()
            user.save()
            user.user_otp_verification.save()
        return Response(data={'message': 'Successfully OTP verified.', 'status': {'code': 200, 'msg': 'success'}})


class UserDetailsView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = serializers.UserSerializer(request.user, many=False)
        return Response(data={'data': serializer.data, 'message': 'Successfully retrieved.',
                              'status': {'code': 200, 'msg': 'success'}})


class UploadGSTCertificateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        gst_certificate = request.FILES.get('gst-certificate')
        # print('ggg: ', gst_certificate)
        if gst_certificate is None:
            return Response(
                data={'message': 'Select GST certificate to upload.', 'status': {'code': 230, 'msg': 'failed'}},
                status=status.HTTP_400_BAD_REQUEST)
        seller_id = f'{generate_unique_id(10)}U{request.user.id}'
        try:
            seller = models.SellerGST.objects.get(user_id=request.user.id)
        except ObjectDoesNotExist:
            seller = models.SellerGST.objects.create(user_id=request.user.id, seller_id=seller_id)

        seller.certificate = gst_certificate
        seller.save()
        return Response(
            data={'message': 'Successfully certificate uploaded.', 'status': {'code': 200, 'msg': 'success'}})


class UpdateGSTDetailsView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        trade_name = request.data.get('trade-name')
        gst_no = request.data.get('gst-no')
        gst_type = request.data.get('gst-type')
        legal_name = request.data.get('legal-name')
        business_address = request.data.get('business_address')

        # print(
        #     f"trade_name={trade_name}, gst_no={gst_no}, gst_type={gst_type}, legal_name={legal_name}, business_address={business_address}")

        if trade_name is None or trade_name == "" or gst_no is None or gst_no == "" or gst_type is None or gst_type == "" or legal_name is None or legal_name == "" or business_address is None or business_address == "":
            return Response(data={'message': 'Enter all details.', 'status': {'code': 230, 'msg': 'failed'}})

        seller_gst = get_object_or_404(models.SellerGST, user=request.user)
        seller_gst.trade_name = trade_name
        seller_gst.gst_number = gst_no
        seller_gst.gst_type = gst_type
        seller_gst.legal_name = legal_name
        seller_gst.business_address = business_address
        seller_gst.gst_verified = False
        seller_gst.is_otp_used = False
        # seller_gst.save()
        otp = mail.generate_otp()
        seller_gst.otp = otp
        seller_gst.save()
        # print('seller_gst.gst_otp: ', seller_gst.gst_otp, otp)
        mail.send_otp(request.user, otp, "gst")

        serializer = serializers.SellerGSTDetailsSerializer(seller_gst, many=False)
        return Response(data={'data': serializer.data, 'message': 'Successfully retrieved.',
                              'status': {'code': 200, 'msg': 'success'}})


class SellerDetailsView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        serializer = serializers.SellerGSTDetailsSerializer(request.user.user_gst, many=False)
        return Response(data={'data': serializer.data, 'message': 'Successfully retrieved.',
                              'status': {'code': 200, 'msg': 'success'}})


class GetBusinessView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        user_business = get_object_or_404(models.Business, user=request.user)
        serializer = serializers.BusinessSerializer(user_business, many=False)
        return Response(data={'data': serializer.data, 'message': 'Successfully retrieved.',
                              'status': {'code': 200, 'msg': 'success'}})


class UpdateBusinessView(generics.CreateAPIView):
    serializer_class = serializers.BusinessSerializer
    permission_classes = [permissions.IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        upload_file = request.data.get('action')
        if upload_file is None or upload_file == "":
            return Response(data={'message': 'Submit action in 0 or 1.', 'status': {'code': 230, 'msg': 'failed'}})

        if int(upload_file) == 1:
            pic = request.FILES.get('profile-pic')
            business = models.Business.objects.update_or_create(user_id=request.user.id,
                                                                defaults={'profile_pic': pic})
            return Response(
                data={'message': 'Successfully profile pic uploaded.', 'status': {'code': 200, 'msg': 'success'}})
        else:
            name = request.data.get('business-name')
            address = request.data.get('business-address')
            email = request.data.get('business-email')
            contact_number = request.data.get('business-contact_number')
            shipping_method = request.data.get('business-shipping_method')
            store_name = request.data.get('store_name')

            business = models.Business.objects.update_or_create(user_id=request.user.id,
                                                                defaults={'name': name,
                                                                          'address': address,
                                                                          'email_address': email,
                                                                          'store_name': store_name,
                                                                          'phone_number': contact_number,
                                                                          'shipping_method': shipping_method})
            serializer = serializers.BusinessSerializer(business[0], many=False)
            return Response(data={'data': serializer.data, 'message': 'Successfully business details updated.',
                                  'status': {'code': 200, 'msg': 'success'}})


class BankDetailsView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        if not models.Business.objects.filter(user_id=request.user.id).exists():
            return Response(
                data={'message': 'First create your business profile.', 'status': {'code': 230, 'msg': 'failed'}},
                status=status.HTTP_400_BAD_REQUEST)

        acc_holder_name = request.data.get('acc-holder-name')
        acc_number = request.data.get('acc-number')
        ifsc = request.data.get('ifsc')

        if acc_holder_name is None or acc_number is None or ifsc is None or acc_holder_name == "" or acc_number == "" or ifsc == "":
            return Response(data={'message': 'Submit all bank details.', 'status': {'code': 230, 'msg': 'failed'}},
                            status=status.HTTP_400_BAD_REQUEST)

        user_business = get_object_or_404(models.Business, user=request.user)
        bank_details = models.BanksDetails.objects.create(business_id=user_business.id, acc_holder_name=acc_holder_name,
                                                          acc_number=acc_number, ifsc=ifsc)
        serializer = serializers.BankDetailsSerializer(bank_details, many=False)
        return Response(data={'data': serializer.data, 'message': 'Bank account details successfully added.',
                              'status': {'code': 200, 'msg': 'success'}})


class HomeView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        return Response(data={'message': 'You are authenticated', 'username': request.user.username},
                        status=status.HTTP_200_OK)


# Catalogue
class RetrieveCatalogueView(generics.RetrieveAPIView):
    """Retrieve all catalogue's"""
    serializer_class = serializers.CatalogueSerializer
    permission_classes = [permissions.IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        queryset = models.Catalogue.objects.all()
        serializer = serializers.CatalogueSerializer(queryset, many=True)
        return Response(data={'data': serializer.data, 'message': 'Successfully Retrieved.',
                              "status": {'code': 200, 'msg': 'success'}}, status=status.HTTP_200_OK)


class RetrieveCategoriesView(generics.RetrieveAPIView):
    serializer_class = serializers.ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        queryset = models.ProductCategory.objects.all()
        serializer = serializers.ProductCategorySerializer(queryset, many=True)
        return Response(data={'data': serializer.data, 'message': 'Successfully retrieved.',
                              'status': {'code': 200, 'msg': 'success'}}, status=status.HTTP_200_OK)


class CreateCategoryView(generics.CreateAPIView):
    serializer_class = serializers.ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        name = request.data.get('name')
        if name is None or name == "":
            return Response(
                data={'message': 'Please submit name to create category.', 'status': {'code': 220, 'msg': 'failed'}},
                status=status.HTTP_400_BAD_REQUEST)

        if models.ProductCategory.objects.filter(name=name).exists():
            return Response(
                data={'message': 'This category is already available!', 'status': {'code': 220, 'msg': 'failed'}},
                status=status.HTTP_400_BAD_REQUEST)

        category = models.ProductCategory.objects.create(name=name, created_by_id=request.user.id)
        serializer = serializers.ProductCategorySerializer(category, many=False)
        return Response(data={'data': serializer.data, 'message': 'Successfully retrieved.',
                              'status': {'code': 200, 'msg': 'success'}}, status=status.HTTP_200_OK)


# class CatalogueCreateView(generics.CreateAPIView):
#     queryset = models.Catalogue.objects.all()
#     serializer_class = serializers.CatalogueSerializer


# class CatalogueDetailView(generics.RetrieveAPIView):
#     """ Retrieve catalogue by its id """
#     lookup_url_kwarg = 'id'
#     queryset = models.Catalogue.objects.all()
#     serializer_class = serializers.CatalogueSerializer
#     permission_classes = [permissions.IsAuthenticated, ]


# ======= Products Views

class ProductUpdateView(generics.UpdateAPIView):
    serializer_class = serializers.ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        product_id = request.data.get('p-id')

        try:
            product = models.ProductDetails.objects.get(id=product_id)
        except ObjectDoesNotExist:
            return Response(data={'message': 'Product does not exit. Try creating this product',
                                  'status': {'msg': 'failed', 'code': 220}}, status=status.HTTP_404_NOT_FOUND)

        stock = request.data.get("stock")
        discount = request.data.get("discount")
        final_price = request.data.get("final-price")

        if stock is not None and stock != "":
            product.stock = stock
        if discount is not None and discount != "":
            product.discount = int(discount)
        if final_price is not None and final_price != "":
            product.final_price = final_price

        product.save()

        serializer = serializers.ProductDetailSerializer(product, many=False)
        return Response(data={'data': serializer.data, 'message': 'Product successfully updated.',
                              'status': {'code': 200, 'msg': 'success'}}, status=status.HTTP_200_OK)


class ProductsListsView(generics.RetrieveAPIView):
    # ListCreateAPIview will only help with post method and with get method
    serializer_class = serializers.ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        paginator = OnBoardUPagination()

        page_size = request.GET.get('page-size')
        if page_size is not None and page_size != "":
            paginator.page_size = int(page_size)

        queryset = models.ProductDetails.objects.filter(user_id=request.user.id).order_by('id').reverse()
        result_queryset = paginator.paginate_queryset(queryset, request)

        serializer = serializers.ProductDetailSerializer(result_queryset, many=True)
        s = {'code': 200, 'msg': 'success'}
        return paginator.get_paginated_response(data=serializer.data, msg="Successfully retrieved.", status=s)


class PublishProductView(generics.UpdateAPIView):
    serializer_class = serializers.ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        product_id = request.data.get('p-id')
        publish = request.data.get('publish')
        if product_id is None or product_id == "":
            return Response(data={'message': 'Please submit product id!', 'status': {'code': 230, 'msg': 'failed'}},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            product = models.ProductDetails.objects.get(id=product_id)
        except ObjectDoesNotExist:
            return Response(
                data={'message': 'Please submit correct product id!', 'status': {'code': 230, 'msg': 'failed'}},
                status=status.HTTP_400_BAD_REQUEST)
        product.publish = bool(int(publish))
        product.save()
        serializer = serializers.ProductDetailSerializer(product, many=False)
        return Response(data={'products': serializer.data, 'message': 'Successfully retrieved.',
                              'status': {'code': 200, 'msg': 'success'}})


class CreateProductView(generics.CreateAPIView):
    serializer_class = serializers.ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        products_list = request.data.get('products')

        for product in products_list:
            name = product['name']
            image = product['image']
            description = product['description']
            features = product['features']
            price = product['price']
            discount = product['discount']
            final_price = product['final_price']
            stock = product['stock']
            catalogue_name = product['catalogue']
            category_name = product['category']

            try:
                category = models.ProductCategory.objects.get(name=category_name)
            except ObjectDoesNotExist:
                category = models.ProductCategory.objects.create(name=category_name, created_by_id=request.user.id)

            if catalogue_name is None or catalogue_name == "":
                catalogue_name = name.split()[0]
            try:
                catalogue = models.Catalogue.objects.get(name=catalogue_name)
            except ObjectDoesNotExist:
                catalogue = models.Catalogue.objects.create(created_by_id=request.user.id, name=catalogue_name,
                                                            category_id=category.id)

            try:
                product = models.Product.objects.get(name=name, catalogue_id=catalogue.id, category_id=category.id)
            except ObjectDoesNotExist:
                product = models.Product.objects.create(name=name, image=image, description=description,
                                                        features=features, price=price, catalogue_id=catalogue.id,
                                                        category_id=category.id)

            try:
                product_detail = models.ProductDetails.objects.get(user_id=request.user.id, product_id=product.id)
            except ObjectDoesNotExist:
                product_detail = models.ProductDetails.objects.create(user_id=request.user.id, product_id=product.id,
                                                                      discount=discount, final_price=final_price,
                                                                      stock=stock)
        return Response(data={'message': 'Products created successfully.',
                              'status': {'code': 200, 'msg': 'success'}}, status=status.HTTP_200_OK)


class ExtractDataFromExcel(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        excel_file = request.FILES.get('excel-file')
        if excel_file is None or excel_file == "":
            return Response(data={'message': 'Please submit excel file!', 'status': {'code': 230, 'msg': 'failed'}},
                            status=status.HTTP_404_NOT_FOUND)

        file_path = excel_file.name  # Replace with the actual file path
        file_extension = os.path.splitext(file_path)[1]

        if file_extension == '.xlsx':
            print('File is in XLSX format')
            data_df = pd.read_excel(excel_file)
        elif file_extension == '.csv':
            print('File is in CSV format')
            data_df = pd.read_csv(excel_file)
        else:
            print('File format is not recognized')
            return Response(
                data={'message': 'Only submit .xlsx and .csv file!', 'status': {'code': 230, 'msg': 'failed'}},
                status=status.HTTP_406_NOT_ACCEPTABLE)

        json_data = data_df.to_json(orient='records')
        json_object = json.loads(json_data)
        return Response(data={'data': json_object, 'message': 'Successfully catalogue extracted.',
                              'status': {'code': 200, 'msg': 'success'}},
                        status=status.HTTP_200_OK)


class UploadProductImages(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        product_image = request.FILES.get('product-image')
        if product_image is None:
            return Response(
                data={'message': 'Select product image to upload.', 'status': {'code': 230, 'msg': 'failed'}},
                status=status.HTTP_400_BAD_REQUEST)

        p_image = models.ProductImages.objects.create(user_id=request.user.id)
        p_image.image = product_image
        p_image.save()

        image_url = request.build_absolute_uri("/media/") + str(p_image.image)

        return Response(
            data={'image': image_url, 'message': 'Successfully image uploaded.',
                  'status': {'code': 200, 'msg': 'success'}})


class UploadCatalogueImages(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        catalogue_image = request.FILES.get('catalogue-image')
        print(catalogue_image)
        if catalogue_image is None:
            return Response(
                data={'message': 'Select catalogue image to upload.', 'status': {'code': 230, 'msg': 'failed'}},
                status=status.HTTP_400_BAD_REQUEST)

        c_image = models.CatalogueImages.objects.create(user_id=request.user.id)
        c_image.file = catalogue_image
        c_image.save()

        image_url = request.build_absolute_uri("/media/") + str(c_image.file)

        return Response(
            data={'image': image_url, 'message': 'Successfully image uploaded.',
                  'status': {'code': 200, 'msg': 'success'}})

