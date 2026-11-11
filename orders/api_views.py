
from django.core.exceptions import ValidationError

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer
from .services import create_order_from_cart


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).order_by('-created')


class OrderCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order = create_order_from_cart(
                request=request,
                customer_data=serializer.validated_data,
            )

        except ValidationError as exc:
            return Response(
                {"error": exc.messages},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "message": "Order created",
                "order_id": order.id,
                "total_price": str(order.total_price),
            },
            status=status.HTTP_201_CREATED
        )
