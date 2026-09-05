"""
Payment and billing constants.
"""

# How many charges a payment-history read returns. Deep history belongs in the
# billing portal; the agent only ever needs "what have I been charged lately".
PAYMENT_HISTORY_LIMIT = 10

NO_USER_MESSAGE = "Could not identify the user, so their billing state is unavailable."

#: Billing country prefilled on every checkout opened outside production. Dodo's
#: documented test card (4242 4242 4242 4242) is a US Visa and the Indian rail
#: declines it, so a developer whose IP puts the overlay on the Indian rail could
#: not pay with the card the docs say to use. The customer can still change it.
DODO_TEST_MODE_BILLING_COUNTRY = "US"
