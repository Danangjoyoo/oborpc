"""
Security Related Utility
"""
import httpx

BASIC_AUTH_TOKEN = "44a3f281214d481b8408e7b2355968d1"


def validate_rpc_response(response: httpx.Response):
    """
    Validate rpc response with defined security basic token
    """
    if response.status_code != 200:
        return False

    try:
        valid_content_type = (
            response.headers.get("content-type", "").lower()
            == "application/json"
        )
        valid_token = (
            response.headers.get("authorization", "").lower()
            == f"basic {BASIC_AUTH_TOKEN}"
        )
        return valid_content_type and valid_token
    except:
        return False
