import requests
import json
from time import gmtime, strftime

# --- Configuration ---
# **IMPORTANT:** Replace "YOUR_DEVELOPER_TOKEN" with your actual Microsoft Advertising Developer Token.
# **UPDATED DEVELOPER TOKEN from user's image:**
DEVELOPER_TOKEN = "120BLHQLR411819"

# **Choose your environment: "sandbox" or "production"**
ENVIRONMENT = "sandbox"  # Set to "sandbox" for testing, "production" for live
API_ENVIRONMENT_BASE_URL = "https://clientcenter.api" # Base URL, environment will be added

if ENVIRONMENT == "sandbox":
    API_ENDPOINT_BASE = f"{API_ENVIRONMENT_BASE_URL}.sandbox.bingads.microsoft.com/CustomerManagement/v13" # Removed /Customer from base URL
    print("Using SANDBOX environment.")
elif ENVIRONMENT == "production":
    API_ENDPOINT_BASE = f"{API_ENVIRONMENT_BASE_URL}.bingads.microsoft.com/CustomerManagement/v13" # Removed /Customer from base URL
    print("Using PRODUCTION environment.")
else:
    print("Invalid ENVIRONMENT setting. Please choose 'sandbox' or 'production'. Exiting.")
    exit()

SIGNUP_CUSTOMER_ENDPOINT = f"{API_ENDPOINT_BASE}/Customer/Signup" # Added /Customer back to Signup URL
# **Corrected GetUser Endpoint URL (removed extra /Customer segment and using GET method):**
GET_USER_ENDPOINT = f"{API_ENDPOINT_BASE}/GetUser"


# --- Request Headers ---
headers = {
    "AuthenticationToken": DEVELOPER_TOKEN,
    "Content-Type": "application/json",
}


def output_status_message(message):
    print(message)

def output_user(user_data):
    print(json.dumps(user_data, indent=4)) # Simple output for user data

def output_array_of_customerrole(customer_roles):
    print(json.dumps(customer_roles, indent=4)) # Simple output for customer roles


def main():
    try:
        output_status_message("-----\nGetUser:")
        # **Using GET method for GetUser (RESTful convention)**
        get_user_response = requests.get(GET_USER_ENDPOINT, headers=headers) # Changed to GET request, removed json={} body
        get_user_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        get_user_response_json = get_user_response.json()

        user = get_user_response_json.get("User") # Assuming "User" key in response based on C# example
        customer_roles_response = get_user_response_json.get("CustomerRoles", {}) # Handle missing CustomerRoles
        customer_roles = customer_roles_response.get("CustomerRole", []) # Handle missing CustomerRole array

        output_status_message("User:")
        output_user(user)
        output_status_message("CustomerRoles:")
        output_array_of_customerrole(customer_roles_response) # Output the whole CustomerRoles structure


        # Only a user with the aggregator role (33) can sign up new customers.
        # If the user does not have the aggregator role, then do not continue.

        role_ids = []
        if customer_roles: # Check if customer_roles is not None and not empty
            for customer_role in customer_roles:
                role_ids.append(customer_role.get('RoleId')) # Use .get to avoid KeyError

        if 33 not in role_ids:
            output_status_message("Only a user with the aggregator role (33) can sign up new customers.")
            return  # Exit the main function


        customer_data = {
            "Industry": "Other", #  Industry.Other in C#
            "MarketCountry": "US", # MarketCountry = "US" in C#
            "MarketLanguage": "English", # MarketLanguage = LanguageType.English in C#
            "Name": "Child Customer " + strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()), # Name = "Child Customer " + DateTime.UtcNow in C#
        }

        account_data = {
            "BusinessAddress": {
                "BusinessName": "Contoso", # BusinessName = "Contoso" in C#
                "City": "Redmond", # City = "Redmond"
                "Line1": "One Microsoft Way", # Line1 = "One Microsoft Way"
                "CountryCode": "US", # CountryCode = "US"
                "PostalCode": "98052", # PostalCode = "98052"
                "StateOrProvince": "WA", # StateOrProvince = "WA"
            },
            "CurrencyCode": "USD", # CurrencyCode = CurrencyCode.USD in C#
            "Name": "Child Account " + strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()), # Name = "Child Account " + DateTime.UtcNow in C#
            "ParentCustomerId": user.get('CustomerId'), # ParentCustomerId = (long)user.CustomerId in C#
            "TaxInformation": None, # TaxInformation = null in C#
            "TimeZone": "PacificTimeUSCanadaTijuana", # TimeZone = TimeZoneType.PacificTimeUSCanadaTijuana in C#
        }


        output_status_message("-----\nSignupCustomer:")
        signup_customer_request_data = {
            "Customer": customer_data,
            "Account": account_data,
            "ParentCustomerId": user.get('CustomerId') # Match ParentCustomerId from Account
        }


        signup_customer_response = requests.post(
            SIGNUP_CUSTOMER_ENDPOINT,
            headers=headers,
            json=signup_customer_request_data
        )
        signup_customer_response.raise_for_status() # Raise HTTPError for bad responses
        signup_customer_response_json = signup_customer_response.json()


        output_status_message("New Customer and Account:")

        output_status_message(f"\tCustomerId: {signup_customer_response_json.get('CustomerId')}")
        output_status_message(f"\tCustomerNumber: {signup_customer_response_json.get('CustomerNumber')}")
        output_status_message(f"\tAccountId: {signup_customer_response_json.get('AccountId')}")
        output_status_message(f"\tAccountNumber: {signup_customer_response_json.get('AccountNumber')}")


    except requests.exceptions.HTTPError as ex:
        output_status_message(f"HTTP Error: {ex}")
        if ex.response is not None: # Check if response object exists before accessing .text
            output_status_message(f"Response Body (Error): {ex.response.text}")
    except Exception as ex:
        output_status_message(f"Exception: {ex}")


if __name__ == '__main__':
    main()
    print("\nScript execution finished.")