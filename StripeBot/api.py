# api.py
from config import STRIPE_API_KEY
import stripe


async def get_subscribers_emails():
    stripe.api_key = STRIPE_API_KEY
    subscriptions = stripe.Subscription.list()

    customer_emails = {}
    for subscription in subscriptions.auto_paging_iter():
        customer_id = subscription.customer
        try:
            customer = stripe.Customer.retrieve(customer_id)
            customer_emails[customer.id] = customer.email
        except stripe.error.StripeError as e:
            print(f"Error retrieving customer {customer_id}: {e}")
            pass

    subscribers_emails = []
    for subscription in subscriptions.auto_paging_iter():
        customer_id = subscription.customer
        email = customer_emails.get(customer_id)
        subscribers_emails.append(email)

    print(subscribers_emails)
    return subscribers_emails
