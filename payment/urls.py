from django.urls import path
from . import views

urlpatterns = [
    path("webhooks/paypal/", views.ProcessWebhookView.as_view()),
    path("webhooks/stripe/", views.stripe_webhook),
    path("create-checkout-session/<int:id>", views.StripeCheckoutView.as_view()),
]
