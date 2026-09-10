"""
Payment and billing constants.
"""

# How many charges a payment-history read returns. Deep history belongs in the
# billing portal; the agent only ever needs "what have I been charged lately".
PAYMENT_HISTORY_LIMIT = 10

# How many of a user's recent checkout sessions payment verification asks Dodo
# about before giving up. It scans instead of reading only the newest because
# every paywall block mints a fresh session, so the one that was actually paid
# is routinely buried under later ones; the cap bounds the Dodo round trips a
# single verify can make (the scan stops at the first session Dodo calls paid,
# so a user who just paid normally costs one).
CHECKOUT_SESSION_SCAN_LIMIT = 10

NO_USER_MESSAGE = "Could not identify the user, so their billing state is unavailable."

#: Everything a checkout opened outside production prefills, so a developer
#: only types the test card. The country matters: Dodo's documented test card
#: (4242 4242 4242 4242) is a US Visa and the Indian rail declines it, so an
#: overlay placed on the Indian rail by the developer's IP could not pay with
#: the card the docs name. The address is a real US one so validation passes;
#: the customer can still edit every field.
DODO_TEST_MODE_BILLING_ADDRESS: dict[str, str] = {
    "country": "US",
    "street": "548 Market St",
    "city": "San Francisco",
    "state": "CA",
    "zipcode": "94104",
}
DODO_TEST_MODE_PHONE_NUMBER = "+14155550123"
