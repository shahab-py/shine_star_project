import logging
import requests
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views import View
from django.http import HttpResponseRedirect
from .models import Order, OrderItem
from shop.models import Product
from shop.cart import Cart
from django.conf import settings
from django.utils import timezone
from .access import get_accessible_order


logger = logging.getLogger(__name__)

def order_create(request):
    cart = Cart(request)
    if not cart.is_empty():
        user = request.user if request.user.is_authenticated else None

        order = Order.objects.create(
            user=user,
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', ''),
            email=request.POST.get('email', ''),
            address=request.POST.get('address', ''),
            city=request.POST.get('city', ''),
            postcode=request.POST.get('postcode', ''),
            phone_number=request.POST.get('phone_number', ''),
            province=request.POST.get('province', ''),
            status='pending',
            paid=False,
            total_price=cart.get_total_price()
        )

        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                price_at_purchase=item['price'],
                quantity=item['quantity']
            )

        cart.clear()

        return redirect('orders:payment_start', order_id=order.id)
    
    messages.error(request, "سبد خرید شما خالی است.")
    return redirect('shop:product_list')

def payment_start(request, order_id):
    if (
        not settings.ZARINPAL["MERCHANT_ID"]
        or not settings.ZARINPAL["START_URL"]
    ):
        logger.error("ZarinPal settings are incomplete.")
        messages.error(request, "درگاه پرداخت در حال حاضر در دسترس نیست.")
        return redirect("shop:product_list")

    reservation_time = timezone.now()
    existing_authority = None
    request_in_progress = False

    # مرحله اول: رزرو سفارش در یک تراکنش کوتاه
    with transaction.atomic():
        accessible_order = get_accessible_order(request, order_id)

        order = get_object_or_404(
            Order.objects.select_for_update(),
            id=accessible_order.pk,
        )
        if order.paid or order.status == "paid":
            messages.info(request, "این سفارش قبلاً پرداخت شده است.")
            return redirect(
                "orders:order_success",
                order_id=order.id,
            )

        if (
            order.status != "pending"
            or order.expires_at <= timezone.now()
        ):
            if order.status == "pending":
                order.status = "expired"
                order.save(update_fields=["status"])

            messages.error(
                request,
                "مهلت پرداخت این سفارش به پایان رسیده است.",
            )
            return redirect("shop:product_list")

        if order.payment_authority:
            existing_authority = order.payment_authority

        elif order.payment_request_started_at:
            request_in_progress = True

        else:
            order.payment_request_started_at = reservation_time
            order.save(update_fields=["payment_request_started_at"])

        order_data = {
            "id": order.id,
            "amount": int(order.total_price),
            "phone_number": order.phone_number,
            "email": order.email,
        }

    # اگر Authority قبلی وجود دارد، درخواست جدید نساز
    if existing_authority:
        return redirect(
            f"https://sandbox.zarinpal.com/pg/StartPay/{existing_authority}"
        )

    # اگر درخواست دیگری در جریان است، منتظر بمان
    if request_in_progress:
        messages.info(
            request,
            "درخواست پرداخت این سفارش در حال بررسی است.",
        )
        return redirect("shop:product_list")

    callback_url = request.build_absolute_uri(
        reverse(
            "orders:payment_verify",
            kwargs={"order_id": order_data["id"]},
        )
    )

    payload = {
        "merchant_id": settings.ZARINPAL["MERCHANT_ID"],
        "amount": order_data["amount"],
        "currency": "IRT",
        "callback_url": callback_url,
        "description": f"Payment for order #{order_data['id']}",
        "metadata": {
            "mobile": order_data["phone_number"],
            "email": order_data["email"],
        },
    }

    # مرحله دوم: ارتباط با درگاه، خارج از تراکنش دیتابیس
    try:
        response = requests.post(
            settings.ZARINPAL["START_URL"],
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        result = response.json()

    except (requests.RequestException, ValueError):
        logger.exception(
            "ZarinPal payment request failed for order %s",
            order_data["id"],
        )
        messages.error(
            request,
            "وضعیت درخواست پرداخت مشخص نیست. لطفاً دوباره درخواست ندهید.",
        )
        return redirect("shop:product_list")

    # بررسی ساختار پاسخ دریافتی از درگاه
    if not isinstance(result, dict):
        logger.error(
            "Unexpected ZarinPal response type for order %s: %s",
            order_data["id"],
            type(result).__name__,
        )
        messages.error(
            request,
            "پاسخ درگاه قابل تشخیص نیست. لطفاً دوباره درخواست پرداخت ندهید.",
        )
        return redirect("shop:product_list")

    data = result.get("data")

    if not isinstance(data, dict):
        logger.error(
            "Invalid ZarinPal response structure for order %s",
            order_data["id"],
        )
        messages.error(
            request,
            "پاسخ درگاه قابل تشخیص نیست. لطفاً دوباره درخواست پرداخت ندهید.",
        )
        return redirect("shop:product_list")

    code = data.get("code")
    authority = data.get("authority")

    if isinstance(authority, str):
        authority = authority.strip()
    else:
        authority = None

    if code == 100 and not authority:
        logger.error(
            "ZarinPal returned success code without authority "
            "for order %s",
            order_data["id"],
        )
        messages.error(
            request,
            "پاسخ درگاه ناقص است. لطفاً دوباره درخواست پرداخت ندهید.",
        )
        return redirect("shop:product_list")

    if code != 100:
        errors = result.get("errors")

        explicit_rejection = (
            isinstance(errors, dict)
            and errors.get("code") is not None
            and isinstance(errors.get("message"), str)
            and bool(errors["message"].strip())
        )

        if not explicit_rejection:
            logger.error(
                "Ambiguous ZarinPal response for order %s: %s",
                order_data["id"],
                result,
            )
            messages.error(
                request,
                "وضعیت درخواست پرداخت مشخص نیست. "
                "لطفاً دوباره درخواست ندهید.",
            )
            return redirect("shop:product_list")

        logger.warning(
            "ZarinPal explicitly rejected payment request "
            "for order %s: %s",
            order_data["id"],
            errors,
        )

        with transaction.atomic():
            locked_order = get_object_or_404(
                Order.objects.select_for_update(),
                id=order_data["id"],
            )

            if (
                locked_order.payment_request_started_at
                == reservation_time
            ):
                locked_order.payment_request_started_at = None
                locked_order.save(
                    update_fields=["payment_request_started_at"]
                )

        messages.error(
            request,
            "درخواست پرداخت از طرف درگاه پذیرفته نشد.",
        )
        return redirect("shop:product_list")

    # مرحله سوم: ذخیره Authority در یک تراکنش کوتاه
    with transaction.atomic():
        locked_order = get_object_or_404(
            Order.objects.select_for_update(),
            id=order_data["id"],
        )

        if (
            locked_order.payment_request_started_at != reservation_time
            or locked_order.status != "pending"
            or locked_order.expires_at <= timezone.now()
        ):
            logger.error(
                "Payment state changed while requesting authority "
                "for order %s",
                locked_order.id,
            )
            messages.error(
                request,
                "وضعیت سفارش تغییر کرده است؛ پرداخت را ادامه ندهید.",
            )
            return redirect("shop:product_list")

        locked_order.payment_authority = authority
        locked_order.payment_request_started_at = None

        locked_order.save(
            update_fields=[
                "payment_authority",
                "payment_request_started_at",
            ]
        )

    return redirect(
        f"https://sandbox.zarinpal.com/pg/StartPay/{authority}"
    )


def payment_verify(request, order_id):
    authority = request.GET.get("Authority", "").strip()
    status = request.GET.get("Status", "").strip()

    if not authority or status != "OK":
        messages.error(request, "پرداخت توسط درگاه تأیید نشد.")
        return redirect("shop:product_list")

    if (
        not settings.ZARINPAL.get("MERCHANT_ID")
        or not settings.ZARINPAL.get("VERIFY_URL")
    ):
        logger.error("ZarinPal verification settings are incomplete.")
        messages.error(request, "تنظیمات تأیید پرداخت کامل نیست.")
        return redirect("shop:product_list")

    order = get_object_or_404(Order, id=order_id)

    if order.payment_authority != authority:
        logger.warning(
            "Payment authority mismatch for order %s",
            order.id,
        )
        messages.error(request, "شناسه پرداخت با سفارش مطابقت ندارد.")
        return redirect("shop:product_list")

    if order.paid:
        return redirect("orders:order_success", order_id=order.id)

    if order.status not in ("pending", "expired"):
        messages.error(request, "وضعیت سفارش برای تأیید پرداخت معتبر نیست.")
        return redirect("shop:product_list")

    payload = {
        "merchant_id": settings.ZARINPAL["MERCHANT_ID"],
        "amount": int(order.total_price),
        "authority": authority,
        "currency": "IRT",
    }

    try:
        response = requests.post(
            settings.ZARINPAL["VERIFY_URL"],
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        result = response.json()

    except (requests.RequestException, ValueError):
        logger.exception(
            "ZarinPal verification request failed for order %s",
            order.id,
        )
        messages.error(
            request,
            "ارتباط با درگاه برای تأیید پرداخت ناموفق بود.",
        )
        return redirect("shop:product_list")

    if not isinstance(result, dict):
        messages.error(request, "پاسخ تأیید درگاه معتبر نیست.")
        return redirect("shop:product_list")

    data = result.get("data")

    if not isinstance(data, dict) or data.get("code") not in (100, 101):
        logger.warning(
            "ZarinPal verification rejected for order %s: %s",
            order.id,
            result.get("errors") or result.get("data") or {},
        )
        messages.error(request, "پرداخت توسط درگاه تأیید نشد.")
        return redirect("shop:product_list")

    ref_id = data.get("ref_id")

    if ref_id is None or not str(ref_id).strip():
        logger.error(
            "ZarinPal verification response has no ref_id for order %s",
            order.id,
        )
        messages.error(request, "شناسه پیگیری پرداخت دریافت نشد.")
        return redirect("shop:product_list")

    try:
        with transaction.atomic():
            locked_order = Order.objects.select_for_update().get(
                id=order_id
            )

            if locked_order.payment_authority != authority:
                raise ValueError("Payment authority mismatch.")

            if locked_order.paid:
                return redirect(
                    "orders:order_success",
                    order_id=locked_order.id,
                )

            if locked_order.status not in ("pending", "expired"):
                raise ValueError("Order status is not eligible for payment.")

            items = list(
                locked_order.items.all().order_by("product_id")
            )
            if not items:
                raise ValueError("Cannot finalize payment for an empty order.")

            product_ids = sorted({
                item.product_id for item in items
            })

            locked_products = {
                product.id: product
                for product in Product.objects.select_for_update()
                .filter(id__in=product_ids)
                .order_by("id")
            }

            insufficient_stock = []

            for item in items:
                product = locked_products.get(item.product_id)

                if product is None:
                    insufficient_stock.append(
                        f"محصول حذف‌شده با شناسه {item.product_id}"
                    )
                    continue

                if product.stock < item.quantity:
                    insufficient_stock.append(product.name)

            locked_order.paid = True
            locked_order.payment_ref_id = str(ref_id).strip()

            if insufficient_stock:
                locked_order.status = "payment_review"

                logger.warning(
                    "Payment confirmed but order %s requires review. "
                    "Insufficient stock: %s",
                    locked_order.id,
                    ", ".join(insufficient_stock),
                )

            else:
                for item in items:
                    product = locked_products[item.product_id]
                    product.decrease_stock(item.quantity)

                locked_order.status = "paid"

            locked_order.save(
                update_fields=[
                    "paid",
                    "status",
                    "payment_ref_id",
                ]
            )

    except (ValidationError, ValueError) as exc:
        logger.exception(
            "Could not finalize payment for order %s: %s",
            order_id,
            str(exc),
        )
        messages.error(
            request,
            "ثبت نهایی پرداخت انجام نشد؛ سفارش نیازمند بررسی است.",
        )
        return redirect("shop:product_list")

    if insufficient_stock:
        messages.warning(
            request,
            "پرداخت تأیید شد، اما سفارش به دلیل کمبود موجودی نیازمند بررسی است.",
        )
    else:
        messages.success(request, "پرداخت با موفقیت تأیید شد.")

    return redirect(
        "orders:order_success",
        order_id=order_id,
    )



def order_success(request, order_id):
    order = get_accessible_order(request, order_id)
    return render(request, 'orders/order_success.html', {'order': order})
