import json
from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from store.models import Order, OrderItem
from paypalrestsdk import notifications
import stripe


@method_decorator(csrf_exempt, name="dispatch")
class ProcessWebhookView(View):
    def post(self, request):
        if "HTTP_PAYPAL_TRANSMISSION_ID" not in request.META:
            return HttpResponseBadRequest()

        auth_algo = request.META["HTTP_PAYPAL_AUTH_ALGO"]
        cert_url = request.META["HTTP_PAYPAL_CERT_URL"]
        transmission_id = request.META["HTTP_PAYPAL_TRANSMISSION_ID"]
        transmission_sig = request.META["HTTP_PAYPAL_TRANSMISSION_SIG"]
        transmission_time = request.META["HTTP_PAYPAL_TRANSMISSION_TIME"]
        webhook_id = settings.PAYPAL_WEBHOOK_ID
        event_body = request.body.decode(request.encoding or "utf-8")

        valid = notifications.WebhookEvent.verify(
            transmission_id=transmission_id,
            timestamp=transmission_time,
            webhook_id=webhook_id,
            event_body=event_body,
            cert_url=cert_url,
            actual_sig=transmission_sig,
            auth_algo=auth_algo,
        )

        if not valid:
            return HttpResponseBadRequest()

        webhook_event = json.loads(event_body)

        event_type = webhook_event["event_type"]

        CHECKOUT_ORDER_APPROVED = "CHECKOUT.ORDER.APPROVED"

        if event_type == CHECKOUT_ORDER_APPROVED:
            order_id = webhook_event["resource"]["purchase_units"][0]["custom_id"]
            order = Order.objects.get(id=order_id)
            order.is_paid = True
            order.payment_method = "P"
            order.save()
        return HttpResponse()


stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeCheckoutView(APIView):
    def post(self, request, id):
        order_item = OrderItem.objects.filter(order_id=id)
        line_items = []
        for item in order_item:
            line_item = {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": item.product.title,
                        "images": ["https://i.imgur.com/EHyR2nP.png"],
                    },
                    "unit_amount": int(item.product.unit_price * 100),
                },
                "quantity": item.quantity,
            }
            line_items.append(line_item)
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=line_items,
                payment_method_types=[
                    "card",
                ],
                metadata={"order_id": id},
                mode="payment",
                success_url=settings.SITE_URL
                + id
                + "/?success=true&session_id={CHECKOUT_SESSION_ID}",
                cancel_url=settings.SITE_URL + id + "/?canceled=true",
            )
            return redirect(checkout_session.url)
        except:
            return redirect(settings.SITE_URL + str(id) + "/?error=true")


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        order_id = session["metadata"]["order_id"]
        order = Order.objects.get(id=order_id)
        order.is_paid = True
        order.payment_method = "C"
        order.save()
    return HttpResponse(status=200)
